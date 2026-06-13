import os
import csv
import json
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

# Import the existing MVA solver
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'model')))
from mva_solver import OpenNetworkMVASolver, ServiceCentre

app = FastAPI(title="Analytical Queueing Network API", version="1.0.0")

# ── Mount static files and serve dashboard at root ──────────────────────────
_STATIC_DIR = Path(__file__).parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    """Serve the SPE Observatory Hub dashboard."""
    html_file = _STATIC_DIR / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)

# Path to data files (adjust if repository root differs)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MEASUREMENT_CSV = os.path.join(PROJECT_ROOT, 'data', 'processed', 'empirical_measurements.csv')
MODEL_JSON = os.path.join(PROJECT_ROOT, 'scripts', 'model', 'queueing_network_parameters.json')

class SolveRequest(BaseModel):
    arrival_rate: float  # external arrival rate (requests per second)
    replicas: Dict[str, int] | None = None  # optional per‑service replica count, e.g. {"Frontend": 2}

    @field_validator('arrival_rate')
    @classmethod
    def arrival_rate_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('arrival_rate must be positive')
        return v
        
    @field_validator('replicas')
    @classmethod
    def replicas_must_be_positive(cls, v: Dict[str, int] | None) -> Dict[str, int] | None:
        if v is not None:
            for count in v.values():
                if count <= 0:
                    raise ValueError('replica counts must be positive')
        return v

def _load_parameters() -> Dict[str, Any]:
    """Load default model parameters required by the solver.
    The original `queueing_network.py` script writes a JSON file with service
    names, service times, routing matrix, and other static data.  This helper
    reads that file so the API can reuse the same configuration.
    """
    if not os.path.exists(MODEL_JSON):
        raise FileNotFoundError(f"Model parameters JSON not found at {MODEL_JSON}")
    with open(MODEL_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def _load_measurements() -> List[Dict[str, Any]]:
    """Read the empirical measurements CSV and return a list of dictionaries.
    Expected columns: service_name, mean_response_time_ms, ...
    """
    if not os.path.exists(MEASUREMENT_CSV):
        raise FileNotFoundError(f"Measurements CSV not found at {MEASUREMENT_CSV}")
    with open(MEASUREMENT_CSV, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

@app.post("/solve")
def solve(request: SolveRequest) -> Dict[str, Any]:
    """Solve the open queueing network for a given external arrival rate.
    The endpoint returns per‑service predicted mean response times (ms), utilizations
    and visit ratios.
    """
    try:
        params = _load_parameters()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    centres = []
    num_servers_list = params.get("num_servers")
    if not num_servers_list or not isinstance(num_servers_list, list):
        num_servers_list = [1] * len(params["service_names"])

    if request.replicas:
        invalid_keys = set(request.replicas.keys()) - set(params["service_names"])
        if invalid_keys:
            raise HTTPException(status_code=400, detail=f"Invalid service names in replicas: {invalid_keys}")

    for idx, name in enumerate(params["service_names"]):
        st = params["service_times"][idx]
        num_servers = num_servers_list[idx]
        # Apply horizontal replica overrides if any (mathematically accurate M/M/c)
        if request.replicas and name in request.replicas:
            num_servers = int(request.replicas[name])
        centres.append(ServiceCentre(name=name, service_time=st, num_servers=num_servers))

    # Convert routing matrix to numpy array
    routing_matrix = np.array(params["routing_matrix"])

    # Build external arrivals vector (only Frontend receives external requests)
    external_arrivals = np.zeros(len(params["service_names"]))
    try:
        frontend_idx = params["service_names"].index("Frontend")
    except ValueError:
        frontend_idx = 0
    external_arrivals[frontend_idx] = request.arrival_rate

    # Create and solve the model
    try:
        solver = OpenNetworkMVASolver(
            centres=centres,
            routing_matrix=routing_matrix,
            external_arrivals=external_arrivals,
        )
        results = solver.solve()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Model solver failed: {e}")

    # Format results for JSON response
    preds = []
    for idx, name in enumerate(params["service_names"]):
        preds.append({
            "service": name,
            "predicted_response_time_ms": results.mean_response_times[idx] * 1000 if results.mean_response_times[idx] != float('inf') else float('inf'),
            "utilization": results.utilizations[idx],
            "visit_ratio": results.visit_ratios[idx],
        })
        
    response = {
        "arrival_rate": request.arrival_rate,
        "service_predictions": preds,
        "system_metrics": {
            "throughput": results.system_throughput,
            "system_response_time_ms": results.system_response_time * 1000,
        },
    }
    return response

@app.get("/measurements")
def get_measurements() -> List[Dict[str, Any]]:
    """Return the empirical measurement data as JSON."""
    try:
        return _load_measurements()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
