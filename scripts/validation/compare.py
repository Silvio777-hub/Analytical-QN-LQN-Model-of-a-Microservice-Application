"""
Validation Script: Compare QN Model Predictions vs. Empirical Measurements

Loads model predictions (from mva_solver output) and empirical measurements
(from Prometheus/Jaeger), computes error metrics, and generates comparison
plots and tables.

Error Metrics:
  - RMSE (Root Mean Squared Error)
  - MAE (Mean Absolute Error)
  - MAPE (Mean Absolute Percentage Error)

Usage:
  python compare.py
  python compare.py --predictions results/model_predictions.json \
                    --measurements data/processed/metrics_*.csv
"""

import argparse
import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


def load_predictions(filepath: str) -> dict:
    """Load model predictions from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def load_measurements(filepath: str) -> dict:
    """Load empirical measurements from CSV file."""
    measurements = {}
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            service = row["service"]
            measurements[service] = {
                "request_rate": float(row.get("request_rate", 0)),
                "mean_response_time_ms": float(row.get("mean_response_time_s", 0)) * 1000,
                "cpu_utilization": float(row.get("cpu_utilization", 0)),
            }
    return measurements


def compute_errors(predicted: np.ndarray, measured: np.ndarray) -> dict:
    """Compute error metrics between predicted and measured values."""
    errors = predicted - measured
    abs_errors = np.abs(errors)

    rmse = np.sqrt(np.mean(errors ** 2))
    mae = np.mean(abs_errors)

    # MAPE (avoid division by zero)
    nonzero = measured != 0
    if np.any(nonzero):
        mape = np.mean(abs_errors[nonzero] / np.abs(measured[nonzero])) * 100
    else:
        mape = float('inf')

    return {
        "RMSE": rmse,
        "MAE": mae,
        "MAPE_%": mape,
    }


def plot_comparison_bar(services, predicted, measured, metric_name,
                        ylabel, output_path):
    """Generate a side-by-side bar chart comparing predicted vs measured."""
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(services))
    width = 0.35

    ax.bar(x - width/2, predicted, width, label="Model Prediction",
                    color="#2196F3", alpha=0.85, edgecolor="white")
    ax.bar(x + width/2, measured, width, label="Empirical Measurement",
                    color="#FF9800", alpha=0.85, edgecolor="white")

    ax.set_xlabel("Service Centre", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(f"{metric_name}: Model vs. Empirical", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(services, rotation=45, ha="right", fontsize=9)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def plot_scatter(predicted, measured, metric_name, unit, output_path):
    """Generate a scatter plot of predicted vs measured values."""
    fig, ax = plt.subplots(figsize=(8, 8))

    ax.scatter(measured, predicted, s=100, c="#2196F3", edgecolors="white",
               linewidths=1.5, alpha=0.8, zorder=5)

    # Perfect prediction line
    all_vals = np.concatenate([predicted, measured])
    min_val, max_val = np.min(all_vals) * 0.9, np.max(all_vals) * 1.1
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2,
            alpha=0.5, label="Perfect Prediction", zorder=1)

    ax.set_xlabel(f"Measured {metric_name} ({unit})", fontsize=12)
    ax.set_ylabel(f"Predicted {metric_name} ({unit})", fontsize=12)
    ax.set_title(f"Predicted vs. Measured {metric_name}", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def plot_error_heatmap(services, metrics_errors, output_path):
    """Generate a heatmap of per-service error metrics."""
    fig, ax = plt.subplots(figsize=(10, 6))

    error_matrix = []
    metric_labels = []
    for metric_name, per_service_errors in metrics_errors.items():
        metric_labels.append(metric_name)
        row = [per_service_errors.get(svc, 0) for svc in services]
        error_matrix.append(row)

    error_matrix = np.array(error_matrix)

    sns.heatmap(error_matrix, annot=True, fmt='.1f', cmap='YlOrRd',
                xticklabels=services, yticklabels=metric_labels,
                ax=ax, linewidths=0.5, cbar_kws={'label': 'Absolute Error'})

    ax.set_title("Per-Service Prediction Errors", fontsize=14, fontweight="bold")
    ax.set_xticklabels(services, rotation=45, ha="right", fontsize=9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def generate_report(services, pred_data, meas_data, errors, output_dir):
    """Generate a text summary report of the comparison."""
    report_file = os.path.join(output_dir, "comparison_summary.txt")

    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("MODEL VALIDATION REPORT\n")
        f.write("Analytical QN Model vs. Empirical Measurements\n")
        f.write("=" * 80 + "\n\n")

        # Per-service comparison table
        f.write("PER-SERVICE COMPARISON\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Service':<25} {'Pred RT(ms)':>12} {'Meas RT(ms)':>12} "
                f"{'Error(ms)':>12} {'Error(%)':>10}\n")
        f.write("-" * 80 + "\n")

        for svc in services:
            pred_rt = pred_data.get(svc, {}).get("response_time_ms", 0)
            meas_rt = meas_data.get(svc, {}).get("mean_response_time_ms", 0)
            err = pred_rt - meas_rt
            pct = (abs(err) / meas_rt * 100) if meas_rt > 0 else 0
            f.write(f"{svc:<25} {pred_rt:>12.2f} {meas_rt:>12.2f} "
                    f"{err:>12.2f} {pct:>9.1f}%\n")

        f.write("\n")

        # Error summary
        f.write("ERROR METRICS SUMMARY\n")
        f.write("-" * 40 + "\n")
        for metric, value in errors.items():
            f.write(f"  {metric:<15} {value:.4f}\n")

        f.write("\n")
        f.write("=" * 80 + "\n")

    print(f"  Report: {report_file}")


def run_with_sample_data(output_dir="results/figures"):
    """
    Run comparison with sample data to demonstrate the pipeline.
    Use this when empirical data is not yet collected.
    """
    print("Running with SAMPLE DATA for demonstration...")
    print("(Replace with real data from Prometheus/Jaeger)\n")

    services = [
        "Frontend", "ProductCatalogService", "CurrencyService",
        "CartService", "RecommendationService", "AdService",
        "CheckoutService", "ShippingService", "PaymentService",
        "EmailService",
    ]

    # Sample predicted values (from model)
    pred_rt = np.array([15.2, 6.1, 3.5, 5.8, 10.3, 7.2, 22.8, 4.9, 12.1, 14.5])

    # Sample measured values (simulated empirical data with some noise)
    np.random.seed(42)
    meas_rt = pred_rt * (1 + np.random.normal(0, 0.15, len(pred_rt)))
    meas_rt = np.clip(meas_rt, 1.0, None)  # Ensure positive

    # Compute errors
    errors = compute_errors(pred_rt, meas_rt)
    print("Error Metrics (Response Time):")
    for k, v in errors.items():
        print(f"  {k}: {v:.4f}")

    # Generate plots
    os.makedirs(output_dir, exist_ok=True)
    print("\nGenerating comparison plots...")

    plot_comparison_bar(
        services, pred_rt, meas_rt,
        "Mean Response Time", "Response Time (ms)",
        os.path.join(output_dir, "comparison_response_time.png")
    )

    plot_scatter(
        pred_rt, meas_rt,
        "Response Time", "ms",
        os.path.join(output_dir, "scatter_response_time.png")
    )

    # Per-service error for heatmap
    per_svc_errors = {svc: abs(pred_rt[i] - meas_rt[i])
                      for i, svc in enumerate(services)}
    plot_error_heatmap(
        services,
        {"Response Time Error (ms)": per_svc_errors},
        os.path.join(output_dir, "error_heatmap.png")
    )


def main():
    parser = argparse.ArgumentParser(description="Compare model predictions vs. measurements")
    parser.add_argument("--predictions", type=str, default="results/model_predictions.json",
                        help="Path to model predictions JSON")
    parser.add_argument("--measurements", type=str, default=None,
                        help="Path to measurements CSV")
    parser.add_argument("--output", type=str, default="results/figures",
                        help="Output directory for figures")
    parser.add_argument("--demo", action="store_true",
                        help="Run with sample data for demonstration")
    args = parser.parse_args()

    if args.demo:
        run_with_sample_data(args.output)
        return

    # Check if data files exist
    if not os.path.exists(args.predictions):
        print(f"Predictions file not found: {args.predictions}")
        print("Run the model first: python scripts/model/queueing_network.py --save")
        print("Or use --demo flag to run with sample data")
        return

    if args.measurements is None or not os.path.exists(args.measurements):
        print("No measurements file found.")
        print("Collect data first: python scripts/data_collection/collect_metrics.py")
        print("Or use --demo flag to run with sample data")
        return

    # Load data
    print("Loading predictions and measurements...")
    pred_data = load_predictions(args.predictions)
    meas_data = load_measurements(args.measurements)

    services_all = pred_data["service_names"]
    pred_rt_all = np.array(pred_data["mean_response_times_ms"])

    services = []
    pred_rt = []
    meas_rt = []

    for i, svc in enumerate(services_all):
        m_data = meas_data.get(svc)
        if m_data and m_data.get("mean_response_time_ms", 0.0) > 0.0:
            services.append(svc)
            pred_rt.append(pred_rt_all[i])
            meas_rt.append(m_data["mean_response_time_ms"])

    services = np.array(services)
    pred_rt = np.array(pred_rt)
    meas_rt = np.array(meas_rt)

    # Compute errors
    errors = compute_errors(pred_rt, meas_rt)
    print("\nError Metrics (Response Time):")
    for k, v in errors.items():
        print(f"  {k}: {v:.4f}")

    # Generate plots
    os.makedirs(args.output, exist_ok=True)
    print("\nGenerating comparison plots...")

    plot_comparison_bar(services, pred_rt, meas_rt,
                        "Mean Response Time", "Response Time (ms)",
                        os.path.join(args.output, "comparison_response_time.png"))

    plot_scatter(pred_rt, meas_rt, "Response Time", "ms",
                 os.path.join(args.output, "scatter_response_time.png"))

    # Per-service error for heatmap
    per_svc_errors = {svc: abs(pred_rt[i] - meas_rt[i])
                      for i, svc in enumerate(services)}
    plot_error_heatmap(
        services,
        {"Response Time Error (ms)": per_svc_errors},
        os.path.join(args.output, "error_heatmap.png")
    )

    # Generate report
    pred_svc_data = {svc: {"response_time_ms": pred_rt[i]}
                     for i, svc in enumerate(services)}
    generate_report(services, pred_svc_data, meas_data, errors, args.output)


if __name__ == "__main__":
    main()
