#!/usr/bin/env bash
# =====================================================================
# SPE Analytical Model — Master Execution Script (Linux/macOS)
# =====================================================================
set -e

export PYTHONIOENCODING="utf-8"

echo "=================================================================="
echo "  SPE Analytical QN/LQN Model — Master Pipeline Runner"
echo "=================================================================="

echo "\n>>> [1/5] Running Pytest Suite..."
pytest -v

echo "\n>>> [2/5] Running 19-Point Master Consistency Audit..."
python scripts/audit_report.py

echo "\n>>> [3/5] Solving MVA Queueing Network..."
python scripts/model/queueing_network.py --arrival-rate 10.0 --save

echo "\n>>> [4/5] Fitting Universal Scalability Law (USL)..."
python scripts/model/usl_analyzer.py

echo "\n>>> [5/5] Running Capacity Planning Simulator..."
python scripts/capacity_planner.py --all

echo "\n=================================================================="
echo "  ✅ ALL PIPELINE PHASES COMPLETED WITH 100% SUCCESS!"
echo "=================================================================="
