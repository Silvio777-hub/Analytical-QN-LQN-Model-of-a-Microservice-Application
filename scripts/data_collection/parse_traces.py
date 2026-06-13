"""
Jaeger Trace Parser for Google Online Boutique

Extracts routing probabilities and service dependency graphs from
distributed traces collected by Jaeger/OpenTelemetry.

For each trace, the parser walks the span tree to determine:
  - Which service calls which other services
  - How many times each call happens
  - Routing probabilities (fraction of calls from A→B out of all calls from A)
  - Per-service processing times (exclusive of child spans)

Prerequisites:
  - Jaeger running and collecting traces from Online Boutique
  - Default Jaeger Query endpoint: http://localhost:16686

Usage:
  python parse_traces.py
  python parse_traces.py --jaeger http://localhost:16686 --limit 1000
"""

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime

import requests
import numpy as np


JAEGER_URL = "http://localhost:16686"

# Service names as they appear in Jaeger
ONLINE_BOUTIQUE_SERVICES = [
    "frontend",
    "productcatalogservice",
    "currencyservice",
    "cartservice",
    "recommendationservice",
    "adservice",
    "checkoutservice",
    "shippingservice",
    "paymentservice",
    "emailservice",
]

# Map to model names
SERVICE_NAME_MAP = {
    "frontend": "Frontend",
    "productcatalogservice": "ProductCatalogService",
    "currencyservice": "CurrencyService",
    "cartservice": "CartService",
    "recommendationservice": "RecommendationService",
    "adservice": "AdService",
    "checkoutservice": "CheckoutService",
    "shippingservice": "ShippingService",
    "paymentservice": "PaymentService",
    "emailservice": "EmailService",
}


def fetch_services(jaeger_url: str) -> list:
    """Fetch list of services from Jaeger."""
    try:
        resp = requests.get(f"{jaeger_url}/api/services", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching services: {e}")
        return []


def fetch_traces(jaeger_url: str, service: str, limit: int = 500) -> list:
    """Fetch traces for a specific service from Jaeger."""
    try:
        resp = requests.get(
            f"{jaeger_url}/api/traces",
            params={
                "service": service,
                "limit": str(limit),
                "lookback": "1h",
            },
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching traces for {service}: {e}")
        return []


def parse_trace(trace: dict) -> tuple:
    """
    Parse a single Jaeger trace to extract service calls and exclusive durations.

    Returns:
        edges: list of (parent_service, child_service) tuples
        durations: dict of {service: [duration_s, ...]}
    """
    spans = trace.get("spans", [])
    processes = trace.get("processes", {})

    # Build span lookup
    span_lookup = {}
    for span in spans:
        span_id = span["spanID"]
        process_id = span["processID"]
        service_name = processes.get(process_id, {}).get("serviceName", "unknown")
        duration_us = span["duration"]  # microseconds
        start_time_us = span["startTime"]  # microseconds
        span_lookup[span_id] = {
            "service": service_name.lower(),
            "duration_us": duration_us,
            "start_time_us": start_time_us,
            "end_time_us": start_time_us + duration_us,
            "refs": span.get("references", []),
            "child_intervals": []
        }

    edges = []

    # Find parent spans to determine edges and populate child intervals
    for span_id, span_info in span_lookup.items():
        service = span_info["service"]

        for ref in span_info["refs"]:
            if ref["refType"] == "CHILD_OF":
                parent_id = ref["spanID"]
                if parent_id in span_lookup:
                    parent_info = span_lookup[parent_id]
                    parent_service = parent_info["service"]
                    if parent_service != service:  # Ignore same-service spans
                        edges.append((parent_service, service))

                    # Clip child interval to parent boundary to handle potential clock skews
                    child_start = max(parent_info["start_time_us"], span_info["start_time_us"])
                    child_end = min(parent_info["end_time_us"], span_info["end_time_us"])
                    if child_start < child_end:
                        parent_info["child_intervals"].append((child_start, child_end))

    # Calculate exclusive durations
    durations = defaultdict(list)
    for span_id, span_info in span_lookup.items():
        service = span_info["service"]

        # Merge overlapping child intervals to find total waiting time
        child_intervals = span_info["child_intervals"]
        waiting_time_us = 0
        if child_intervals:
            sorted_intervals = sorted(child_intervals, key=lambda x: x[0])
            merged = [sorted_intervals[0]]
            for current in sorted_intervals[1:]:
                prev_start, prev_end = merged[-1]
                curr_start, curr_end = current
                if curr_start <= prev_end:
                    merged[-1] = (prev_start, max(prev_end, curr_end))
                else:
                    merged.append(current)
            waiting_time_us = sum(end - start for start, end in merged)

        exclusive_duration_us = max(0, span_info["duration_us"] - waiting_time_us)
        durations[service].append(exclusive_duration_us / 1_000_000)  # → seconds

    return edges, durations


def compute_routing_probabilities(all_edges: list) -> dict:
    """
    Compute routing probabilities from observed edges.

    P[from][to] = count(from→to) / count(all edges from 'from')
    """
    # Count edge occurrences
    edge_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    from_totals: dict[str, int] = defaultdict(int)

    for parent, child in all_edges:
        edge_counts[parent][child] += 1
        from_totals[parent] += 1

    # Compute probabilities
    routing: dict[str, dict[str, float]] = {}
    for from_svc, destinations in edge_counts.items():
        model_from = SERVICE_NAME_MAP.get(from_svc, from_svc)
        routing[model_from] = {}
        total = from_totals[from_svc]
        for to_svc, count in destinations.items():
            model_to = SERVICE_NAME_MAP.get(to_svc, to_svc)
            routing[model_from][model_to] = round(count / total, 4)

    return routing


def compute_service_demands(all_durations: dict) -> dict:
    """Compute mean service demands from observed span durations."""
    demands = {}
    for svc, durations in all_durations.items():
        model_name = SERVICE_NAME_MAP.get(svc, svc)
        if durations:
            demands[model_name] = {
                "mean_service_time": float(np.mean(durations)),
                "median_service_time": float(np.median(durations)),
                "p95_service_time": float(np.percentile(durations, 95)),
                "p99_service_time": float(np.percentile(durations, 99)),
                "std_service_time": float(np.std(durations)),
                "sample_count": len(durations),
            }
    return demands


def save_results(routing: dict, demands: dict, dep_graph: dict,
                 output_dir: str = "data/processed"):
    if not routing and not demands and not dep_graph:
        print("\nWarning: No trace data parsed. Skipping saving empty results files to prevent clutter.")
        return

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save routing probabilities
    rp_file = os.path.join(output_dir, "routing_probabilities.json")
    with open(rp_file, 'w') as f:
        json.dump(routing, f, indent=2)
    print(f"  Routing probabilities: {rp_file}")

    # Save service demands
    sd_file = os.path.join(output_dir, "service_demands.json")
    with open(sd_file, 'w') as f:
        json.dump(demands, f, indent=2)
    print(f"  Service demands: {sd_file}")

    # Save dependency graph
    dg_file = os.path.join(output_dir, f"dependency_graph_{timestamp}.json")
    with open(dg_file, 'w') as f:
        json.dump(dep_graph, f, indent=2)
    print(f"  Dependency graph: {dg_file}")

    # Also save raw data
    raw_dir = "data/raw"
    os.makedirs(raw_dir, exist_ok=True)
    raw_file = os.path.join(raw_dir, f"trace_data_{timestamp}.json")
    with open(raw_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "routing_probabilities": routing,
            "service_demands": demands,
            "dependency_graph": dep_graph,
        }, f, indent=2)
    print(f"  Raw trace data: {raw_file}")


def print_dependency_graph(routing: dict):
    """Pretty-print the service dependency graph."""
    print("\n  Service Dependency Graph:")
    print("  " + "-" * 50)
    for from_svc, destinations in sorted(routing.items()):
        for to_svc, prob in sorted(destinations.items(), key=lambda x: -x[1]):
            bar = "█" * int(prob * 30)
            print(f"  {from_svc:<25} → {to_svc:<25} {prob:.3f} {bar}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Parse Jaeger traces")
    parser.add_argument("--jaeger", type=str, default=JAEGER_URL,
                        help="Jaeger Query URL (default: http://localhost:16686)")
    parser.add_argument("--limit", type=int, default=500,
                        help="Max traces per service (default: 500)")
    parser.add_argument("--output", type=str, default="data/processed",
                        help="Output directory")
    args = parser.parse_args()

    print("=" * 60)
    print("JAEGER TRACE PARSER")
    print(f"Jaeger URL: {args.jaeger}")
    print(f"Trace limit per service: {args.limit}")
    print("=" * 60)
    print()

    # Fetch available services
    services = fetch_services(args.jaeger)
    if not services:
        print("No services found in Jaeger. Is Jaeger running?")
        print("Make sure Online Boutique is deployed with tracing enabled.")
        return

    print(f"Found {len(services)} services: {', '.join(services)}")
    print()

    # Fetch and parse traces for each service
    all_edges = []
    all_durations = defaultdict(list)
    dep_graph = defaultdict(set)

    for service in ONLINE_BOUTIQUE_SERVICES:
        if service not in [s.lower() for s in services]:
            print(f"  Skipping {service} (not found in Jaeger)")
            continue

        print(f"Fetching traces for {service}...")
        traces = fetch_traces(args.jaeger, service, args.limit)
        print(f"  Got {len(traces)} traces")

        for trace in traces:
            edges, durations = parse_trace(trace)
            all_edges.extend(edges)
            for svc, durs in durations.items():
                all_durations[svc].extend(durs)
            for parent, child in edges:
                dep_graph[parent].add(child)

    # Convert sets to lists for JSON serialization
    dep_graph_serializable = {k: sorted(list(v)) for k, v in dep_graph.items()}

    # Compute routing probabilities
    print("\nComputing routing probabilities...")
    routing = compute_routing_probabilities(all_edges)
    print_dependency_graph(routing)

    # Compute service demands
    print("Computing service demands...")
    demands = compute_service_demands(all_durations)
    for svc, stats in sorted(demands.items()):
        print(f"  {svc:<25} mean={stats['mean_service_time']*1000:.2f}ms  "
              f"p95={stats['p95_service_time']*1000:.2f}ms  "
              f"n={stats['sample_count']}")

    # Save results
    print("\nSaving results...")
    save_results(routing, demands, dep_graph_serializable, args.output)

    print("\nDone! Use these files as input to the QN model:")
    print("  python scripts/model/queueing_network.py --data data/processed")


if __name__ == "__main__":
    main()
