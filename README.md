# SPE Project #2: Analytical QN/LQN Model of a Microservice Application

## Objective

Develop an analytical queueing network model of **Google Online Boutique** (11 microservices)
and validate predictions against empirical measurements.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Environment Setup](#environment-setup)
5. [Deploying the Online Boutique (Monitoring Stack)](#deploying-the-online-boutique-monitoring-stack)
6. [Running a Load Test](#running-a-load-test)
7. [Collecting Empirical Metrics](#collecting-empirical-metrics)
8. [Running the Queueing Network Model](#running-the-queueing-network-model)
9. [Validating Predictions Against Measurements](#validating-predictions-against-measurements)
10. [Running the Full Workflow (CLI)](#running-the-full-workflow-cli)
11. [FastAPI Server & Web Dashboard](#fastapi-server--web-dashboard)
12. [Running via Docker (Optional)](#running-via-docker-optional)
13. [Running Tests](#running-tests)
14. [Monitoring Interfaces](#monitoring-interfaces)
15. [Methodology](#methodology)
16. [Project Report](#project-report)
17. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

Google Online Boutique is a cloud-native demo application with 11 microservices:

| Service              | Language | Role                                      |
|----------------------|----------|-------------------------------------------|
| Frontend             | Go       | HTTP server serving the website            |
| CartService          | C#       | Stores shopping cart in Redis              |
| ProductCatalogService| Go       | Provides product list and details          |
| CurrencyService      | Node.js  | Converts currencies                        |
| PaymentService       | Node.js  | Charges credit card (mock)                 |
| ShippingService      | Go       | Provides shipping cost estimates           |
| EmailService         | Python   | Sends order confirmation emails (mock)     |
| CheckoutService      | Go       | Orchestrates checkout flow                 |
| RecommendationService| Python   | Recommends products based on cart          |
| AdService            | Java     | Provides text ads based on context         |
| Redis                | -        | In-memory store for cart data              |

---

## Project Structure

```
PROJECT/
├── README.md                              # This file
├── Dockerfile                             # Container image for analysis scripts
├── requirements.txt                       # Python dependencies
│
├── api/
│   ├── app.py                             # FastAPI REST API (solve model, get measurements)
│   └── static/
│       └── index.html                     # SPE Observatory Hub web dashboard
│
├── cli/
│   └── run_all.py                         # CLI runner: collect → solve → validate → serve
│
├── scripts/
│   ├── model/
│   │   ├── queueing_network.py            # Main QN model definition & analysis
│   │   ├── mva_solver.py                  # Core Open-network MVA solver (M/M/1 & M/M/c)
│   │   └── queueing_network_parameters.json  # Saved model parameters for the API
│   ├── data_collection/
│   │   ├── collect_metrics.py             # Scrape Prometheus for service metrics
│   │   └── parse_traces.py               # Extract routing probabilities from Jaeger
│   ├── validation/
│   │   └── compare.py                     # Compare predictions vs. measurements + plots
│   └── load_testing/
│       ├── run_load_test.ps1              # PowerShell load test monitor (Windows)
│       └── run_load_test.sh               # Bash load test monitor (Linux/macOS)
│
├── deployment/
│   ├── docker-compose.yaml                # Online Boutique + Monitoring (Prometheus, Jaeger, Grafana)
│   ├── prometheus.yml                     # Prometheus scrape config
│   ├── otel-collector-config.yaml         # OpenTelemetry Collector routing
│   └── grafana/                           # Grafana provisioning (dashboards/datasources)
│
├── data/
│   ├── processed/                         # Cleaned metrics CSVs, service_times.json, routing_probabilities.json
│   └── raw/                               # Raw Prometheus JSON exports
│
├── results/
│   ├── model_predictions.json             # MVA solver output
│   └── figures/                           # Generated plots (utilization, response time, etc.)
│
├── tests/
│   ├── test_solver.py                     # Unit tests for the MVA solver
│   └── test_api.py                        # Integration tests for the FastAPI API
│
└── docs/
    ├── FINAL_REPORT.md                    # Comprehensive project report
    ├── model_description.md               # QN diagram + formulas
    ├── validation_report.md               # Predictions vs. measurements analysis
    └── Explanation.md                     # Supplementary explanation
```

---

## Prerequisites

| Requirement       | Version   | Purpose                                           |
|--------------------|-----------|--------------------------------------------------|
| **Docker**         | 20.10+    | Run the Online Boutique microservices + monitoring |
| **Docker Compose** | v2+       | Orchestrate multi-container deployment             |
| **Python**         | 3.9+      | Run model scripts, API server, CLI                 |
| **Git**            | any       | Clone the repository                               |

> **Note:** Python is only required if you run the analysis scripts locally. You can alternatively run everything inside Docker (see [Running via Docker](#running-via-docker-optional)).

---

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SPE-Project
```

### 2. Create a Python Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi`, `uvicorn[standard]`, `pydantic` — REST API server
- `numpy`, `scipy` — numerical computation & MVA solver
- `pandas`, `matplotlib`, `seaborn` — data analysis & plotting
- `requests` — HTTP client for Prometheus/Jaeger queries
- `pyyaml` — YAML parsing for replica configs
- `pytest` — test framework

### 4. Verify the Installation

```bash
python -c "import fastapi, numpy, matplotlib; print('All dependencies OK')"
```

---

## Deploying the Online Boutique (Monitoring Stack)

The `deployment/` directory contains a Docker Compose file that brings up all 11 Online Boutique microservices along with the full observability stack.

### Start the Stack

```bash
cd deployment
docker-compose up -d
```

This launches the following containers:

| Container              | Port(s)                      | Description                           |
|------------------------|------------------------------|---------------------------------------|
| `frontend`             | `8080`                       | Online Boutique web UI                |
| `cartservice`          | —                            | Shopping cart (backed by Redis)        |
| `productcatalogservice`| —                            | Product catalog                       |
| `currencyservice`      | —                            | Currency conversion                   |
| `paymentservice`       | —                            | Payment processing (mock)             |
| `shippingservice`      | —                            | Shipping cost estimates               |
| `emailservice`         | —                            | Order confirmation emails (mock)      |
| `checkoutservice`      | —                            | Checkout orchestration                |
| `recommendationservice`| —                            | Product recommendations               |
| `adservice`            | —                            | Context-based advertisements          |
| `redis-cart`           | —                            | Redis for cart state                  |
| `loadgenerator`        | —                            | Built-in Locust-based load generator  |
| `prometheus`           | `9090`                       | Metrics collection                    |
| `jaeger`               | `16686`                      | Distributed tracing UI                |
| `grafana`              | `3100`                       | Dashboards                            |
| `cadvisor`             | `8081`                       | Container resource monitoring         |
| `otel-collector`       | `4317`, `4318`, `8889`       | OpenTelemetry Collector               |

### Verify the Deployment

Open your browser and check:
- **Frontend:** http://localhost:8080  
- **Prometheus:** http://localhost:9090  
- **Jaeger UI:** http://localhost:16686  

### Stop the Stack

```bash
cd deployment
docker-compose down
```

---

## Running a Load Test

The Docker Compose stack includes a built-in **load generator** (Locust-based) that automatically generates traffic against the frontend. By default it simulates **10 concurrent users**.

To change the number of simulated users, edit `USERS` in `deployment/docker-compose.yaml`:
```yaml
loadgenerator:
  environment:
    USERS: "20"    # Change this value
```

Then restart the load generator:
```bash
cd deployment
docker-compose restart loadgenerator
```

### Monitor the Load Test (Optional)

Use the provided scripts to monitor the load test and wait for data collection:

**Windows (PowerShell):**
```powershell
.\scripts\load_testing\run_load_test.ps1                     # Default: 10 users, 5 minutes
.\scripts\load_testing\run_load_test.ps1 -Users 20 -Duration 600   # 20 users, 10 minutes
```

**Linux / macOS:**
```bash
./scripts/load_testing/run_load_test.sh              # Default: 10 users, 5 minutes
./scripts/load_testing/run_load_test.sh 20 600       # 20 users, 10 minutes
```

> **Tip:** Let the load generator run for at least **5 minutes** before collecting metrics, so Prometheus has enough data for accurate rate calculations.

---

## Collecting Empirical Metrics

Once the monitoring stack has been running and the load generator has produced traffic, collect metrics from Prometheus and Jaeger:

### Collect Service Metrics (from Prometheus)

```bash
python scripts/data_collection/collect_metrics.py
```

**Options:**
| Flag             | Default                    | Description                       |
|------------------|----------------------------|-----------------------------------|
| `--prometheus`   | `http://localhost:9090`    | Prometheus URL                    |
| `--jaeger`       | `http://localhost:16686`   | Jaeger URL (for container mapping)|
| `--output`       | `data/processed`           | Output directory                  |

This collects:
- Request rates (req/s) per service
- Mean response times (seconds) per service
- CPU utilization per service (from cAdvisor)

Output files are saved to `data/processed/` as timestamped CSV files and `service_times.json`.

### Extract Routing Probabilities (from Jaeger)

```bash
python scripts/data_collection/parse_traces.py
```

This analyzes Jaeger traces to compute the routing probability matrix and saves it to `data/processed/routing_probabilities.json`.

---

## Running the Queueing Network Model

### Basic Run (Default Parameters)

Run the model with estimated parameters from source code analysis:

```bash
python scripts/model/queueing_network.py
```

### Run with Empirical Data

Use the collected metrics as input parameters:

```bash
python scripts/model/queueing_network.py --data data/processed
```

### Run with a Custom Arrival Rate

```bash
python scripts/model/queueing_network.py --rate 15
```

### Sweep Arrival Rates & Generate Plots

Sweep from 1 to 50 req/s and generate utilization and response time plots:

```bash
python scripts/model/queueing_network.py --sweep --save
```

### Full Example (Empirical Data + Save + Sweep)

```bash
python scripts/model/queueing_network.py --data data/processed --rate 10 --save --sweep
```

**Command-Line Flags:**
| Flag                 | Default  | Description                                       |
|----------------------|----------|---------------------------------------------------|
| `--rate` / `--arrival`| `10.0`  | External arrival rate in req/s                    |
| `--data`             | `None`   | Path to empirical data directory                  |
| `--sweep`            | `False`  | Sweep arrival rates and generate performance plots|
| `--save`             | `False`  | Save predictions to `results/` and model params   |

**Output:**
- Console: per-service utilization, response times, throughput, and bottleneck analysis
- `results/model_predictions.json` — solver output (when `--save` is used)
- `results/figures/utilization_vs_arrival_rate.png` — utilization plot (when `--sweep`)
- `results/figures/response_time_vs_arrival_rate.png` — response time plot (when `--sweep`)
- `results/figures/system_response_time.png` — end-to-end response time (when `--sweep`)

---

## Validating Predictions Against Measurements

Compare model predictions with empirical data:

```bash
python scripts/validation/compare.py \
  --predictions results/model_predictions.json \
  --measurements data/processed/empirical_measurements.csv
```

### Run with Demo/Sample Data

If you don't have empirical data yet, use the built-in sample data:

```bash
python scripts/validation/compare.py --demo
```

**Command-Line Flags:**
| Flag             | Default                                           | Description                      |
|------------------|---------------------------------------------------|----------------------------------|
| `--predictions`  | `results/model_predictions.json`                  | Path to model predictions JSON   |
| `--measurements` | `None`                                            | Path to measurements CSV         |
| `--output`       | `results/figures`                                 | Output directory for figures     |
| `--demo`         | `False`                                           | Run with sample data             |

**Output:**
- Error metrics: RMSE, MAE, MAPE
- `results/figures/comparison_response_time.png` — bar chart of predicted vs. measured
- `results/figures/scatter_response_time.png` — scatter plot with perfect-prediction line
- `results/figures/error_heatmap.png` — per-service error heatmap
- `results/figures/comparison_summary.txt` — detailed text report

---

## Running the Full Workflow (CLI)

The CLI runner (`cli/run_all.py`) executes all steps in sequence:

1. Collect metrics from Prometheus/Jaeger
2. Solve the queueing network model
3. Validate predictions against empirical data
4. (Optionally) start the FastAPI server

```bash
python cli/run_all.py --arrival 10
```

### With Replica Overrides

Create a YAML file (e.g., `replicas.yaml`):
```yaml
Frontend: 2
CheckoutService: 3
```

Then run:
```bash
python cli/run_all.py --arrival 10 --replicas replicas.yaml
```

### With the API Server

```bash
python cli/run_all.py --arrival 10 --run-server --port 8000
```

**Command-Line Flags:**
| Flag           | Default | Description                                        |
|----------------|---------|-----------------------------------------------------|
| `--arrival`    | —       | **(Required)** External arrival rate in req/s       |
| `--replicas`   | `None`  | Path to YAML file with per-service replica counts   |
| `--run-server` | `False` | Start the FastAPI server after the workflow          |
| `--port`       | `8000`  | Port for the FastAPI server                         |

---

## FastAPI Server & Web Dashboard

The project includes a REST API and a web-based dashboard for interactive exploration.

### Start the API Server

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

Then open:
- **Web Dashboard:** http://localhost:8000  
- **API Docs (Swagger):** http://localhost:8000/docs  

### API Endpoints

#### `POST /solve`

Solve the queueing network for a given arrival rate:

```bash
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{"arrival_rate": 10.0}'
```

With replica overrides:
```bash
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{"arrival_rate": 10.0, "replicas": {"Frontend": 2, "CheckoutService": 3}}'
```

**Response:**
```json
{
  "arrival_rate": 10.0,
  "service_predictions": [
    {
      "service": "Frontend",
      "predicted_response_time_ms": 150.2,
      "utilization": 0.72,
      "visit_ratio": 1.0
    }
  ],
  "system_metrics": {
    "throughput": 10.0,
    "system_response_time_ms": 312.5
  }
}
```

#### `GET /measurements`

Return the empirical measurement data as JSON:

```bash
curl http://localhost:8000/measurements
```

---

## Running via Docker (Optional)

You can run all analysis scripts inside a Docker container without installing Python locally.

### 1. Build the Docker Image

```bash
docker build -t spe-model .
```

### 2. Run the QN Model

```bash
docker run --rm -v "${PWD}/results:/app/results" spe-model \
  python scripts/model/queueing_network.py --data data/processed --rate 10 --save --sweep
```

### 3. Run the Validation

```bash
docker run --rm -v "${PWD}/results:/app/results" spe-model \
  python scripts/validation/compare.py --measurements data/processed/empirical_measurements.csv
```

### 4. Start the API Server in Docker

```bash
docker run --rm -p 8000:8000 spe-model \
  uvicorn api.app:app --host 0.0.0.0 --port 8000
```

---

## Running Tests

The project includes unit tests for the MVA solver and integration tests for the API.

### Run All Tests

```bash
pytest tests/ -v
```

### Run Individual Test Files

```bash
pytest tests/test_solver.py -v    # MVA solver unit tests
pytest tests/test_api.py -v       # FastAPI integration tests
```

### Test Summary

| Test File          | Tests                                                                  |
|--------------------|------------------------------------------------------------------------|
| `test_solver.py`   | M/M/1 single node, M/M/c multi-server stability, closed-loop detection, textbook visit ratios |
| `test_api.py`      | GET /measurements, POST /solve (success, invalid input, replica overrides) |

---

## Monitoring Interfaces

When the Docker Compose stack is running, the following UIs are available:

| Interface     | URL                        | Credentials             |
|---------------|----------------------------|--------------------------|
| **Frontend**  | http://localhost:8080       | —                        |
| **Prometheus**| http://localhost:9090       | —                        |
| **Jaeger UI** | http://localhost:16686      | —                        |
| **Grafana**   | http://localhost:3100       | admin / admin            |
| **cAdvisor**  | http://localhost:8081       | —                        |

### Useful Prometheus Queries

```promql
# Request rate per service
sum(rate(grpc_server_handled_total[5m])) by (grpc_service)

# Mean response time per service
sum(rate(grpc_server_handling_seconds_sum[5m])) by (grpc_service)
  / sum(rate(grpc_server_handling_seconds_count[5m])) by (grpc_service)

# CPU utilization per container
sum(rate(container_cpu_usage_seconds_total[5m])) by (container)
```

---

## Methodology

1. **Workload Measurement**: Collect arrival rates, service times, and utilization
   from Prometheus; extract routing probabilities from Jaeger traces.
2. **Model Construction**: Build an Open Queueing Network with each microservice
   as an M/M/1 (or M/M/c) service centre, parameterized by the collected data.
3. **Model Solution**: Solve via Mean Value Analysis (MVA) for throughput,
   response time, and utilization at each service.
4. **Validation**: Compare model predictions against empirical measurements
   and analyze deviations using RMSE, MAE, and MAPE.

---

## Project Report

The comprehensive project report containing all modeling results and validation analysis is at:

📄 **[docs/FINAL_REPORT.md](docs/FINAL_REPORT.md)**

Additional documentation:
- [Model Description](docs/model_description.md) — QN diagram, formulas, and service centre definitions
- [Validation Report](docs/validation_report.md) — detailed predictions vs. measurements analysis

---

## Troubleshooting

### Docker Compose fails to start
- Make sure Docker Desktop is running.
- Ensure ports `8080`, `9090`, `16686`, `3100`, `8081` are not in use.
- Try `docker-compose down` then `docker-compose up -d` again.

### Prometheus returns no data
- Wait at least **2–3 minutes** after starting the stack for scrape intervals to kick in.
- Verify the services are running: `docker-compose ps`.
- Check the Prometheus targets page: http://localhost:9090/targets.

### `collect_metrics.py` reports all zeros
- The monitoring stack must be running and the load generator must be producing traffic.
- Make sure you've waited long enough for rate calculations (at least 5 minutes of data).

### `ModuleNotFoundError` when running scripts
- Make sure you've activated the virtual environment and installed dependencies:
  ```bash
  source .venv/bin/activate   # or .\.venv\Scripts\Activate.ps1 on Windows
  pip install -r requirements.txt
  ```

### API server can't find `queueing_network_parameters.json`
- Run the model with `--save` first to generate the parameters file:
  ```bash
  python scripts/model/queueing_network.py --save
  ```

### Tests fail with import errors
- Run tests from the project root directory:
  ```bash
  pytest tests/ -v
  ```
