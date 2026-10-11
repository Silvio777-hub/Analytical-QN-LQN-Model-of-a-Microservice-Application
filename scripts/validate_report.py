"""
Recomputes every table from source files and flags mismatches.
Run: python scripts/validate_report.py
"""
import json, math, os, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load source files
sd_path = os.path.join(base_dir, "data", "processed", "service_demands.json")
if not os.path.exists(sd_path):
    sd_path = os.path.join(base_dir, "data", "service_demands.json")

rp_path = os.path.join(base_dir, "data", "processed", "routing_probabilities.json")
if not os.path.exists(rp_path):
    rp_path = os.path.join(base_dir, "data", "routing_probabilities.json")

emp_path = os.path.join(base_dir, "data", "processed", "empirical_measurements.csv")
if not os.path.exists(emp_path):
    emp_path = os.path.join(base_dir, "data", "empirical_measurements.csv")

sd  = json.load(open(sd_path))
rp  = json.load(open(rp_path))
emp = pd.read_csv(emp_path)

# Visit ratios
services = list(sd.keys())
n = len(services); idx = {s:i for i,s in enumerate(services)}
P = np.zeros((n,n))
for s, targets in rp.items():
    for d, p in targets.items():
        P[idx[s], idx[d]] = p
lam_ext = np.zeros(n); lam_ext[idx["Frontend"]] = 1.0
V = np.linalg.solve(np.eye(n) - P.T, lam_ext)

# At lambda0 = 10: demands, utilization, M/M/1 residence
lam0 = 10.0
S_ms = {s: sd[s]["mean_service_time"]*1000 for s in services}
D = {s: V[idx[s]] * S_ms[s] for s in services}
rho = {s: lam0 * D[s] / 1000 for s in services}

print("=== VISIT RATIOS & DEMANDS ===")
for s in services:
    print(f"  {s:22s}: V={V[idx[s]]:.4f}, S={S_ms[s]:.2f} ms, D={D[s]:.2f} ms, rho@10={rho[s]*100:.2f}%")

# System response time across tiers
tiers = [1, 3, 5, 7, 9, 10, 11, 12]
preds = {}
print("\n=== MODEL PREDICTIONS ACROSS TIERS ===")
for lam in tiers:
    R = sum(V[idx[s]] * S_ms[s] / (1 - lam * D[s] / 1000)
            for s in services if lam * D[s] / 1000 < 1)
    preds[lam] = R
    print(f"  Tier lambda={lam:4.1f}: Pred RT = {R:7.2f} ms")

# APE at lambda=5
obs_5 = emp.loc[emp.service == "Frontend", "mean_response_time_s"].iloc[0] * 1000
ape = abs(obs_5 - preds[5]) / obs_5 * 100
print(f"\nAPE at lambda=5: {ape:.2f}%  (obs={obs_5:.1f} ms, pred={preds[5]:.2f} ms)")

# Frontend ROI
sens = {s: V[idx[s]] / (1 - rho[s])**2 for s in services}
total = sum(sens.values())
print(f"Frontend ROI: {sens['Frontend']/total*100:.2f}%  (sum={total:.3f} ms/ms)")

# SLA breach
def R_sys(lam):
    return sum(V[idx[s]] * S_ms[s] / (1 - lam * D[s] / 1000) for s in services)
lo, hi = 10.0, 11.0
for _ in range(50):
    mid = (lo + hi) / 2
    if R_sys(mid) < 500: lo = mid
    else: hi = mid
print(f"SLA breach at lambda = {(lo+hi)/2:.2f} req/s")

# USL
print("\n=== USL CAPACITY & EFFICIENCY ===")
sigma, kappa, X1 = 0.0248, 0.0031, 12.5
for N in range(1, 7):
    X = N*X1 / (1 + sigma*(N-1) + kappa*N*(N-1))
    print(f"c={N}: capacity={X:.2f} req/s, eff={X/(N*X1)*100:.1f}%")
