import json
import numpy as np

# Command 2.1 — Cross-check the clean service demands
sd = json.load(open("audit_october/service_demands_clean.json"))
print(f"{'Service':25s} {'Mean (ms)':>10s} {'Median':>10s} {'P95':>10s} {'CoV':>8s} {'Samples':>8s} {'% Timeout':>10s}")
print("-" * 85)
for svc, v in sd.items():
    print(f"{svc:25s} {v['mean_service_time']*1000:>10.3f} {v['median_service_time']*1000:>10.3f} {v['p95_service_time']*1000:>10.3f} {v['cov']:>8.3f} {v['sample_count']:>8d} {v['pct_timeouts']:>9.2f}%")

print("\n" + "=" * 85 + "\n")

# Command 2.2 — Recompute demands and check the bottleneck
rp = json.load(open("audit_october/routing_probabilities_clean.json"))

services = list(sd.keys())
n = len(services)
idx = {s: i for i, s in enumerate(services)}

P = np.zeros((n, n))
for src, targets in rp.items():
    for dst, p in targets.items():
        if src in idx and dst in idx:
            P[idx[src], idx[dst]] = p

lam_ext = np.zeros(n)
lam_ext[idx['Frontend']] = 1.0
V = np.linalg.solve(np.eye(n) - P.T, lam_ext)

print(f"{'Service':25s} {'V_i':>8s} {'S (ms)':>10s} {'D (ms)':>10s} {'rho @10':>10s}")
print("-" * 70)
for s in sorted(services, key=lambda x: -V[idx[x]] * sd[x]['mean_service_time'] * 1000):
    V_i = V[idx[s]]
    S_ms = sd[s]['mean_service_time'] * 1000
    D_ms = V_i * S_ms
    rho = 10 * D_ms / 1000
    print(f"{s:25s} {V_i:>8.4f} {S_ms:>10.3f} {D_ms:>10.4f} {rho*100:>9.3f}%")

# Identify bottleneck
demands = {s: V[idx[s]] * sd[s]['mean_service_time'] * 1000 for s in services}
bottleneck = max(demands, key=demands.get)
sorted_demands = sorted(demands.values())
print(f"\nBottleneck: {bottleneck} (D = {demands[bottleneck]:.3f} ms)")
print(f"Second-heaviest: {sorted_demands[-2]:.3f} ms")
print(f"Imbalance ratio: {sorted_demands[-1] / sorted_demands[-2]:.2f}x")
