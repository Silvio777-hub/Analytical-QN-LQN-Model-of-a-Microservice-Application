"""
Generate Report Figures 7.1 – 7.4
===================================
Uses the EXACT data from the report (Table 2, §7.1) at λ = 5.0 req/s.

Outputs (saved to results/figures/):
  - fig_7_1_predicted_vs_measured.png   (grouped bar chart)
  - fig_7_2_error_heatmap.png           (dual-row heatmap: absolute + relative)
  - fig_7_3_utilization_sweep.png       (utilization vs arrival rate, all 11 services)
  - fig_7_4_e2e_response_time_sweep.png (system response time vs arrival rate)

Usage:
  cd <project_root>
  python scripts/validation/generate_report_figures.py
"""

import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ──────────────────────────────────────────────────────────────────────────────
# DATA — Exact values from the report (Table 2, §7.1, λ = 5.0 req/s)
# ──────────────────────────────────────────────────────────────────────────────

SERVICES = [
    "Frontend",
    "ProductCatalog",
    "Currency",
    "Cart",
    "Recommendation",
    "Ad",
    "Checkout",
    "Shipping",
    "Payment",
    "Email",
    "Redis",
]

# Predicted response times (ms) — from MVA solver (Table 2)
PRED_RT = np.array(
    [276.19, 5.05, 3.01, 4.01, 7.52, 5.89, 14.71, 3.83, 9.56, 11.55, 2.00]
)

# Measured response times (ms) — from Prometheus (Table 2)
MEAS_RT = np.array(
    [285.00, 8.20, 5.10, 6.80, 12.40, 9.10, 22.50, 7.20, 14.30, 18.00, 3.50]
)

# Visit ratios V_i (§5.1)
V = np.array(
    [
        1.000,
        0.370,
        0.184,
        0.150,
        0.080,
        0.050,
        0.040,
        0.048,
        0.012,
        0.008,
        0.150,
    ]
)

# Exclusive service demands S_i in seconds (§4.4)
S = np.array(
    [
        0.11667,
        0.005,
        0.003,
        0.004,
        0.0075,
        0.0058,
        0.0145,
        0.0038,
        0.0095,
        0.0115,
        0.002,
    ]
)

# Internal arrival rates at λ = 5.0 (§5.1)
LAMBDA_I = np.array([5.00, 1.85, 0.92, 0.75, 0.40, 0.25, 0.20, 0.24, 0.06, 0.04, 0.75])

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "figures")

# ──────────────────────────────────────────────────────────────────────────────
# STYLE CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.grid": True,
        "grid.alpha": 0.3,
    }
)

BLUE = "#2563EB"
ORANGE = "#F59E0B"
RED_DASH = "#EF4444"


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 7.1 — Grouped Bar Chart: Predicted vs. Measured Response Times
# ══════════════════════════════════════════════════════════════════════════════


def fig_7_1(output_dir: str):
    fig, ax = plt.subplots(figsize=(13, 6.5))

    x = np.arange(len(SERVICES))
    width = 0.35

    bars_pred = ax.bar(
        x - width / 2,
        PRED_RT,
        width,
        label="Predicted (MVA)",
        color=BLUE,
        alpha=0.88,
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
    )
    bars_meas = ax.bar(
        x + width / 2,
        MEAS_RT,
        width,
        label="Measured (Prometheus)",
        color=ORANGE,
        alpha=0.88,
        edgecolor="white",
        linewidth=0.6,
        zorder=3,
    )

    # Annotate the Frontend bars with their values
    ax.annotate(
        f"{PRED_RT[0]:.1f}",
        xy=(x[0] - width / 2, PRED_RT[0]),
        ha="center",
        va="bottom",
        fontsize=8,
        fontweight="bold",
        color=BLUE,
    )
    ax.annotate(
        f"{MEAS_RT[0]:.1f}",
        xy=(x[0] + width / 2, MEAS_RT[0]),
        ha="center",
        va="bottom",
        fontsize=8,
        fontweight="bold",
        color="#B45309",
    )

    # Add the 95% CI band for Frontend
    ci_low, ci_high = 269.9, 300.1
    ax.axhspan(
        ci_low,
        ci_high,
        xmin=0.0,
        xmax=0.15,
        alpha=0.12,
        color="green",
        label="95% CI [269.9, 300.1] ms",
        zorder=1,
    )

    ax.set_xlabel("Service Centre")
    ax.set_ylabel("Mean Response Time (ms)")
    ax.set_title(
        "Figure 7.1: Predicted vs. Measured Response Times ($\\lambda = 5.0$ req/s)",
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(SERVICES, rotation=40, ha="right")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.set_ylim(0, max(MEAS_RT) * 1.15)

    path = os.path.join(output_dir, "fig_7_1_predicted_vs_measured.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  ✓ Saved {path}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 7.2 — Heatmap: Absolute Error (ms) + Relative Error (%)
# ══════════════════════════════════════════════════════════════════════════════


def fig_7_2(output_dir: str):
    abs_err = np.abs(PRED_RT - MEAS_RT)
    rel_err = abs_err / MEAS_RT * 100

    data = np.vstack([abs_err, rel_err])
    row_labels = ["Absolute Error (ms)", "Relative Error (%)"]

    fig, ax = plt.subplots(figsize=(14, 4))

    sns.heatmap(
        data,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        xticklabels=SERVICES,
        yticklabels=row_labels,
        linewidths=0.8,
        linecolor="white",
        cbar_kws={"label": "Error Magnitude"},
        ax=ax,
    )

    ax.set_title(
        "Figure 7.2: Per-Service Prediction Error Heatmap ($\\lambda = 5.0$ req/s)",
        fontweight="bold",
        pad=12,
    )
    ax.set_xticklabels(SERVICES, rotation=40, ha="right")

    path = os.path.join(output_dir, "fig_7_2_error_heatmap.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  ✓ Saved {path}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 7.3 — Utilization (ρ) vs. External Arrival Rate (all 11 services)
# ══════════════════════════════════════════════════════════════════════════════


def fig_7_3(output_dir: str):
    lambdas = np.linspace(0.5, 8.5, 200)

    fig, ax = plt.subplots(figsize=(12, 6.5))

    # Use a qualitative palette for 11 distinguishable lines
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    colors = np.vstack([colors, [[0.5, 0.0, 0.5, 1.0]]])  # add purple for Redis

    for i in range(len(SERVICES)):
        rho = lambdas * V[i] * S[i]
        lw = 2.5 if i == 0 else 1.3
        ls = "-" if i == 0 else "--"
        ax.plot(
            lambdas,
            rho,
            label=SERVICES[i],
            color=colors[i],
            linewidth=lw,
            linestyle=ls,
        )

    # Saturation threshold
    ax.axhline(
        y=1.0,
        color=RED_DASH,
        linestyle=":",
        linewidth=2,
        alpha=0.8,
        label="Saturation ($\\rho = 1.0$)",
    )

    # Mark theoretical λ_max ≈ 8.57 req/s
    lambda_max = 1.0 / (V[0] * S[0])
    ax.axvline(x=lambda_max, color="gray", linestyle=":", linewidth=1, alpha=0.6)
    ax.annotate(
        f"$\\lambda_{{max}}$ ≈ {lambda_max:.1f}",
        xy=(lambda_max, 0.5),
        xytext=(lambda_max - 1.8, 0.55),
        fontsize=9,
        color="gray",
        arrowprops=dict(arrowstyle="->", color="gray", lw=1),
    )

    ax.set_xlabel("External Arrival Rate $\\lambda$ (req/s)")
    ax.set_ylabel("Utilization $\\rho_i$")
    ax.set_title(
        "Figure 7.3: Service Centre Utilization vs. Arrival Rate",
        fontweight="bold",
    )
    ax.set_ylim(0, 1.1)
    ax.set_xlim(0.5, 8.5)
    ax.legend(loc="upper left", ncol=2, fontsize=8.5, framealpha=0.9)

    path = os.path.join(output_dir, "fig_7_3_utilization_sweep.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  ✓ Saved {path}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 7.4 — End-to-End System Response Time vs. Arrival Rate
# ══════════════════════════════════════════════════════════════════════════════


def fig_7_4(output_dir: str):
    lambdas = np.linspace(0.5, 8.4, 300)
    Rsys = np.full_like(lambdas, np.nan)

    for idx, lam in enumerate(lambdas):
        rho = lam * V * S
        if np.any(rho >= 1.0):
            break  # system unstable beyond this point
        R_i = S / (1 - rho)
        Rsys[idx] = np.sum(V * R_i) * 1000  # convert to ms

    # Trim NaNs
    valid = ~np.isnan(Rsys)
    lam_v = lambdas[valid]
    Rsys_v = Rsys[valid]

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(
        lam_v,
        Rsys_v,
        color=BLUE,
        linewidth=2.5,
        zorder=3,
        label="$R_{sys} = \\sum V_i \\cdot R_i$ (MVA)",
    )

    # Annotate λ = 5.0 operating point
    rho_5 = 5.0 * V * S
    R_5 = S / (1 - rho_5)
    Rsys_5 = np.sum(V * R_5) * 1000
    ax.plot(
        5.0,
        Rsys_5,
        "o",
        color=ORANGE,
        markersize=10,
        zorder=5,
        label=f"Operating point ($\\lambda=5.0$, $R_{{sys}}={Rsys_5:.1f}$ ms)",
    )

    # Mark theoretical λ_max
    lambda_max = 1.0 / (V[0] * S[0])
    ax.axvline(
        x=lambda_max,
        color=RED_DASH,
        linestyle=":",
        linewidth=1.8,
        alpha=0.7,
        label=f"$\\lambda_{{max}}$ ≈ {lambda_max:.1f} req/s",
    )

    # Empirical plateau annotation
    ax.annotate(
        "Empirical plateau at\n~8.9 req/s (timeouts)",
        xy=(8.3, Rsys_v[-1]),
        xytext=(6.5, Rsys_v[-1] * 0.85),
        fontsize=9,
        color="gray",
        fontstyle="italic",
        arrowprops=dict(arrowstyle="->", color="gray", lw=1),
    )

    ax.set_xlabel("External Arrival Rate $\\lambda$ (req/s)")
    ax.set_ylabel("Mean System Response Time $R_{sys}$ (ms)")
    ax.set_title(
        "Figure 7.4: End-to-End Response Time vs. Arrival Rate (Sensitivity Sweep)",
        fontweight="bold",
    )
    ax.legend(loc="upper left", framealpha=0.9)
    ax.set_xlim(0.5, 8.5)

    path = os.path.join(output_dir, "fig_7_4_e2e_response_time_sweep.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  ✓ Saved {path}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    out = os.path.abspath(OUTPUT_DIR)
    os.makedirs(out, exist_ok=True)

    print(f"Generating report figures → {out}\n")
    fig_7_1(out)
    fig_7_2(out)
    fig_7_3(out)
    fig_7_4(out)
    print("\nDone. All 4 figures saved.")
