"""
Universal Scalability Law (USL) Analyzer for Online Boutique
=============================================================
Calculates Gunther's USL parameters (sigma: contention, kappa: coherency)
and models capacity scaling efficiency for multi-replica Frontend deployment.

USL Capacity Formula:
    C(N) = N / (1 + sigma*(N - 1) + kappa*N*(N - 1))

Efficiency Formula:
    eta(N) = C(N) / N = 1 / (1 + sigma*(N - 1) + kappa*N*(N - 1))
"""

import json
import math
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def erlang_c(c: int, a: float) -> float:
    """Erlang-C queueing probability C(c, a) for an M/M/c queue.

    Args:
        c: Number of parallel servers (replicas).
        a: Offered traffic load in Erlangs (lambda * S).

    Returns:
        P(queueing) — probability an arriving request must wait.
    """
    rho_per = a / c
    if rho_per >= 1.0:
        return 1.0
    sum_terms = sum((a ** k) / math.factorial(k) for k in range(c))
    last_term = (a ** c) / math.factorial(c) * (1.0 / (1.0 - rho_per))
    return last_term / (sum_terms + last_term)


def mmc_response_time(S: float, lam: float, c: int) -> float:
    """Mean response time for M/M/c queue via Erlang-C formula.

    R(c) = S + C(c, a) * S / (c * (1 - rho_c))

    Args:
        S:   Exclusive service time per request (seconds).
        lam: Arrival rate directed to this service tier (req/s).
        c:   Number of parallel server replicas.

    Returns:
        Mean residence time in seconds.
    """
    a = lam * S          # offered load in Erlangs
    rho_per = a / c      # per-replica utilisation fraction
    if rho_per >= 1.0:
        return float("inf")
    Cca = erlang_c(c, a)
    wait = Cca * S / (c * (1.0 - rho_per))
    return S + wait


def compute_usl_profile():
    """Compute and export the USL scaling profile for the Frontend bottleneck.

    Parameters taken directly from the project report (Table 3 / Table 8):
      - sigma = 0.0248  (2.48% serialisation contention — Kubernetes iptables routing)
      - kappa = 0.0031  (0.31% coherency crosstalk — network overlay hops)
      - X1    = 12.50 req/s  (single-pod saturation capacity: 1 / S0 = 1 / 0.080)
      - S0    = 0.080 s      (Frontend exclusive CPU service demand)
      - lambda = 10.0 req/s  (nominal operating arrival rate)

    Backend response-time contribution is Sigma(V_i * R_i) for all non-Frontend
    services at lambda_0 = 10 req/s, computed by the MVA solver:
      backend_ms = 5.019 ms
    """
    np.random.seed(42)  # reproducibility — ensures deterministic output

    # ── Model parameters (report Table 3) ──────────────────────────────────
    sigma = 0.0248           # Amdahl serialisation coefficient
    kappa = 0.0031           # Coherency crosstalk coefficient
    base_saturation_rps = 12.5   # Single-pod saturation: 1 / S0
    S0 = 0.080               # Frontend exclusive service demand (seconds)
    lambda_nom = 10.0        # Nominal operating arrival rate (req/s)
    backend_ms = 5.019       # Backend Sigma(V_i * R_i) at 10 req/s (ms)

    replicas = list(range(1, 11))
    capacities = []
    efficiencies = []
    system_latencies_ms = []

    for n in replicas:
        denom = 1.0 + sigma * (n - 1) + kappa * n * (n - 1)

        # USL saturation capacity (req/s) — correct USL formula: N*X1/denom
        sat_capacity = base_saturation_rps * n / denom

        # USL scaling efficiency (%)
        eff = (1.0 / denom) * 100.0

        # M/M/c mean Frontend response time at nominal load via Erlang-C
        fe_rt_s = mmc_response_time(S0, lambda_nom, n)
        e2e_ms = fe_rt_s * 1000.0 + backend_ms

        capacities.append(round(sat_capacity, 2))
        efficiencies.append(round(eff, 1))
        system_latencies_ms.append(round(e2e_ms, 1))

    # Optimal scaling point: N* = floor(sqrt((1 - sigma) / kappa))
    n_opt = int(np.sqrt((1.0 - sigma) / kappa)) if kappa > 0 else 99

    usl_data = {
        "model_name": "Neil Gunther Universal Scalability Law (USL)",
        "target_service": "Frontend (Gateway)",
        "parameters": {
            "sigma_contention": sigma,
            "kappa_coherency": kappa,
            "base_saturation_capacity_rps": base_saturation_rps,
            "frontend_service_demand_s": S0,
            "nominal_arrival_rate_rps": lambda_nom,
            "backend_contribution_ms": backend_ms,
            "optimal_replica_limit_N_star": n_opt,
        },
        "sweet_spot_recommendation": {
            "optimal_replicas": 3,
            "usl_efficiency_percent": 93.6,
            "capacity_expansion_factor": 2.82,
            "system_latency_ms_at_10rps": 86.9,
            "system_latency_reduction_percent": 78.5,
        },
        "scaling_sweep": [
            {
                "replicas": n,
                "relative_capacity": round(
                    n / (1.0 + sigma * (n - 1) + kappa * n * (n - 1)), 2
                ),
                "saturation_capacity_rps": capacities[i],
                "efficiency_percent": efficiencies[i],
                "system_response_time_ms": system_latencies_ms[i],
            }
            for i, n in enumerate(replicas)
        ],
    }

    out_file = RESULTS_DIR / "usl_parameters.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(usl_data, f, indent=2)

    print(f"Exported USL parameters and scaling sweep to {out_file}")

    # Print summary table for quick verification against report Table 8
    print(
        f"\n{'c':>4}  {'Capacity (req/s)':>18}  {'eta (%)':>8}  "
        f"{'System RT @ 10 rps (ms)':>24}"
    )
    print("-" * 62)
    for i, n in enumerate(replicas):
        print(
            f"{n:>4}  {capacities[i]:>18.2f}  {efficiencies[i]:>8.1f}  "
            f"{system_latencies_ms[i]:>24.1f}"
        )

    return usl_data


if __name__ == "__main__":
    compute_usl_profile()
