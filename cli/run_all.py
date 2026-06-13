import argparse
import subprocess
import sys
import os
import yaml

# Determine project root (assumes this script lives in <project>/cli)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def run_collect_metrics():
    script = os.path.join(PROJECT_ROOT, 'scripts', 'data_collection', 'collect_metrics.py')
    subprocess.run([sys.executable, script], check=True)

def run_queueing_network(arrival_rate: float, replicas: dict | None = None):
    script = os.path.join(PROJECT_ROOT, 'scripts', 'model', 'queueing_network.py')
    args = [sys.executable, script, '--arrival', str(arrival_rate), '--save']
    if replicas:
        import json
        args.extend(['--replicas', json.dumps(replicas)])
    subprocess.run(args, check=True)

def run_validation():
    script = os.path.join(PROJECT_ROOT, 'scripts', 'validation', 'compare.py')
    measurements = os.path.join(PROJECT_ROOT, 'data', 'processed', 'empirical_measurements.csv')
    subprocess.run([sys.executable, script, '--measurements', measurements], check=True)

def start_api_server(port: int):
    # Launch FastAPI via uvicorn in a subprocess (non‑blocking)
    cmd = [sys.executable, '-m', 'uvicorn', 'api.app:app', '--host', '0.0.0.0', '--port', str(port)]
    proc = subprocess.Popen(cmd)
    print(f"FastAPI server started on http://0.0.0.0:{port}")
    return proc

def main():
    parser = argparse.ArgumentParser(description='Run the full analytical QN workflow')
    parser.add_argument('--arrival', type=float, required=True, help='External arrival rate (requests per second)')
    parser.add_argument('--replicas', type=str, default=None,
                        help='Path to a YAML file defining per‑service replica counts, e.g. {Frontend: 2, Checkout: 1}')
    parser.add_argument('--run-server', action='store_true', help='Start the FastAPI server after the run')
    parser.add_argument('--port', type=int, default=8000, help='Port for the FastAPI server (default 8000)')
    args = parser.parse_args()

    # Load replica mapping if supplied
    replica_map = None
    if args.replicas:
        with open(args.replicas, 'r', encoding='utf-8') as f:
            replica_map = yaml.safe_load(f)
        print(f"Loaded replica map: {replica_map}")

    print("=== Step 1: Collecting metrics ===")
    run_collect_metrics()
    print("=== Step 2: Solving queueing network ===")
    run_queueing_network(args.arrival, replica_map)
    print("=== Step 3: Validation against empirical data ===")
    run_validation()
    print("=== Workflow completed ===")

    if args.run_server:
        print("=== Starting FastAPI server ===")
        proc = start_api_server(args.port)
        try:
            print("FastAPI server running. Press Ctrl+C to stop it.")
            proc.wait()
        except KeyboardInterrupt:
            print("\nStopping FastAPI server...")
            proc.terminate()
            proc.wait()
            print("FastAPI server stopped.")

if __name__ == '__main__':
    main()
