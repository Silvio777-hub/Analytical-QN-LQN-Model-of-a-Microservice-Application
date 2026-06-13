#!/bin/bash
# Load Test Runner for Online Boutique
#
# The Online Boutique includes a built-in load generator (Locust-based).
# This script configures and monitors the load test.
#
# Usage:
#   ./run_load_test.sh              # Default: 10 users for 5 minutes
#   ./run_load_test.sh 20 600       # 20 users for 10 minutes

USERS=${1:-10}
DURATION=${2:-300}    # seconds
FRONTEND="http://localhost:8080"

echo "============================================"
echo "  Online Boutique Load Test"
echo "  Users: $USERS"
echo "  Duration: ${DURATION}s"
echo "  Frontend: $FRONTEND"
echo "============================================"

# Check if frontend is reachable
echo "Checking frontend..."
if ! curl -s --max-time 5 "$FRONTEND" > /dev/null 2>&1; then
    echo "ERROR: Frontend not reachable at $FRONTEND"
    echo "Make sure the deployment is running: docker-compose up -d"
    exit 1
fi
echo "Frontend is running!"

# The built-in loadgenerator in docker-compose handles load generation.
# This script monitors the test duration and collects data.

echo ""
echo "Load generator is running via docker-compose (loadgenerator service)."
echo "To change the number of users, update USERS env var in docker-compose.yaml."
echo ""
echo "Monitoring endpoints:"
echo "  Frontend:    $FRONTEND"
echo "  Prometheus:  http://localhost:9090"
echo "  Jaeger UI:   http://localhost:16686"
echo "  Grafana:     http://localhost:3000"
echo ""
echo "Waiting ${DURATION}s for data collection..."

# Wait for the specified duration
sleep $DURATION

echo ""
echo "Load test complete! Now collect data:"
echo "  python scripts/data_collection/collect_metrics.py"
echo "  python scripts/data_collection/parse_traces.py"
