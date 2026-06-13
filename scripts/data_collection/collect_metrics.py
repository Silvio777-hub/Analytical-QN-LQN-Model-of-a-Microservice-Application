"""
Prometheus Metrics Collector for Google Online Boutique

Queries Prometheus HTTP API to collect per-service performance metrics:
  - Request rate (req/s)
  - Mean response time (seconds)
  - CPU and memory utilization

Exports data to CSV and JSON files in data/processed/.

Prerequisites:
  - Prometheus running and scraping Online Boutique services
  - Default Prometheus endpoint: http://localhost:9090

Usage:
  python collect_metrics.py
  python collect_metrics.py --prometheus http://localhost:9090 --duration 300
"""

import argparse
import csv
import json
import os
from datetime import datetime

import requests
import numpy as np


# Default Prometheus URL
PROMETHEUS_URL = "http://localhost:9090"

# Online Boutique service names (as they appear in Prometheus metrics)
SERVICES = [
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

# Map Prometheus service names to model names
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


def query_prometheus(prom_url: str, query: str) -> dict:
    """Execute a PromQL instant query."""
    try:
        resp = requests.get(
            f"{prom_url}/api/v1/query",
            params={"query": query},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error querying Prometheus: {e}")
        return {"status": "error", "data": {"result": []}}


def query_range(prom_url: str, query: str, start: float,
                end: float, step: str = "15s") -> dict:
    """Execute a PromQL range query."""
    try:
        resp = requests.get(
            f"{prom_url}/api/v1/query_range",
            params={
                "query": query,
                "start": str(start),
                "end": str(end),
                "step": step,
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  Error querying Prometheus: {e}")
        return {"status": "error", "data": {"result": []}}


def collect_request_rates(prom_url: str) -> dict:
    """
    Collect per-service request rates using rate of request counters.

    Uses istio/envoy metrics or application-level metrics depending
    on what's available.
    """
    print("Collecting request rates...")
    rates = {}

    # Try different metric names (depends on instrumentation)
    queries = [
        # gRPC metrics (most Online Boutique services use gRPC)
        'sum(rate(grpc_server_handled_total{grpc_service=~".*"}[5m])) by (grpc_service)',
        # HTTP metrics (frontend)
        'sum(rate(http_server_requests_seconds_count[5m])) by (service)',
        # Istio metrics (if using service mesh)
        'sum(rate(istio_requests_total[5m])) by (destination_service_name)',
        # Generic request count
        'sum(rate(request_count_total[5m])) by (service)',
    ]

    for query in queries:
        result = query_prometheus(prom_url, query)
        if result.get("status") == "success":
            for item in result["data"]["result"]:
                # Extract service name from labels
                metric = item["metric"]
                svc_name = (metric.get("grpc_service") or
                           metric.get("service") or
                           metric.get("destination_service_name", ""))
                svc_name = svc_name.lower().replace("hipstershop.", "")

                for known_svc in SERVICES:
                    if known_svc in svc_name:
                        value = float(item["value"][1])
                        if value > 0:
                            rates[known_svc] = value
                            break

    for svc in SERVICES:
        if svc not in rates:
            rates[svc] = 0.0
            print(f"  Warning: No rate data for {svc}")
        else:
            print(f"  {svc}: {rates[svc]:.3f} req/s")

    return rates


def collect_response_times(prom_url: str) -> dict:
    """
    Collect per-service mean response times.
    Uses histogram metrics (response time buckets).
    """
    print("Collecting response times...")
    times = {}

    queries = [
        # gRPC latency
        ('sum(rate(grpc_server_handling_seconds_sum[5m])) by (grpc_service) / '
         'sum(rate(grpc_server_handling_seconds_count[5m])) by (grpc_service)'),
        # HTTP latency
        ('sum(rate(http_server_requests_seconds_sum[5m])) by (service) / '
         'sum(rate(http_server_requests_seconds_count[5m])) by (service)'),
        # Istio latency
        ('sum(rate(istio_request_duration_milliseconds_sum[5m])) by (destination_service_name) / '
         'sum(rate(istio_request_duration_milliseconds_count[5m])) by (destination_service_name) / 1000'),
    ]

    for query in queries:
        result = query_prometheus(prom_url, query)
        if result.get("status") == "success":
            for item in result["data"]["result"]:
                metric = item["metric"]
                svc_name = (metric.get("grpc_service") or
                           metric.get("service") or
                           metric.get("destination_service_name", ""))
                svc_name = svc_name.lower().replace("hipstershop.", "")

                for known_svc in SERVICES:
                    if known_svc in svc_name:
                        value = float(item["value"][1])
                        if value > 0 and not np.isnan(value):
                            times[known_svc] = value
                            break

    for svc in SERVICES:
        if svc not in times:
            times[svc] = 0.0
            print(f"  Warning: No latency data for {svc}")
        else:
            print(f"  {svc}: {times[svc]*1000:.2f} ms")

    return times


def fetch_container_mappings(jaeger_url: str) -> dict:
    """
    Fetch container ID to service name mappings from Jaeger trace metadata.
    This helps resolve container names when cAdvisor only exports container hashes on Windows.
    """
    print("Fetching container mappings from Jaeger...")
    mapping = {}
    try:
        # Fetch a few traces for each service to extract their container IDs
        for svc in SERVICES:
            try:
                resp = requests.get(
                    f"{jaeger_url}/api/traces",
                    params={"service": svc, "limit": "5", "lookback": "1h"},
                    timeout=2  # Short timeout for local Jaeger checks
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for trace in data.get("data", []):
                        processes = trace.get("processes", {})
                        for proc in processes.values():
                            svc_name = proc.get("serviceName", "").lower()
                            for tag in proc.get("tags", []):
                                if tag.get("key") == "container.id":
                                    container_id = tag.get("value", "")
                                    if container_id:
                                        mapping[container_id.lower()] = svc_name
                                        if len(container_id) > 12:
                                            mapping[container_id[:12].lower()] = svc_name
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                print(f"  Warning: Cannot connect to Jaeger endpoint {jaeger_url}. Skipping container mapping.")
                break
    except Exception as e:
        print(f"  Warning: Could not fetch container mappings from Jaeger: {e}")
    return mapping


def collect_utilization(prom_url: str, container_mappings: dict | None = None) -> dict:
    """Collect CPU utilization per service."""
    print("Collecting CPU utilization...")
    utils: dict[str, float] = {}
    if container_mappings is None:
        container_mappings = {}

    # Try CPU quota query first
    query_quota = ('sum(rate(container_cpu_usage_seconds_total[5m])) by (container, id, name) / '
                   'sum(container_spec_cpu_quota / container_spec_cpu_period) by (container, id, name)')
    
    # Fallback query if CPU quota/limit is not set
    query_raw = 'sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (container, id, name)'

    result = query_prometheus(prom_url, query_quota)
    if result.get("status") != "success" or not result.get("data", {}).get("result"):
        print("  Quota query returned no data, falling back to raw CPU usage...")
        result = query_prometheus(prom_url, query_raw)

    if result.get("status") == "success":
        for item in result["data"]["result"]:
            metric = item["metric"]
            container = metric.get("container", "").lower()
            container_id = metric.get("id", "").lower()
            container_name = metric.get("name", "").lower()
            val = float(item["value"][1])
            
            if np.isnan(val):
                continue

            matched_svc = None
            
            # Match by container name or spec name directly
            for known_svc in SERVICES:
                if known_svc in container or known_svc in container_name:
                    matched_svc = known_svc
                    break
            
            # Match by Jaeger container mapping fallback
            if not matched_svc:
                for cid, svc_name in container_mappings.items():
                    if cid in container_id or cid in container or cid in container_name:
                        matched_svc = svc_name
                        break
                        
            if matched_svc:
                utils[matched_svc] = utils.get(matched_svc, 0.0) + val

    for svc in SERVICES:
        if svc not in utils:
            utils[svc] = 0.0
        else:
            print(f"  {svc}: {utils[svc]*100:.1f}%")

    return utils


def save_metrics(rates, times, utils, output_dir="data/processed"):
    """Save collected metrics to files."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Check if we have any valid non-zero metrics
    has_valid_times = any(v > 0 for v in times.values())
    has_valid_rates = any(v > 0 for v in rates.values())
    has_valid_utils = any(v > 0 for v in utils.values())

    if not (has_valid_times or has_valid_rates or has_valid_utils):
        raise RuntimeError("All collected metrics are zero. Prometheus/Jaeger appear to be offline or returning empty data.")

    service_times_file = os.path.join(output_dir, "service_times.json")
    
    if has_valid_times:
        service_times = {}
        for svc in SERVICES:
            model_name = SERVICE_NAME_MAP.get(svc, svc)
            service_times[model_name] = times.get(svc, 0.0)

        with open(service_times_file, 'w') as f:
            json.dump(service_times, f, indent=2)
        print(f"\nModel input service times updated: {service_times_file}")
    else:
        print(f"\nWarning: No non-zero service times collected. Preserving existing '{service_times_file}'.")

    # Save as CSV (for analysis)
    csv_file = os.path.join(output_dir, f"metrics_{timestamp}.csv")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["service", "request_rate", "mean_response_time_s",
                         "cpu_utilization"])
        for svc in SERVICES:
            writer.writerow([
                SERVICE_NAME_MAP.get(svc, svc),
                rates.get(svc, 0.0),
                times.get(svc, 0.0),
                utils.get(svc, 0.0),
            ])

    # Save all raw data as JSON
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    raw_dir = os.path.join(project_root, "data", "raw")
    raw_file = os.path.join(raw_dir, f"prometheus_data_{timestamp}.json")
    os.makedirs(raw_dir, exist_ok=True)
    with open(raw_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "request_rates": {SERVICE_NAME_MAP.get(k, k): v for k, v in rates.items()},
            "response_times": {SERVICE_NAME_MAP.get(k, k): v for k, v in times.items()},
            "cpu_utilization": {SERVICE_NAME_MAP.get(k, k): v for k, v in utils.items()},
        }, f, indent=2)

    print("Saved metrics log:")
    print(f"  {csv_file}")
    print(f"  {raw_file}")


def main():
    parser = argparse.ArgumentParser(description="Collect metrics from Prometheus")
    parser.add_argument("--prometheus", type=str, default=PROMETHEUS_URL,
                        help="Prometheus URL (default: http://localhost:9090)")
    parser.add_argument("--jaeger", type=str, default="http://localhost:16686",
                        help="Jaeger Query URL (default: http://localhost:16686)")
    parser.add_argument("--output", type=str, default="data/processed",
                        help="Output directory (default: data/processed)")
    args = parser.parse_args()

    print("=" * 60)
    print("PROMETHEUS METRICS COLLECTOR")
    print(f"Prometheus URL: {args.prometheus}")
    print(f"Jaeger URL:     {args.jaeger}")
    print("=" * 60)
    print()

    # Fetch container mapping from Jaeger to resolve container hashes
    container_mappings = fetch_container_mappings(args.jaeger)
    print()

    rates = collect_request_rates(args.prometheus)
    print()
    times = collect_response_times(args.prometheus)
    print()
    utils = collect_utilization(args.prometheus, container_mappings)
    print()

    save_metrics(rates, times, utils, args.output)
    print("\nDone! Use these files as input to the QN model:")
    print("  python scripts/model/queueing_network.py --data data/processed")


if __name__ == "__main__":
    main()
