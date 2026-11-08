# Raw Trace Data — Dataset Inventory

This directory contains three Jaeger distributed trace collection runs performed on **October 8, 2026** from the live Google Online Boutique Docker Desktop deployment.

## Files

| File | Collected | Spans | Traces | Role |
|---|---|---|---|---|
| `trace_data_20261008_160832.json` | 2026-10-08 16:08:32 UTC | — | — | Preliminary warm-up run; used for initial parameter exploration only |
| `trace_data_20261008_175826.json` | 2026-10-08 17:58:26 UTC | **6,642** | **687** | ✅ **AUTHORITATIVE** — all report values derive from this file |
| `trace_data_20261008_184155.json` | 2026-10-08 18:41:55 UTC | — | — | Confirmatory / stability run; not used in report calculations |

## Authoritative Dataset Details

**File**: `trace_data_20261008_175826.json`  
**Collection timestamp**: October 8, 2026, 17:58:26 UTC  
**Total spans**: 6,642  
**Total traces**: 687  
**Source**: Jaeger all-services trace export at `http://localhost:16686/api/traces?service=frontend&limit=10000&start=...`

### Processed Derivatives

All downstream processed files derive from this authoritative raw dataset:

- `audit_october/service_demands_clean.json` — Canonical per-service exclusive CPU demands (ms)
- `data/processed/service_demands.json` — Alias; reconciled to match `service_demands_clean.json`
- `data/processed/multitier_empirical_measurements.csv` — 4-tier live load test results (λ ∈ {2, 5, 8, 10} req/s)
- `results/usl_parameters.json` — USL/M/M/c capacity model outputs
- `scripts/model/queueing_network_parameters.json` — QN model parameters

## Why Three Files?

The microservice load testing session on October 8, 2026 comprised three collection runs:

1. **16:08 run** — Initial collection while still tuning load generator parameters; Docker resources not yet fully warmed.
2. **17:58 run** — Stable, steady-state collection after full warm-up; this is the canonical dataset.
3. **18:41 run** — Post-analysis confirmatory run to verify stability of service time measurements.

The 16:08 and 18:41 files are retained for reproducibility and audit purposes only. **No report values derive from them.**

## Data Integrity

- Do not use `trace_data_20261008_160832.json` or `trace_data_20261008_184155.json` for calculations.
- If re-running analysis, always point scripts at `trace_data_20261008_175826.json`.
- The canonical Frontend exclusive CPU service demand is **S₀ = 18.880 ms** (mean across 687 traces).
