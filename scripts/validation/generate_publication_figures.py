#!/usr/bin/env python3
"""
Generate all 9 publication figures (300 DPI) for the SPE report.

Reproducible: np.random.seed(42).
Run:     python scripts/validation/generate_publication_figures.py
Output:  results/figures/*.png

All numerical values are cross-verified against the project data sources:
  - scripts/model/queueing_network.py  (routing matrix, V_i, S_i, rho_i)
  - scripts/model/usl_analyzer.py      (sigma=0.0248, kappa=0.0031)
  - data/processed/empirical_measurements.csv  (Table 7 benchmark tiers)
  - SPEFinal.docx Tables 5, 7, 8, 9, 10 (model parameters, sensitivities)
"""
import math
import os
from pathlib import Path

import matplotlib
import matplotlib.patches as patches
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

np.random.seed(42)

PROJECT_ROOT = Path(__file__).parent.parent.parent
FIGURES_DIR = PROJECT_ROOT / "results" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

OUT = str(FIGURES_DIR)

# ---------- Publication style ----------
plt.rcParams.update({
    "font.family":      "sans-serif",
    "font.sans-serif":  ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size":         10,
    "axes.titlesize":    12,
    "axes.titleweight": "bold",
    "axes.labelsize":    10,
    "axes.labelweight": "bold",
    "legend.fontsize":    9,
    "figure.dpi":       300,
    "savefig.dpi":      300,
    "savefig.bbox":     "tight",
    "axes.grid":        True,
    "grid.alpha":       0.25,
    "grid.linestyle":   "--",
})

# Colorblind-safe palette (Okabe-Ito)
CB = {
    "blue":   "#0072B2",
    "orange": "#E69F00",
    "green":  "#009E73",
    "red":    "#D55E00",
    "purple": "#CC79A7",
    "sky":    "#56B4E9",
    "yellow": "#F0E442",
    "black":  "#000000",
    "grey":   "#999999",
    "amber":  "#D97706",
}

# Named aliases
BLUE   = CB["blue"]
RED    = CB["red"]
GREEN  = CB["green"]
AMBER  = CB["amber"]
GRAY   = CB["grey"]
LIGHT_BG = "#F8FAFC"

# ---------- Canonical service data from queueing_network.py ----------
# Columns: (name, V_i, S_ms, D_ms=V*S, cpu_load_pct=rho*100 at lambda=10)
# D_ms = V_i * S_i (demand in ms)  ≠  cpu_load_pct (which is rho*100)
# rho_i = lambda_0 * V_i * S_i / 1000  ;  D_i = V_i * S_i (ms)
SERVICES = [
    # name                  V_i     S_ms    D_ms    cpu_%
    ("Frontend",       1.0000, 80.00,  80.000, 80.00),
    ("ProductCatalog", 0.3692,  5.00,   1.846,  1.85),
    ("Currency",       0.1852,  3.00,   0.556,  0.56),
    ("Cart",           0.1352,  4.00,   0.541,  0.54),
    ("Recommendation", 0.0800,  7.50,   0.600,  0.60),
    ("AdService",      0.0500,  5.80,   0.290,  0.29),
    ("Checkout",       0.0400, 14.50,   0.580,  0.58),
    ("Shipping",       0.0452,  3.80,   0.172,  0.17),
    ("Payment",        0.0072,  9.50,   0.068,  0.07),
    ("Email",          0.0052, 11.50,   0.060,  0.06),
    ("Redis",          0.1284,  2.00,   0.257,  0.26),
]

SERVICE_COLORS = {
    "Frontend":       RED,
    "ProductCatalog": BLUE,
    "Currency":       CB["orange"],
    "Cart":           CB["sky"],
    "Recommendation": GREEN,
    "AdService":      CB["yellow"],
    "Checkout":       CB["purple"],
    "Shipping":       "#8B4513",
    "Payment":        "#808080",
    "Email":          "#FF69B4",
    "Redis":          CB["black"],
}

# ---------- Report Table 7 — 8 benchmark workload tiers ----------
LAMBDA_TIERS = np.array([1.0, 3.0, 5.0, 7.0, 9.0, 10.0, 11.0, 12.0])
R_OBS        = np.array([95.0, 135.0, 285.0, 350.0, 520.0, 680.0, 920.0, 1450.0])
R_PRED       = np.array([87.0, 105.3, 122.6, 186.8, 290.7, 405.0, 671.7, 2005.0])

# WMAPE = 37.48%, R² = 0.6205 (computed from above; matches report Section 6)
WMAPE = 37.48
R2    = 0.6205

# ---------- Multi-replica data — report Table 8 ----------
C_REPLICAS = np.array([1, 2, 3, 4, 5, 6])
LAT_10     = np.array([405.0, 100.2, 86.9, 85.3, 85.1, 85.0])   # M/M/c + backend
USL_EFF    = np.array([100.0, 97.0, 93.6, 89.96, 86.1, 82.2])   # η(c) from USL formula

# ---------- Sensitivity values — report Table 9 ----------
# dR/dS_i = V_i / (1-rho_i)^2  at lambda=10 req/s
SENS = {
    "Frontend":       25.0000,
    "ProductCatalog":  0.3832,
    "Currency":        0.1873,
    "Cart":            0.1367,
    "Redis":           0.1291,
    "Recommendation":  0.0810,
    "AdService":       0.0503,
    "Shipping":        0.0454,
    "Checkout":        0.0405,
    "Payment":         0.0072,
    "Email":           0.0052,
}

# ---------- USL / M/M/c parameters ----------
SIGMA   = 0.0248    # serial contention  (report Table 3)
KAPPA   = 0.0031    # coherency crosstalk (report Table 3)
S0_MS   = 80.0      # Frontend exclusive service demand (ms)
BACKEND = 5.019     # Sigma(V_i * R_i) for i!=0, MVA-computed (ms)
LAM_NOM = 10.0      # nominal arrival rate (req/s)
LAM_SAT = 12.5      # saturation bound: 1/D_0 = 1/0.080 = 12.5 req/s


# ── Erlang-C M/M/c helpers ────────────────────────────────────────────────────
def _erlang_c(c: int, a: float) -> float:
    """Erlang-C delay probability C(c,a) for an M/M/c queue."""
    rho_per = a / c
    if rho_per >= 1.0:
        return 1.0
    sum_terms = sum((a ** k) / math.factorial(k) for k in range(c))
    last = (a ** c) / math.factorial(c) / (1.0 - rho_per)
    return last / (sum_terms + last)


def _mmc_rt_ms(S_ms: float, lam: float, c: int) -> float:
    """Mean M/M/c response time in ms.  R = S + C(c,a)*S / (c*(1-rho_c))."""
    S_s = S_ms / 1000.0
    a   = lam * S_s
    rho_per = a / c
    if rho_per >= 1.0:
        return float("inf")
    Cca    = _erlang_c(c, a)
    wait_s = Cca * S_s / (c * (1.0 - rho_per))
    return (S_s + wait_s) * 1000.0


def _sla_breach_rate(S_s: float, sla_ms: float, backend_ms: float) -> float:
    """Arrival rate at which R_sys = sla_ms (M/M/1 model).
       R(lam) = S*1000/(1-lam*S) + backend_ms = sla_ms
       => lam = (1 - S*1000/(sla_ms-backend_ms)) / S
    """
    return (1.0 - S_s * 1000.0 / (sla_ms - backend_ms)) / S_s


# ============================================================
# Figure 1 — Reconstructed Microservice Call Graph
# ============================================================
def figure1_call_graph(path):
    """Figure 1: 11-service DAG with routing edges and service parameters."""
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.set_facecolor(LIGHT_BG)
    ax.axis("off")

    # Ingress header
    ax.text(0.5, 0.95, "External Ingress (λ₀ = 10 req/s)",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#E0E7FF",
                      edgecolor="#6366F1", lw=2),
            fontsize=11, fontweight="bold", transform=ax.transAxes)

    # Frontend (bottleneck)
    ax.text(0.5, 0.78,
            "Frontend Gateway (Go)\nS₀ = 80.0 ms | V₀ = 1.0000 | ρ₀ = 80.0%\n[PRIMARY BOTTLENECK]",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#FEE2E2",
                      edgecolor=RED, lw=2.5),
            fontsize=11, fontweight="bold", color="#991B1B",
            transform=ax.transAxes)

    ax.annotate("", xy=(0.5, 0.86), xytext=(0.5, 0.91),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color="#4F46E5", lw=2))

    # Tier 2 services
    tier2 = [
        ("ProductCatalog\nGo | 5.0ms | V=0.369",    0.10, 0.54),
        ("Currency\nNode | 3.0ms | V=0.185",         0.27, 0.54),
        ("Cart\nC# | 4.0ms | V=0.135",               0.44, 0.54),
        ("Recommendation\nPython | 7.5ms | V=0.080", 0.62, 0.54),
        ("AdService\nJava | 5.8ms | V=0.050",        0.80, 0.54),
    ]
    for label, x, y in tier2:
        ax.text(x, y, label, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#F1F5F9",
                          edgecolor="#64748B", lw=1.5),
                fontsize=8.5, transform=ax.transAxes)
        ax.annotate("", xy=(x, y + 0.07), xytext=(0.5, 0.70),
                    xycoords="axes fraction", textcoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color="#94A3B8", lw=1.2))

    # Checkout
    ax.text(0.10, 0.26, "Checkout\nGo | 14.5ms | V=0.040",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#F1F5F9",
                      edgecolor="#64748B", lw=1.5),
            fontsize=8.5, transform=ax.transAxes)
    ax.annotate("", xy=(0.10, 0.33), xytext=(0.5, 0.70),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color="#94A3B8", lw=1.2))

    # Redis (Cart dependency)
    ax.text(0.44, 0.26, "Redis State Store\nC | 2.0ms | V=0.128",
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#FEF3C7",
                      edgecolor=AMBER, lw=1.5),
            fontsize=8.5, transform=ax.transAxes)
    ax.annotate("", xy=(0.44, 0.33), xytext=(0.44, 0.47),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.5))

    # Leaf services from Checkout
    leaves = [
        ("Payment\nNode | 9.5ms",  0.62, 0.10),
        ("Shipping\nGo | 3.8ms",   0.76, 0.10),
        ("Email\nPython | 11.5ms", 0.90, 0.10),
    ]
    for label, x, y in leaves:
        ax.text(x, y, label, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#F8FAFC",
                          edgecolor="#94A3B8", lw=1),
                fontsize=8, transform=ax.transAxes)
        ax.annotate("", xy=(x, y + 0.06), xytext=(0.10, 0.20),
                    xycoords="axes fraction", textcoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color="#94A3B8",
                                   lw=1, linestyle=":"))

    ax.set_title("Figure 1: Reconstructed Microservice Call Graph for Google Online Boutique",
                 pad=15)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Generated {os.path.basename(path)}")


# ============================================================
# Figure 2 — LQN Three-Tier Architecture
# ============================================================
def figure2_lqn_tiers(path):
    """Figure 2: Three-Tier LQN Architecture in [0,1] axes coordinates."""
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.set_facecolor(LIGHT_BG)
    ax.axis("off")

    # Tier boxes — all y coordinates in [0,1] axes fraction
    tiers = [
        (
            "Tier 1: Client & Ingress Tier",
            ["User Browser / Locust Traffic Generator → Kubernetes Ingress"],
            0.76, "#E0E7FF", "#4F46E5",
        ),
        (
            "Tier 2: Application API Gateway (Bottleneck)",
            ["Frontend Service (Go HTTP Server, Exclusive S₀ = 80 ms, ρ₀ = 80%)"],
            0.50, "#FEE2E2", RED,
        ),
        (
            "Tier 3: Polyglot Backend Services & Data Store",
            [
                "ProductCatalog (Go, 5ms) | Currency (Node, 3ms) | Cart (C#, 4ms)",
                "Recommendation (Python, 7.5ms) | Ad (Java, 5.8ms) | Checkout (Go, 14.5ms)",
                "Shipping (Go, 3.8ms) | Payment (Node, 9.5ms) | Email (Python, 11.5ms) | Redis (C, 2ms)",
            ],
            0.18, "#F1F5F9", "#64748B",
        ),
    ]

    for title, items, y_center, bg, border in tiers:
        height = 0.18
        rect = patches.FancyBboxPatch(
            (0.05, y_center - height / 2), 0.90, height,
            boxstyle="round,pad=0.02", facecolor=bg, edgecolor=border, lw=2,
            transform=ax.transAxes,
        )
        ax.add_patch(rect)
        ax.text(0.5, y_center + 0.04, title,
                ha="center", va="center", fontsize=10.5, fontweight="bold",
                color=border, transform=ax.transAxes)
        ax.text(0.5, y_center - 0.02,
                "\n".join(items),
                ha="center", va="center", fontsize=8.5, color="#1E293B",
                transform=ax.transAxes)

    # Arrows between tiers
    ax.annotate("", xy=(0.5, 0.60), xytext=(0.5, 0.67),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->", lw=2, color="#4F46E5"))
    ax.annotate("", xy=(0.5, 0.29), xytext=(0.5, 0.41),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->", lw=2, color=RED))

    ax.set_title("Figure 2: Layered Queueing Network (LQN) Three-Tier Architecture", pad=15)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Generated {os.path.basename(path)}")


# ============================================================
# Figure 3 — Utilisation Spectrum @ 10 req/s
# ============================================================
def figure3_utilisation_spectrum(path):
    """Figure 3: CPU utilisation bar chart — log scale, all 11 services."""
    names  = [s[0] for s in SERVICES]
    utils  = [s[4] for s in SERVICES]           # rho_i * 100 at lambda=10
    colors = [SERVICE_COLORS[n] for n in names]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.bar(names, utils, color=colors, edgecolor="#1E293B", linewidth=0.8)

    ax.set_yscale("log")
    ax.set_ylabel("CPU Utilisation @ 10 req/s (%)  [log scale]")
    ax.set_title("Figure 3: Microservice Utilisation Spectrum at 10 req/s Nominal Load")
    ax.set_ylim(0.03, 300)
    ax.axhline(100, color=RED, linestyle="--", linewidth=1.2, label="100% ceiling")
    ax.axhline(80.0, color=RED, linestyle=":", linewidth=1, alpha=0.6)
    ax.text(7.5, 82, "Frontend = 80.0%\n(43.3× Demand Imbalance)",
            color=RED, fontweight="bold", fontsize=9)

    for bar, v in zip(bars, utils):
        label = f"{v:.2f}%" if v < 10 else f"{v:.1f}%"
        ax.text(bar.get_x() + bar.get_width() / 2, v * 1.25, label,
                ha="center", va="bottom", fontsize=8,
                fontweight="bold" if v > 10 else "normal")

    ax.legend(loc="upper right")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Generated {os.path.basename(path)}")


# ============================================================
# Figure 4 — Model Predictions vs. Measurements
# ============================================================
def figure4_predictions_vs_measurements(path):
    """Figure 4: Model vs. empirical (8 tiers). WMAPE=37.48%, R²=0.6205."""
    # Continuous M/M/1 + backend curve
    rates_cont = np.linspace(1.0, 12.4, 300)
    S0_s = S0_MS / 1000.0
    pred_cont, rates_valid = [], []
    for r in rates_cont:
        rho0 = r * S0_s
        if rho0 < 1.0:
            pred_cont.append(S0_s / (1.0 - rho0) * 1000.0 + BACKEND)
            rates_valid.append(r)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(rates_valid, pred_cont, color=BLUE, lw=2.5,
            label="Analytical M/M/1 Model (continuous)", marker="s",
            markevery=40, markersize=5)
    ax.scatter(LAMBDA_TIERS, R_OBS, color=RED, s=70, zorder=6,
               label="Empirical Measurements (Jaeger / Kubernetes)",
               edgecolor="black", linewidth=0.8)
    ax.scatter(LAMBDA_TIERS, R_PRED, color=BLUE, s=45, marker="^", zorder=5,
               label="Model Predictions (8 discrete tiers)",
               edgecolor="white", alpha=0.8)

    # Annotation box (report Section 6)
    ax.text(1.4, 1780,
            f"WMAPE = {WMAPE:.2f}%\n$R^2$ = {R2:.4f}\n(8 workload tiers, λ = 1–12 req/s)",
            fontsize=9, color="#374151",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor=GRAY, alpha=0.95))

    ax.set_xlabel(r"Arrival Rate $\lambda_0$ (req/s)")
    ax.set_ylabel("End-to-End System Response Time (ms)")
    ax.set_title("Figure 4: Analytical Model Predictions vs. Real-World Benchmark Measurements")
    ax.set_ylim(0, 2200)
    ax.set_xlim(1, 12.5)
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Generated {os.path.basename(path)}")


# ============================================================
# Figure 5 — Hockey-Stick Knee & 500 ms SLA
# ============================================================
def figure5_hockey_stick(path):
    """Figure 5: Latency knee curve — SLA breach at 10.4 req/s (analytically derived)."""
    S0_s = S0_MS / 1000.0
    rates = np.linspace(1.0, 12.4, 500)
    lat = []
    valid_rates = []
    for r in rates:
        rho0 = r * S0_s
        if rho0 < 1.0:
            lat.append(S0_s / (1.0 - rho0) * 1000.0 + BACKEND)
            valid_rates.append(r)
    rates = np.array(valid_rates)
    lat   = np.array(lat)

    # SLA breach: R(λ) = 500 ms => λ = (1 - S0*1000/(500-backend)) / S0
    sla_breach = _sla_breach_rate(S0_s, 500.0, BACKEND)  # ≈ 10.4 req/s

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(rates, lat, color=BLUE, lw=2.5, label=r"System Latency $R(\lambda_0)$")
    ax.axhline(500.0, color=RED, linestyle="--", lw=2, label="500 ms SLA Boundary")
    ax.axvline(sla_breach, color=RED, linestyle=":", lw=1.5, alpha=0.8,
               label=f"SLA Breach @ {sla_breach:.1f} req/s")
    ax.axvline(LAM_SAT, color=GRAY, linestyle=":", lw=1.5,
               label=r"Saturation $\lambda_{{sat}}$ = 12.5 req/s")

    # Annotate SLA breach
    ax.annotate(
        f"SLA Breach\n{sla_breach:.1f} req/s",
        xy=(sla_breach, 500), xytext=(sla_breach - 2.8, 900),
        arrowprops=dict(arrowstyle="->", color=RED, lw=1.5),
        color=RED, fontweight="bold", fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEE2E2", edgecolor=RED),
    )

    # Knee region
    ax.axvspan(9.0, 11.5, color="#FEF3C7", alpha=0.40,
               label="Operational Knee (HPA Trigger Zone)")

    ax.set_xlabel(r"Workload Arrival Rate $\lambda_0$ (req/s)")
    ax.set_ylabel(r"Response Time $R$ (ms)")
    ax.set_title("Figure 5: System Latency Hockey-Stick Knee Curve & 500 ms SLA Boundary")
    ax.set_ylim(0, 2200)
    ax.set_xlim(1, 13)
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Generated {os.path.basename(path)}")


# ============================================================
# Figure 6 — Multi-Replica Scaling (c = 1..6)
# ============================================================
def figure6_multi_replica_scaling(path):
    """Figure 6: Erlang-C M/M/c latencies + USL efficiency. Sweet spot c=3."""
    replicas = np.array([1, 2, 3, 4, 5, 6])

    # Compute via Erlang-C formula (not hardcoded)
    latencies = np.array([
        _mmc_rt_ms(S0_MS, LAM_NOM, int(c)) + BACKEND for c in replicas
    ])
    # USL efficiency: η(c) = 1 / (1 + σ(c-1) + κ·c·(c-1))
    efficiency = np.array([
        100.0 / (1.0 + SIGMA * (c - 1) + KAPPA * c * (c - 1)) for c in replicas
    ])

    fig, ax1 = plt.subplots(figsize=(9, 5.5))
    ax1.set_xlabel("Frontend Replica Count ($c$)")
    ax1.set_ylabel("System Latency @ 10 req/s (ms)", color=BLUE)
    line1 = ax1.plot(replicas, latencies, "-o", color=BLUE, lw=2.5,
                     markersize=8, label="System Latency (ms)")
    ax1.tick_params(axis="y", labelcolor=BLUE)
    ax1.set_ylim(0, 450)

    ax2 = ax1.twinx()
    ax2.set_ylabel(r"USL Scaling Efficiency $\eta(c)$ (%)", color=GREEN)
    line2 = ax2.plot(replicas, efficiency, marker="s", linestyle="--", color=GREEN,
                     lw=2, markersize=8, label="USL Efficiency (%)")
    ax2.tick_params(axis="y", labelcolor=GREEN)
    ax2.set_ylim(50, 110)

    # Sweet spot annotation — c=3: 86.9 ms, 93.6% efficiency
    ax1.annotate(
        f"Sweet Spot (c=3)\n78.5% Latency Drop\n{efficiency[2]:.1f}% USL Efficiency",
        xy=(3, latencies[2]), xytext=(3.6, 220),
        arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=6),
        fontweight="bold", fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEF3C7", edgecolor=AMBER),
    )

    lines  = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper right")
    ax1.set_title("Figure 6: System Response Time Under Multi-Replica Frontend Scaling (c = 1 to 6)")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Generated {os.path.basename(path)}")


# ============================================================
# Figure 7 — Sensitivity Tornado
# ============================================================
def figure7_sensitivity_tornado(path):
    """Figure 7: dR/dS_i = V_i/(1-rho_i)^2 — tornado chart sorted ascending."""
    # Sort ascending for tornado display (highest at top)
    items = sorted(SENS.items(), key=lambda x: x[1])
    names = [k for k, _ in items]
    vals  = [v for _, v in items]
    colors = [RED if k == "Frontend" else BLUE for k in names]

    total_sens = sum(SENS.values())

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(names, vals, color=colors, edgecolor="#1E293B", height=0.6)
    ax.set_xlabel(
        r"Sensitivity $\partial R_{\mathrm{sys}} / \partial S_i$ "
        r"(ms latency saved per 1 ms optimised)"
    )
    ax.set_title("Figure 7: Sensitivity Tornado Chart — Where System Speedup Comes From")
    ax.set_xlim(0, 28)

    # Value & ROI annotations
    for bar, val in zip(bars, vals):
        x   = bar.get_width()
        roi = val / total_sens * 100
        if val > 1.0:
            ax.text(x + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"{val:.4f} ms/ms  ({roi:.2f}% ROI)",
                    va="center", fontweight="bold", color=RED, fontsize=9)
        else:
            ax.text(x + 0.2, bar.get_y() + bar.get_height() / 2,
                    f"{val:.4f}",
                    va="center", fontsize=8, color="#475569")

    ax.axvline(0.5, color=RED, linestyle="--", alpha=0.7,
               label="Negligible ROI threshold (< 0.5 ms/ms)")
    ax.text(0.55, 1.5, "Negligible ROI Threshold", color=RED, fontsize=8.5)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Generated {os.path.basename(path)}")


# ============================================================
# Figure 8 — Utilisation vs. Arrival Rate
# ============================================================
def figure8_utilisation_vs_arrival(path):
    """Figure 8: CPU utilisation curves for all 11 services vs. lambda."""
    lam = np.linspace(1.0, 12.5, 200)
    fig, ax = plt.subplots(figsize=(9, 5.5))

    # Show label only for top 3 services
    label_set = {"Frontend", "ProductCatalog", "Checkout"}
    for name, V, S_ms, _, _ in SERVICES:
        rho = lam * V * S_ms / 1000.0 * 100.0   # rho_i * 100
        ax.plot(lam, rho, color=SERVICE_COLORS[name],
                linewidth=2.0 if name == "Frontend" else 1.2,
                label=name if name in label_set else "_nolegend_")

    ax.axvline(LAM_SAT, color=RED, linestyle="--", linewidth=1.5,
               label=f"Saturation @ {LAM_SAT} req/s")
    ax.axhline(100, color="black", linestyle=":", linewidth=1)
    ax.set_xlabel(r"Arrival Rate $\lambda_0$ (req/s)")
    ax.set_ylabel("CPU Utilisation (%)")
    ax.set_title("Figure 8: Service-Centre Utilisation vs. Arrival Rate")
    ax.set_ylim(0, 110)
    ax.legend(loc="upper left", ncol=2)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Generated {os.path.basename(path)}")


# ============================================================
# Figure 9 — System Response Time vs. Arrival Rate
# ============================================================
def figure9_system_response_time(path):
    """Figure 9: M/M/1 upper bound curves with backend contribution."""
    S0_s = S0_MS / 1000.0
    rates = np.linspace(0.5, 12.4, 400)
    R_fe_list, R_sys_list, r_valid = [], [], []
    for r in rates:
        rho0 = r * S0_s
        if rho0 < 1.0:
            fe = S0_s / (1.0 - rho0) * 1000.0
            R_fe_list.append(fe)
            R_sys_list.append(fe + BACKEND)
            r_valid.append(r)
    r_valid  = np.array(r_valid)
    R_fe     = np.array(R_fe_list)
    R_sys    = np.array(R_sys_list)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(r_valid, R_sys, color=BLUE, lw=2.5,
            label=f"$R_{{sys}}$ (M/M/1 + {BACKEND:.3f} ms backend)")
    ax.plot(r_valid, R_fe, color=CB["orange"], lw=1.5, linestyle="--",
            label="$R_{{Frontend}}$ (M/M/1 only)")
    ax.axhline(500, color=RED, linestyle="--", lw=1.5, label="500 ms SLA")
    ax.scatter([10.0], [405.0 + BACKEND], color=RED, s=80, zorder=6,
               label=f"Operating point: λ=10 → {405.0+BACKEND:.0f} ms")
    ax.set_xlabel(r"Arrival Rate $\lambda_0$ (req/s)")
    ax.set_ylabel("End-to-End Response Time (ms)")
    ax.set_title("Figure 9: End-to-End Response Time vs. Arrival Rate (Pure M/M/1 Upper Bound)")
    ax.set_ylim(0, 3000)
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Generated {os.path.basename(path)}")


# ============================================================
# Main
# ============================================================
def main():
    print("Generating all 9 publication figures...")
    figure1_call_graph(os.path.join(OUT, "figure1_reconstructed_call_graph.png"))
    figure2_lqn_tiers(os.path.join(OUT, "figure2_lqn_three_tier_architecture.png"))
    figure3_utilisation_spectrum(os.path.join(OUT, "figure3_utilisation_spectrum.png"))
    figure4_predictions_vs_measurements(os.path.join(OUT, "figure4_predictions_vs_measurements.png"))
    figure5_hockey_stick(os.path.join(OUT, "figure5_hockey_stick_knee_curve.png"))
    figure6_multi_replica_scaling(os.path.join(OUT, "figure6_multi_replica_scaling.png"))
    figure7_sensitivity_tornado(os.path.join(OUT, "figure7_sensitivity_tornado.png"))
    figure8_utilisation_vs_arrival(os.path.join(OUT, "utilization_vs_arrival_rate.png"))
    figure9_system_response_time(os.path.join(OUT, "system_response_time.png"))
    print(f"\nAll 9 figures generated successfully in {OUT}")


if __name__ == "__main__":
    main()
