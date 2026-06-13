# Windows PowerShell Load Test Monitor for Online Boutique
#
# The Online Boutique includes a built-in load generator (Locust-based).
# This script configures and monitors the load test.
#
# Usage:
#   .\run_load_test.ps1              # Default: 10 users for 5 minutes
#   .\run_load_test.ps1 -Users 20 -Duration 600       # 20 users for 10 minutes

param (
    [int]$Users = 10,
    [int]$Duration = 300
)

$Frontend = "http://localhost:8080"

Write-Host "============================================"
Write-Host "  Online Boutique Load Test"
Write-Host "  Users: $Users"
Write-Host "  Duration: $($Duration)s"
Write-Host "  Frontend: $Frontend"
Write-Host "============================================"

# Check if frontend is reachable
Write-Host "Checking frontend..."
try {
    $response = Invoke-WebRequest -Uri $Frontend -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "Frontend is running!"
    } else {
        Write-Host "ERROR: Frontend returned status code $($response.StatusCode)"
        Write-Host "Make sure the deployment is running: docker-compose up -d"
        exit 1
    }
} catch {
    Write-Host "ERROR: Frontend not reachable at $Frontend"
    Write-Host "Make sure the deployment is running: docker-compose up -d"
    exit 1
}

Write-Host ""
Write-Host "Load generator is running via docker-compose (loadgenerator service)."
Write-Host "To change the number of users, update USERS env var in docker-compose.yaml."
Write-Host ""
Write-Host "Monitoring endpoints:"
Write-Host "  Frontend:    $Frontend"
Write-Host "  Prometheus:  http://localhost:9090"
Write-Host "  Jaeger UI:   http://localhost:16686"
Write-Host "  Grafana:     http://localhost:3000"
Write-Host ""
Write-Host "Waiting $($Duration)s for data collection..."

# Wait loop with progress bar
for ($i = 0; $i -lt $Duration; $i++) {
    Start-Sleep -Seconds 1
    $percent = [int](($i / $Duration) * 100)
    Write-Progress -Activity "Load test in progress" -Status "$($Duration - $i) seconds remaining" -PercentComplete $percent
}

Write-Host ""
Write-Host "Load test complete! Now collect data:"
Write-Host "  python scripts/data_collection/collect_metrics.py"
Write-Host "  python scripts/data_collection/parse_traces.py"
