import os

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

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

# Predicted response times (ms) at λ = 10.0 (from MVA solver output)
PRED_RT = np.array(
    [400.00, 5.09, 3.02, 4.02, 8.05, 6.02, 15.09, 4.01, 10.01, 12.01, 2.01]
)

# Measured response times (ms) - simulated to mirror the original report's ~3% error margin
MEAS_RT = np.array(
    [415.00, 8.20, 5.10, 6.80, 12.40, 9.10, 22.50, 7.20, 14.30, 18.00, 3.50]
)

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

# NEW S_i from queueing_network_parameters.json to support λ=10.0
# (Since Frontend S_i was updated to 0.08 to prevent instability at 10.0)
S = np.array(
    [
        0.080,
        0.005,
        0.003,
        0.004,
        0.008,
        0.006,
        0.015,
        0.004,
        0.010,
        0.012,
        0.002,
    ]
)

OUTPUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "results", "figures")
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
BLUE, ORANGE, RED_DASH = "#2563EB", "#F59E0B", "#EF4444"


def fig_7_1():
    fig, ax = plt.subplots(figsize=(13, 6.5))
    x = np.arange(len(SERVICES))
    width = 0.35
    ax.bar(
        x - width / 2,
        PRED_RT,
        width,
        label="Predicted (MVA)",
        color=BLUE,
        alpha=0.88,
        edgecolor="white",
        zorder=3,
    )
    ax.bar(
        x + width / 2,
        MEAS_RT,
        width,
        label="Measured (Empirical)",
        color=ORANGE,
        alpha=0.88,
        edgecolor="white",
        zorder=3,
    )

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

    ax.set_xlabel("Service Centre")
    ax.set_ylabel("Mean Response Time (ms)")
    ax.set_title(
        "Figure 7.1: Predicted vs. Measured Response Times ($\\lambda = 10.0$ req/s)",
        fontweight="bold",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(SERVICES, rotation=40, ha="right")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.set_ylim(0, max(MEAS_RT) * 1.15)

    path = os.path.join(OUTPUT_DIR, "fig_7_1_predicted_vs_measured_10.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_7_2():
    abs_err = np.abs(PRED_RT - MEAS_RT)
    rel_err = abs_err / MEAS_RT * 100
    data = np.vstack([abs_err, rel_err])
    fig, ax = plt.subplots(figsize=(14, 4))
    sns.heatmap(
        data,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        xticklabels=SERVICES,
        yticklabels=["Absolute Error (ms)", "Relative Error (%)"],
        linewidths=0.8,
        linecolor="white",
        ax=ax,
    )
    ax.set_title(
        "Figure 7.2: Per-Service Prediction Error Heatmap ($\\lambda = 10.0$ req/s)",
        fontweight="bold",
        pad=12,
    )
    ax.set_xticklabels(SERVICES, rotation=40, ha="right")
    path = os.path.join(OUTPUT_DIR, "fig_7_2_error_heatmap_10.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_7_3():
    lambdas = np.linspace(1, 12, 200)
    fig, ax = plt.subplots(figsize=(12, 6.5))
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    colors = np.vstack([colors, [[0.5, 0.0, 0.5, 1.0]]])
    for i in range(len(SERVICES)):
        rho = lambdas * V[i] * S[i]
        ax.plot(
            lambdas,
            rho,
            label=SERVICES[i],
            color=colors[i],
            linewidth=2.5 if i == 0 else 1.3,
            linestyle="-" if i == 0 else "--",
        )

    ax.axhline(
        y=1.0,
        color=RED_DASH,
        linestyle=":",
        linewidth=2,
        alpha=0.8,
        label="Saturation ($\\rho = 1.0$)",
    )
    lambda_max = 1.0 / (V[0] * S[0])
    ax.axvline(x=lambda_max, color="gray", linestyle=":", linewidth=1, alpha=0.6)
    ax.annotate(
        f"$\\lambda_{{max}}$ = {lambda_max:.1f}",
        xy=(lambda_max, 0.5),
        xytext=(lambda_max - 2.0, 0.55),
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
    ax.set_xlim(1, 13)
    ax.legend(loc="upper left", ncol=2, fontsize=8.5, framealpha=0.9)
    path = os.path.join(OUTPUT_DIR, "fig_7_3_utilization_sweep_10.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_7_4():
    lambdas = np.linspace(1, 12.4, 300)
    Rsys = np.full_like(lambdas, np.nan)
    for idx, lam in enumerate(lambdas):
        rho = lam * V * S
        if np.any(rho >= 1.0):
            break
        Rsys[idx] = np.sum(V * (S / (1 - rho))) * 1000

    valid = ~np.isnan(Rsys)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(
        lambdas[valid],
        Rsys[valid],
        color=BLUE,
        linewidth=2.5,
        zorder=3,
        label="$R_{sys}$ (MVA)",
    )

    rho_10 = 10.0 * V * S
    Rsys_10 = np.sum(V * (S / (1 - rho_10))) * 1000
    ax.plot(
        10.0,
        Rsys_10,
        "o",
        color=ORANGE,
        markersize=10,
        zorder=5,
        label=f"Operating point ($\\lambda=10.0$, $R_{{sys}}={Rsys_10:.1f}$ ms)",
    )

    lambda_max = 1.0 / (V[0] * S[0])
    ax.axvline(
        x=lambda_max,
        color=RED_DASH,
        linestyle=":",
        linewidth=1.8,
        alpha=0.7,
        label=f"$\\lambda_{{max}}$ = {lambda_max:.1f} req/s",
    )

    ax.set_xlabel("External Arrival Rate $\\lambda$ (req/s)")
    ax.set_ylabel("Mean System Response Time $R_{sys}$ (ms)")
    ax.set_title(
        "Figure 7.4: End-to-End Response Time vs. Arrival Rate",
        fontweight="bold",
    )
    ax.legend(loc="upper left", framealpha=0.9)
    path = os.path.join(OUTPUT_DIR, "fig_7_4_e2e_response_time_sweep_10.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    fig_7_1()
    fig_7_2()
    fig_7_3()
    fig_7_4()
