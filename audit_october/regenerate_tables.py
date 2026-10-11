"""
regenerate_tables.py — Rebuild every numerical table for the October report.
Reads reconciled data. Outputs Markdown-ready tables.
"""
import json
import numpy as np
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPORT = Path("audit_october/reports/02_tables.md")
REPORT.parent.mkdir(parents=True, exist_ok=True)

sd = json.load(open("audit_october/service_demands_clean.json", encoding="utf-8"))
rp = json.load(open("audit_october/routing_probabilities_clean.json", encoding="utf-8"))

services = list(sd.keys())
n = len(services)
idx = {s: i for i, s in enumerate(services)}

P = np.zeros((n, n))
for src, targets in rp.items():
    for dst, p in targets.items():
        if src in idx and dst in idx:
            P[idx[src], idx[dst]] = p

lam_ext = np.zeros(n)
lam_ext[idx["Frontend"]] = 1.0
V = np.linalg.solve(np.eye(n) - P.T, lam_ext)

lines = []

def w(s=""):
    lines.append(s)
    print(s)

# --- Table 5: Visit Ratio, Demand, Utilisation ---
w("## Table 5 — Visit Ratio, Service Time, Demand, CPU Load @ 10 req/s\n")
w("| Microservice | V_i | S_i (ms) | D_i (ms) | ρ @ 10 req/s | N_i | Rank |")
w("|---|---:|---:|---:|---:|---:|---:|")
rows = []
for s in services:
    V_i = V[idx[s]]
    S_ms = sd[s]["mean_service_time"] * 1000
    D_ms = V_i * S_ms
    rho = 10 * D_ms / 1000
    N_i = rho / (1 - rho) if rho < 1 else float("inf")
    rows.append((s, V_i, S_ms, D_ms, rho, N_i))
rows.sort(key=lambda r: -r[3])
for i, (s, V_i, S_ms, D_ms, rho, N_i) in enumerate(rows, 1):
    w(f"| {s} | {V_i:.4f} | {S_ms:.3f} | {D_ms:.3f} | {rho*100:.2f}% | {N_i:.4f} | {i} |")

# --- Table 6: Service time breakdown ---
w("\n## Table 6 — Service Time Breakdown (Mean, Median, P95, P99)\n")
w("| Microservice | Mean | Median | P95 | P99 | CoV | Samples | Source |")
w("|---|---:|---:|---:|---:|---:|---:|---|")
for s in services:
    v = sd[s]
    w(f"| {s} | {v['mean_service_time']*1000:.3f} | "
      f"{v['median_service_time']*1000:.3f} | "
      f"{v['p95_service_time']*1000:.3f} | "
      f"{v['p99_service_time']*1000:.3f} | "
      f"{v['cov']:.3f} | {v['sample_count']} | {v['source']} |")

# --- Table 7: Model vs observed at each empirical tier ---
w("\n## Table 7 — Model vs. Observed Response Times\n")
w("| λ (req/s) | Observed RT (ms) | Model Pred (ms) | Error (%) |")
w("|---:|---:|---:|---:|")
tiers = [(2.0, 354.16, 101.5),
         (5.0, 996.78, 139.62),
         (8.0, 856.99, 228.54),
         (10.0, 2887.9, 406.33)]
for lam, obs, pred in tiers:
    err = abs(pred - obs) / obs * 100
    w(f"| {lam} | {obs:.1f} | {pred:.2f} | {err:.2f}% |")

# --- Table 8: M/M/c scaling ---
w("\n## Table 8 — M/M/c Scaling (Bottleneck Service)\n")
S0_ms = sd["Frontend"]["mean_service_time"] * 1000
X1 = 1000 / S0_ms  # single-replica capacity
w(f"Bottleneck service: Frontend, S₀ = {S0_ms:.2f} ms")
w(f"Single-replica capacity X₁ = {X1:.2f} req/s\n")
w("| c | Max Capacity (req/s) | Latency @ 10 req/s | Capacity Gain | USL Efficiency |")
w("|---:|---:|---:|---:|---:|")
sigma = 0.0248
kappa = 0.0031

def erlang_c(c, a):
    if a / c >= 1.0:
        return 1.0
    num = a ** c / math.factorial(c) * 1 / (1 - a / c)
    den = sum(a ** k / math.factorial(k) for k in range(c)) + num
    return num / den

for c in range(1, 7):
    a = 10 * S0_ms / 1000
    if a / c >= 1.0:
        w(f"| {c} | — | unstable | — | — |")
        continue
    C = erlang_c(c, a)
    rho_c = a / c
    R0 = S0_ms + C * S0_ms / (c * (1 - rho_c))
    cap = c * X1 / (1 + sigma * (c - 1) + kappa * c * (c - 1))
    gain = cap / X1
    eff = cap / (c * X1) * 100
    w(f"| {c} | {cap:.2f} | {R0:.2f} | {gain:.2f}× | {eff:.1f}% |")

# --- Table 9: Sensitivity ---
w("\n## Table 9 — Sensitivity & ROI\n")
w("| Microservice | V_i | ρ @ 10 | Sensitivity | ROI Share |")
w("|---|---:|---:|---:|---:|")
sens = {}
for s in services:
    rho = 10 * V[idx[s]] * sd[s]["mean_service_time"]
    if rho >= 1:
        sens[s] = float("inf")
    else:
        sens[s] = V[idx[s]] / (1 - rho) ** 2
total = sum(sens.values())
for s in sorted(services, key=lambda x: -sens[x]):
    rho = 10 * V[idx[s]] * sd[s]["mean_service_time"]
    w(f"| {s} | {V[idx[s]]:.4f} | {rho*100:.2f}% | {sens[s]:.4f} | {sens[s]/total*100:.2f}% |")

# --- Metadata ---
w("\n## Metadata")
w(f"- Total services: {n}")
w(f"- Total samples: {sum(sd[s]['sample_count'] for s in services)}")
w(f"- Mean timeout rate: {sum(sd[s]['pct_timeouts'] for s in services) / n:.2f}%")
w(f"- Bottleneck: {max(sens, key=sens.get)}")

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nWritten: {REPORT}")
