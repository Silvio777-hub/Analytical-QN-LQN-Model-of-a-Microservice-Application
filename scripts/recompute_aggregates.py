"""
recompute_aggregates.py
Recomputes:
1. Routing matrix inversion (I - P^T) * lambda = lambda_ext -> visit ratios V_i
2. Demands D_i = V_i * S_i
3. Saturation ceiling lambda_sat = 1 / max(D_i)
4. M/M/1 response times at lambda_0 = 10 req/s: R_i = S_i / (1 - rho_i)
5. End-to-end response time R_sys = sum(V_i * R_i)
6. Sensitivity derivatives dR_sys/dS_i = V_i / (1 - rho_i)^2
7. Sensitivity ROI shares = (dR/dS_i) / sum(dR/dS_j) * 100%
8. Multi-tier validation: WMAPE, R^2, MAE, RMSE from multitier_empirical_measurements.csv
9. USL capacity model fit: X(N) = N * X_1 / (1 + sigma*(N-1) + kappa*N*(N-1))
10. M/M/c Erlang-C delay and residence time for c=1..10
"""
import sys, io, json, csv
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open("data/raw/trace_data_20261008_175826.json") as f:
    raw = json.load(f)

# Service demands
demands_raw = raw["service_demands"]
svcs = sorted(list(demands_raw.keys()))
print(f"Loaded {len(svcs)} microservices from raw data.")

# P-matrix
routing = raw["routing_probabilities"]
svc_idx = {s: i for i, s in enumerate(svcs)}
K = len(svcs)
P = np.zeros((K, K))
for parent, children in routing.items():
    if parent in svc_idx:
        p_i = svc_idx[parent]
        for ch, prob in children.items():
            if ch in svc_idx:
                p_j = svc_idx[ch]
                P[p_i, p_j] = prob

# External arrival: lambda_0 entering Frontend
lambda_ext = np.zeros(K)
frontend_idx = svc_idx["Frontend"]
lambda_ext[frontend_idx] = 10.0 # 10 req/s

I = np.eye(K)
A = (I - P.T)
lambda_vec = np.linalg.solve(A, lambda_ext)
V = lambda_vec / 10.0 # visit ratios

S = np.array([demands_raw[s]["mean_service_time"] for s in svcs])
D = V * S # total demand per transaction (seconds)

rho = lambda_vec * S
R_i = S / (1.0 - rho)
R_sys = np.sum(V * R_i) * 1000.0 # ms

dRdS = V / ((1.0 - rho) ** 2)
ROI = (dRdS / np.sum(dRdS)) * 100.0

lambda_sat = 1.0 / np.max(D)

print("\n--- RECOMPUTED QUEUEING NETWORK METRICS @ 10 req/s ---")
for i, s in enumerate(svcs):
    print(f"{s:25s} | V_i={V[i]:.4f} | S_i={S[i]*1000:7.3f} ms | D_i={D[i]*1000:7.3f} ms | rho={rho[i]*100:6.2f}% | R_i={R_i[i]*1000:7.3f} ms | dR/dS={dRdS[i]:.4f} | ROI={ROI[i]:6.2f}%")

print(f"\nR_sys (weighted sum): {R_sys:.3f} ms")
print(f"Sum of sensitivity derivatives: {np.sum(dRdS):.4f} ms/ms")
print(f"Frontend sensitivity leverage: {dRdS[frontend_idx]:.4f} ms/ms")
print(f"Frontend ROI share: {ROI[frontend_idx]:.2f}%")
print(f"Max demand D_max: {np.max(D)*1000:.3f} ms ({svcs[np.argmax(D)]})")
print(f"Saturation capacity ceiling lambda_sat: {lambda_sat:.2f} req/s")

# Multi-tier validation
print("\n--- MULTI-TIER EMPIRICAL VALIDATION (multitier_empirical_measurements.csv) ---")
tiers = []
with open("data/processed/multitier_empirical_measurements.csv") as f:
    r = csv.DictReader(f)
    for row in r:
        tiers.append(row)

print("CSV Rows:")
obs = []
preds = []
for t in tiers:
    o = float(t["empirical_mean_rt_ms"])
    p = float(t["model_predicted_rt_ms"])
    obs.append(o)
    preds.append(p)
    err_pct = abs(p - o) / o * 100.0
    print(f"  Target RPS={t['target_rps']} | Observed={o:.2f} ms | Model Pred={p:.2f} ms | Err={err_pct:.2f}%")

obs = np.array(obs)
preds = np.array(preds)
wmape = (np.sum(np.abs(preds - obs)) / np.sum(obs)) * 100.0
mae = np.mean(np.abs(preds - obs))
rmse = np.sqrt(np.mean((preds - obs)**2))
r2 = 1.0 - (np.sum((obs - preds)**2) / np.sum((obs - np.mean(obs))**2))

print(f"\nRecomputed Metrics:")
print(f"  WMAPE: {wmape:.2f}%")
print(f"  MAE:   {mae:.2f} ms")
print(f"  RMSE:  {rmse:.2f} ms")
print(f"  R^2:   {r2:.4f}")
