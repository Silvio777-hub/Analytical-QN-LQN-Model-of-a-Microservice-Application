import sys
import os
from fastapi.testclient import TestClient

# Add project root to the python path to import the API app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.app import app

client = TestClient(app)

def test_api_measurements():
    """Test the GET /measurements endpoint."""
    response = client.get("/measurements")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "service" in data[0]
        assert "mean_response_time_s" in data[0]

def test_api_solve_success():
    """Test successful POST /solve request with default configuration."""
    payload = {
        "arrival_rate": 5.0
    }
    response = client.post("/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["arrival_rate"] == 5.0
    assert "service_predictions" in data
    assert "system_metrics" in data
    
    # Verify predictions format
    preds = data["service_predictions"]
    assert any(p["service"] == "Frontend" for p in preds)

    assert len(preds) == 11  # all 11 service centres
    frontend = [p for p in preds if p["service"] == "Frontend"][0]
    assert "predicted_response_time_ms" in frontend
    assert "utilization" in frontend

def test_api_solve_invalid_arrival_rate():
    """Test validation errors for invalid arrival rates."""
    # Negative arrival rate
    payload = {
        "arrival_rate": -1.0
    }
    response = client.post("/solve", json=payload)
    assert response.status_code == 422  # Unprocessable Entity (ValidationError)

    # Zero arrival rate
    payload = {
        "arrival_rate": 0.0
    }
    response = client.post("/solve", json=payload)
    assert response.status_code == 422

def test_api_solve_replicas_override():
    """Test replica overrides."""
    payload = {
        "arrival_rate": 8.0,
        "replicas": {
            "Frontend": 2
        }
    }
    response = client.post("/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Ensure system doesn't saturate because Frontend has 2 replicas now
    preds = data["service_predictions"]
    frontend = [p for p in preds if p["service"] == "Frontend"][0]
    # Total utilization per server: offered_load / c
    # Offered load for Frontend at 8.0 req/s with V0=1.0 is 8.0 * 0.116 = 0.928
    # With 2 servers, utilization per server is 0.464
    assert frontend["utilization"] < 1.0

def test_api_solve_invalid_replicas():
    """Test validation errors for invalid replicas count."""
    payload = {
        "arrival_rate": 5.0,
        "replicas": {
            "Frontend": 0
        }
    }
    response = client.post("/solve", json=payload)
    assert response.status_code == 422
