# =====================================================================
# SPE Analytical Model — Master Makefile
# =====================================================================

.PHONY: all test audit solve usl capacity figures server clean help

PYTHON ?= python

help:
	@echo "=================================================================="
	@echo " SPE Analytical Model — Make Targets"
	@echo "=================================================================="
	@echo " make all        : Run full pipeline (tests, audit, solve, figures)"
	@echo " make test       : Run unit & integration test suite (pytest)"
	@echo " make audit      : Run 19-point Master Consistency Audit"
	@echo " make solve      : Execute MVA queueing network solver"
	@echo " make usl        : Fit & export Universal Scalability Law parameters"
	@echo " make capacity   : Run interactive what-if capacity planner"
	@echo " make figures    : Generate all high-DPI validation figures"
	@echo " make server     : Start interactive FastAPI & dashboard server"
	@echo " make clean      : Remove Python cache and temporary files"
	@echo "=================================================================="

all: test audit solve usl figures
	@echo "\n>>> Full pipeline executed and verified successfully! <<<\n"

test:
	pytest -v

audit:
	$(PYTHON) scripts/audit_report.py

solve:
	$(PYTHON) scripts/model/queueing_network.py --arrival-rate 10.0 --save

usl:
	$(PYTHON) scripts/model/usl_analyzer.py

capacity:
	$(PYTHON) scripts/capacity_planner.py --all

figures:
	$(PYTHON) scripts/validation/generate_report_figures_10.py

server:
	uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
