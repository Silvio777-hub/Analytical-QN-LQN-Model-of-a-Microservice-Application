"""
Google Online Boutique - Queueing Network Model

Defines the Open Queueing Network model for the Google Online Boutique
microservice application, mapping each microservice to a service centre
and defining routing probabilities.

Architecture (11 services):
  Frontend → ProductCatalog, Currency, Cart, Recommendation, Ad, Checkout,
             Shipping
  Checkout → ProductCatalog, Currency, Cart, Shipping, Payment, Email
  Recommendation → ProductCatalog
  CartService → Redis

Service demands and routing probabilities can be:
  1. Estimated from Online Boutique source code and documentation (default)
  2. Loaded from empirical data collected via Prometheus/Jaeger

Usage:
  python queueing_network.py                        # Run with default parameters
  python queueing_network.py --data data/processed   # Use empirical data
  python queueing_network.py --sweep                 # Sweep arrival rates
"""

import argparse
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mva_solver import ServiceCentre, OpenNetworkMVASolver


# ─── Service Index Mapping ─────────────────────────────────────────────────
# Each microservice in Online Boutique maps to a service centre index
SERVICE_NAMES = [
    "Frontend",              # 0
    "ProductCatalogService", # 1
    "CurrencyService",       # 2
    "CartService",           # 3
    "RecommendationService", # 4
    "AdService",             # 5
    "CheckoutService",       # 6
    "ShippingService",       # 7
    "PaymentService",        # 8
    "EmailService",          # 9
    "Redis",                 # 10
]

K = len(SERVICE_NAMES)  # 11 service centres


def get_default_service_times() -> list[float]:
    """
    Default mean service times (in seconds) estimated from
    Online Boutique source code and typical values.

    These are the intrinsic processing times at each service
    (excluding queueing delays).
    """
    return [
        0.116,   # Frontend             - HTTP handler + template render + fan-out
        0.005,   # ProductCatalogService - JSON product lookup
        0.003,   # CurrencyService       - floating-point conversion
        0.004,   # CartService           - Redis get/put wrapper
        0.008,   # RecommendationService - collaborative-filter logic
        0.006,   # AdService             - context-based ad lookup
        0.015,   # CheckoutService       - multi-step orchestration
        0.004,   # ShippingService       - rate calculation
        0.010,   # PaymentService        - mock credit card charge
        0.012,   # EmailService          - SMTP rendering (mock)
        0.002,   # Redis                 - in-memory key-value
    ]


def get_default_routing_matrix() -> np.ndarray:
    """
    Default routing matrix based on Online Boutique request flow (11 services).

    The routing is derived from analyzing the application's source code
    and the typical user journey:
      1. User browses homepage → Frontend fans out to ProductCatalog,
         Currency, Recommendation, Ad, Checkout, Shipping
      2. User views product   → Frontend calls ProductCatalog, Currency
      3. User adds to cart    → Frontend calls Cart → Redis
      4. User checks out      → Frontend calls Checkout, which orchestrates
         calls to ProductCatalog, Currency, Cart, Shipping, Payment,
         Email
      5. No Auth or Notification services in this model


    Routing probabilities represent the fraction of requests leaving
    service i that go to service j. Remaining probability exits the system.
    Row sums must be < 1 (remainder exits the network).

    11-node index map:
      0  Frontend
      1  ProductCatalogService
      2  CurrencyService
      3  CartService
      4  RecommendationService
      5  AdService
      6  CheckoutService
      7  ShippingService
      8  PaymentService
      9  EmailService
      10 Redis
    """
    P = np.zeros((K, K))

    # ── Frontend (0) ──────────────────────────────────────────────────────────
    # Page-mix: browse(35%), product-detail(20%), cart(13%),
    #           checkout(4%), shipping-estimate(4%), ads(5%)
    P[0][1]  = 0.30   # → ProductCatalogService  (browse + product pages)
    P[0][2]  = 0.18   # → CurrencyService         (price display)
    P[0][3]  = 0.13   # → CartService             (cart operations)
    P[0][4]  = 0.08   # → RecommendationService   (homepage widgets)
    P[0][5]  = 0.05   # → AdService               (banner ads)
    P[0][6]  = 0.04   # → CheckoutService         (checkout page)
    P[0][7]  = 0.04   # → ShippingService         (cart shipping estimate)
    # Remaining 0.18 exits (search, auth, static assets, etc.)

    # ── CartService (3) → Redis ───────────────────────────────────────────────
    P[3][10] = 0.95   # Almost all cart ops touch Redis for state

    # ── RecommendationService (4) → ProductCatalogService ────────────────────
    P[4][1] = 0.80    # Fetches product list to filter recommendations

    # ── CheckoutService (6) – multi-step orchestration ────────────────────────
    # Row sum = 0.13*4 + 0.18 + 0.13 = 0.78  (exits with order response)
    P[6][1]  = 0.13   # → ProductCatalogService  (fetch item details)
    P[6][2]  = 0.13   # → CurrencyService         (convert totals)
    P[6][3]  = 0.13   # → CartService             (read + empty cart)
    P[6][7]  = 0.13   # → ShippingService         (final shipping cost)
    P[6][8]  = 0.18   # → PaymentService          (charge card)
    P[6][9]  = 0.13   # → EmailService            (order confirmation)
    # No notification service in 11‑service model

    # Terminal services (respond without further internal routing)
    # ProductCatalogService (1), CurrencyService (2), AdService (5),
    # ShippingService (7), PaymentService (8), EmailService (9), Redis (10)

    return P


def get_default_external_arrivals(arrival_rate: float = 10.0) -> np.ndarray:
    """
    External arrival rates. Only the Frontend receives external requests.

    Args:
        arrival_rate: Total external arrival rate in requests/second.
    """
    ext = np.zeros(K)
    ext[0] = arrival_rate  # All external traffic enters via Frontend
    return ext


def load_empirical_data(data_dir: str) -> tuple:
    """
    Load empirical data from CSV/JSON files collected by data_collection scripts.

    Expected files:
      - service_times.json: {"service_name": mean_service_time, ...}
      - routing_probabilities.json: {"from_service": {"to_service": prob, ...}, ...}

    Returns:
        Tuple of (service_times, routing_matrix)
    """
    st_file = os.path.join(data_dir, "service_times.json")
    rp_file = os.path.join(data_dir, "routing_probabilities.json")

    # Load service times
    with open(st_file, 'r') as f:
        st_data = json.load(f)

    service_times = []
    for name in SERVICE_NAMES:
        if name in st_data:
            service_times.append(st_data[name])
        else:
            print(f"  Warning: No data for {name}, using default")
            defaults = get_default_service_times()
            service_times.append(defaults[SERVICE_NAMES.index(name)])

    # Load routing probabilities
    with open(rp_file, 'r') as f:
        rp_data = json.load(f)

    routing = np.zeros((K, K))
    for from_svc, destinations in rp_data.items():
        if from_svc in SERVICE_NAMES:
            i = SERVICE_NAMES.index(from_svc)
            for to_svc, prob in destinations.items():
                if to_svc in SERVICE_NAMES:
                    j = SERVICE_NAMES.index(to_svc)
                    routing[i][j] = prob

    return service_times, routing


def build_model(service_times: list[float], routing_matrix: np.ndarray,
                arrival_rate: float = 10.0, replicas: dict[str, int] | None = None) -> OpenNetworkMVASolver:
    """Build and return the MVA solver for the Online Boutique model."""
    replicas = replicas or {}
    if replicas:
        print(f"  [Model] Using replica counts: {replicas}")

    centres = []
    for i in range(K):
        name = SERVICE_NAMES[i]
        num_servers = 1
        
        # Check replica override (handling case/suffix variations)
        if name in replicas:
            num_servers = int(replicas[name])
        else:
            for rk, rv in replicas.items():
                rk_clean = rk.lower().replace("service", "")
                name_clean = name.lower().replace("service", "")
                if rk_clean == name_clean or rk_clean in name_clean or name_clean in rk_clean:
                    num_servers = int(rv)
                    break
                    
        centres.append(ServiceCentre(name=name, service_time=service_times[i], num_servers=num_servers))

    external = get_default_external_arrivals(arrival_rate)

    return OpenNetworkMVASolver(centres, routing_matrix, external)


def run_analysis(service_times=None, routing_matrix=None, arrival_rate=10.0, replicas=None):
    """Run the QN model analysis and print results."""
    if service_times is None:
        service_times = get_default_service_times()
    if routing_matrix is None:
        routing_matrix = get_default_routing_matrix()

    print("=" * 60)
    print("ONLINE BOUTIQUE - QN MODEL ANALYSIS")
    print("=" * 60)
    print(f"\nExternal arrival rate: {arrival_rate} req/s")
    print(f"Number of service centres: {K}")
    print()

    # Print service times
    print("Service Demands (mean service times):")
    for i, name in enumerate(SERVICE_NAMES):
        print(f"  {name:<25} S = {service_times[i]*1000:.1f} ms")
    print()

    # Build and solve
    solver = build_model(service_times, routing_matrix, arrival_rate, replicas)
    results = solver.solve()

    print(results.summary())
    return results


def sweep_arrival_rates(service_times=None, routing_matrix=None,
                        rates=None, output_dir="results/figures", replicas=None):
    """
    Sweep over different arrival rates to show how performance degrades
    as load increases. Generates plots of utilization and response time.
    """
    if service_times is None:
        service_times = get_default_service_times()
    if routing_matrix is None:
        routing_matrix = get_default_routing_matrix()
    if rates is None:
        rates = np.arange(1, 51, 1)  # 1 to 50 req/s

    print("Sweeping arrival rates from {} to {} req/s...".format(
        rates[0], rates[-1]))

    all_utilizations = []
    all_response_times = []
    system_response_times = []
    valid_rates = []

    for rate in rates:
        try:
            solver = build_model(service_times, routing_matrix, rate, replicas)
            results = solver.solve()
            all_utilizations.append(results.utilizations.copy())
            all_response_times.append(results.mean_response_times.copy() * 1000)
            system_response_times.append(results.system_response_time * 1000)
            valid_rates.append(rate)
        except ValueError:
            # System becomes unstable at this rate
            break

    if not valid_rates:
        print("System is unstable even at the lowest arrival rate!")
        return

    valid_rates = np.array(valid_rates)
    utils = np.array(all_utilizations)
    rts = np.array(all_response_times)
    sys_rts = np.array(system_response_times)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # ─── Plot 1: Utilization vs Arrival Rate ───────────────────────────
    fig, ax = plt.subplots(figsize=(12, 6))
    # Only plot services with non-trivial utilization
    for i in range(K):
        max_util = np.max(utils[:, i])
        if max_util > 0.01:
            ax.plot(valid_rates, utils[:, i], label=SERVICE_NAMES[i], linewidth=2)

    ax.set_xlabel("External Arrival Rate (req/s)", fontsize=12)
    ax.set_ylabel("Utilization (ρ)", fontsize=12)
    ax.set_title("Service Centre Utilization vs. Arrival Rate", fontsize=14)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label="Saturation")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "utilization_vs_arrival_rate.png"), dpi=150)
    print(f"  Saved: {output_dir}/utilization_vs_arrival_rate.png")
    plt.close()

    # ─── Plot 2: Response Time vs Arrival Rate ─────────────────────────
    fig, ax = plt.subplots(figsize=(12, 6))
    for i in range(K):
        max_rt = np.max(rts[:, i])
        if max_rt > 0.1:
            ax.plot(valid_rates, rts[:, i], label=SERVICE_NAMES[i], linewidth=2)

    ax.set_xlabel("External Arrival Rate (req/s)", fontsize=12)
    ax.set_ylabel("Mean Response Time (ms)", fontsize=12)
    ax.set_title("Service Centre Response Time vs. Arrival Rate", fontsize=14)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "response_time_vs_arrival_rate.png"), dpi=150)
    print(f"  Saved: {output_dir}/response_time_vs_arrival_rate.png")
    plt.close()

    # ─── Plot 3: System Response Time ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(valid_rates, sys_rts, 'b-', linewidth=2.5, label="End-to-end response time")
    ax.set_xlabel("External Arrival Rate (req/s)", fontsize=12)
    ax.set_ylabel("Mean System Response Time (ms)", fontsize=12)
    ax.set_title("End-to-End Response Time vs. Arrival Rate", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "system_response_time.png"), dpi=150)
    print(f"  Saved: {output_dir}/system_response_time.png")
    plt.close()

    # Print the bottleneck
    last_utils = utils[-1]
    bottleneck_idx = np.argmax(last_utils)
    print(f"\n  Bottleneck at max load ({valid_rates[-1]} req/s): "
          f"{SERVICE_NAMES[bottleneck_idx]} (util = {last_utils[bottleneck_idx]:.4f})")
    print(f"  Max stable arrival rate: ~{valid_rates[-1]} req/s")


def save_results(results, output_dir="results"):
    """Save model results to JSON for later comparison with empirical data."""
    os.makedirs(output_dir, exist_ok=True)

    data = {
        "service_names": results.service_names,
        "arrival_rates": results.arrival_rates.tolist(),
        "visit_ratios": results.visit_ratios.tolist(),
        "utilizations": results.utilizations.tolist(),
        "mean_response_times_ms": (results.mean_response_times * 1000).tolist(),
        "mean_queue_lengths": results.mean_queue_lengths.tolist(),
        "throughputs": results.throughputs.tolist(),
        "system_throughput": results.system_throughput,
        "system_response_time_ms": results.system_response_time * 1000,
    }

    out_file = os.path.join(output_dir, "model_predictions.json")
    with open(out_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nModel predictions saved to: {out_file}")


def save_parameters(service_names, service_times, routing_matrix, output_dir=None):
    """Save model parameters to JSON for the API server to use."""
    if output_dir is None:
        # Default to scripts/model relative to project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        output_dir = os.path.join(project_root, 'scripts', 'model')
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if routing_matrix is a numpy array
    if hasattr(routing_matrix, 'tolist'):
        routing_list = routing_matrix.tolist()
    else:
        routing_list = routing_matrix
        
    data = {
        "service_names": service_names,
        "service_times": service_times,
        "routing_matrix": routing_list,
        "num_servers": [1] * len(service_names) # default
    }
    
    out_file = os.path.join(output_dir, "queueing_network_parameters.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Model parameters saved to: {out_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Online Boutique Queueing Network Model"
    )
    parser.add_argument("--rate", "--arrival", type=float, default=10.0,
                        help="External arrival rate in req/s (default: 10)")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to empirical data directory")
    parser.add_argument("--sweep", action="store_true",
                        help="Sweep arrival rates and generate plots")
    parser.add_argument("--save", action="store_true",
                        help="Save predictions to results/")
    parser.add_argument("--replicas", type=str, default=None,
                        help="JSON string of per-service replica counts")
    args = parser.parse_args()

    replicas_dict = {}
    if args.replicas:
        try:
            replicas_dict = json.loads(args.replicas)
        except json.JSONDecodeError as e:
            print(f"Error parsing --replicas JSON: {e}")
            sys.exit(1)

    # Load parameters
    if args.data:
        print(f"Loading empirical data from: {args.data}")
        service_times, routing_matrix = load_empirical_data(args.data)
    else:
        print("Using default (estimated) parameters")
        service_times = get_default_service_times()
        routing_matrix = get_default_routing_matrix()

    # Run analysis
    results = run_analysis(service_times, routing_matrix, args.rate, replicas_dict)

    # Save results
    if args.save:
        save_results(results)
        # Also save parameters for API
        save_parameters(SERVICE_NAMES, service_times, routing_matrix)

    # Sweep arrival rates
    if args.sweep:
        print("\n" + "=" * 60)
        print("ARRIVAL RATE SWEEP ANALYSIS")
        print("=" * 60)
        sweep_arrival_rates(service_times, routing_matrix, replicas=replicas_dict)


if __name__ == "__main__":
    main()
