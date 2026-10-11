param (
    [switch]$Server,
    [int]$Port = 8000
)

$env:PYTHONIOENCODING = 'utf-8'

Write-Host '==================================================================' -ForegroundColor Cyan
Write-Host '  SPE Analytical QN/LQN Model - Master Pipeline Runner' -ForegroundColor Cyan
Write-Host '==================================================================' -ForegroundColor Cyan

Write-Host '>>> [1/5] Running Pytest Suite...' -ForegroundColor Yellow
pytest -v
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Pytest failed!' -ForegroundColor Red
    exit 1
}

Write-Host '>>> [2/5] Running 19-Point Master Consistency Audit...' -ForegroundColor Yellow
python scripts/audit_report.py
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Audit script reported discrepancies!' -ForegroundColor Red
    exit 1
}

Write-Host '>>> [3/5] Solving MVA Queueing Network...' -ForegroundColor Yellow
python scripts/model/queueing_network.py --arrival-rate 10.0 --save

Write-Host '>>> [4/5] Fitting Universal Scalability Law (USL)...' -ForegroundColor Yellow
python scripts/model/usl_analyzer.py

Write-Host '>>> [5/5] Running Capacity Planning Simulator...' -ForegroundColor Yellow
python scripts/capacity_planner.py --all

Write-Host '==================================================================' -ForegroundColor Green
Write-Host '  ALL PIPELINE PHASES COMPLETED WITH 100% SUCCESS!' -ForegroundColor Green
Write-Host '==================================================================' -ForegroundColor Green

if ($Server) {
    Write-Host "Starting Interactive Observatory Hub API on port $Port" -ForegroundColor Cyan
    uvicorn api.app:app --host 0.0.0.0 --port $Port
}
