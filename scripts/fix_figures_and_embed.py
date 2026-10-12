"""
fix_figures_and_embed.py
========================
Three-phase fix script:

  Phase A: Regenerate Figures 1–7 with correct October 8 canonical data
           (replaces old values: Frontend S0=80ms, WMAPE=37.48%, etc.)

  Phase B: Fix Figure 7 caption typo in SPEFinal.docx
           (Para 137 said "Figure 3" – corrected to "Figure 7")

  Phase C: Embed all 7 figures into SPEFinal.docx immediately above
           their respective captions, then sync Course.docx and re-export PDF.

All figures are 300 DPI, 5.5-inch wide, colorblind-safe Okabe-Ito palette.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import copy, math, shutil, zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

np.random.seed(42)

BASE = Path(r"c:\Users\7172981\Downloads\Analytical QNLQN Model of a Microservice Application - Oct")
FIGS = BASE / "results" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)
DOCX = BASE / "SPEFinal.docx"
COURSE_DOCX = BASE / "Software Performance Engineering Course.docx"

# ──────────────────────────────────────────────────────────────────────────────
# CANONICAL OCTOBER 8 DATA
# ──────────────────────────────────────────────────────────────────────────────

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial"],
    "font.size": 10,
    "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.labelsize": 10, "axes.labelweight": "bold",
    "legend.fontsize": 9,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.grid": True, "grid.alpha": 0.25, "grid.linestyle": "--",
})

# Okabe-Ito colorblind-safe palette
BLUE   = "#0072B2"
RED    = "#D55E00"
GREEN  = "#009E73"
AMBER  = "#E69F00"
PURPLE = "#CC79A7"
SKY    = "#56B4E9"
GRAY   = "#999999"
BLACK  = "#000000"
LIGHT  = "#F8FAFC"

# Service data — canonical October 8, from service_demands_clean.json
# (name, V_i, S_ms, D_ms, rho_pct at lambda=10)
SERVICES = [
    ("Frontend",            1.0000, 18.880, 18.880, 18.88),
    ("CartService",         0.0399, 35.229,  1.406,  1.41),
    ("CheckoutService",     0.0367, 33.522,  1.230,  1.23),
    ("CurrencyService",     0.2771,  1.603,  0.444,  0.44),
    ("AdService",           0.0218, 19.882,  0.433,  0.43),
    ("RecommendationSvc",   0.0898,  3.828,  0.344,  0.34),
    ("PaymentService",      0.0051, 47.942,  0.244,  0.24),
    ("ProductCatalog",      0.6369,  0.324,  0.206,  0.21),
    ("ShippingService",     0.0142, 13.445,  0.191,  0.19),
    ("Redis",               0.0379,  2.000,  0.076,  0.08),
    ("EmailService",        0.0051,  1.293,  0.007,  0.01),
]

SVC_COLORS = {
    "Frontend": RED, "CartService": BLUE, "CheckoutService": PURPLE,
    "CurrencyService": AMBER, "AdService": SKY, "RecommendationSvc": GREEN,
    "PaymentService": GRAY, "ProductCatalog": "#8B4513",
    "ShippingService": "#FF69B4", "Redis": BLACK, "EmailService": "#4CAF50",
}

# Table 7 validation tiers (4 empirical tiers, October 8)
LAMBDA_OBS = np.array([2.0,    5.0,    8.0,    10.0])
R_OBS      = np.array([354.2,  996.8,  857.0,  2887.9])
R_PRED     = np.array([101.50, 139.62, 228.54,  406.33])
WMAPE = 82.81
R2    = -0.986

# M/M/c scaling table
C_REPS   = np.array([1, 2, 3, 4, 5, 6])
CAP_10   = np.array([52.97, 102.75, 148.75, 190.59, 228.06, 261.13])
LAT_10   = np.array([23.27,  19.05,  18.89,  18.88,  18.88,  18.88])
USL_EFF  = np.array([100.0,  97.0,   93.6,   90.0,   86.1,   82.2])

# Sensitivity scores (October 8)
SENS = {
    "Frontend":          1.5197,
    "ProductCatalog":    0.6396,
    "CurrencyService":   0.2796,
    "RecommendationSvc": 0.0904,
    "CartService":       0.0411,
    "AdService":         0.0215,
    "CheckoutService":   0.0363,
    "ShippingService":   0.0140,
    "PaymentService":    0.0051,
    "EmailService":      0.0050,
    "Redis":             0.0376,
}

S0_MS  = 18.880   # Frontend bottleneck service time
LAM_SAT = 52.97   # single-replica saturation (req/s)
SIGMA  = 0.0248
KAPPA  = 0.0031


def _erlang_c(c, a):
    rho = a / c
    if rho >= 1.0:
        return 1.0
    terms = sum(a**k / math.factorial(k) for k in range(c))
    last = a**c / math.factorial(c) / (1.0 - rho)
    return last / (terms + last)


def _mmc_rt(S_ms, lam, c):
    S_s = S_ms / 1000.0
    a = lam * S_s
    rho = a / c
    if rho >= 1.0:
        return float("inf")
    Cca = _erlang_c(c, a)
    wait = Cca * S_s / (c * (1.0 - rho))
    return (S_s + wait) * 1000.0


# ══════════════════════════════════════════════════════════════════════════════
# PHASE A — GENERATE FIGURES
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("PHASE A — Regenerating Figures 1–7")
print("=" * 60)


# ── Figure 1: Call Graph ──────────────────────────────────────────────────────
def make_figure1():
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.set_facecolor(LIGHT)
    ax.axis("off")
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)

    def node(x, y, label, color="#DBEAFE", ec=BLUE, lw=1.5, fs=8.5, bold=False):
        bb = dict(boxstyle="round,pad=0.4", facecolor=color, edgecolor=ec, lw=lw)
        ax.text(x, y, label, ha="center", va="center", bbox=bb,
                fontsize=fs, fontweight="bold" if bold else "normal",
                transform=ax.transData)

    def arrow(x0, y0, x1, y1, label="", color="#555"):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2))
        if label:
            mx, my = (x0+x1)/2, (y0+y1)/2+0.15
            ax.text(mx, my, label, ha="center", va="center",
                    fontsize=7.5, color="#444")

    # Nodes
    ax.text(5, 9.5, "External Client (Locust 5 req/s)", ha="center",
            fontsize=10, fontweight="bold", color="#1E3A5F")

    node(5, 8.5, "Frontend Gateway (Go)\nS₀=18.88ms | V₀=1.00 | ρ=18.88%\n[PRIMARY BOTTLENECK]",
         "#FEE2E2", RED, 2.5, 9.5, True)

    node(2,  6.8, "ProductCatalog (Go)\nS=0.32ms | V=0.637",  "#DBEAFE", BLUE)
    node(5,  6.8, "CurrencyService (Node)\nS=1.60ms | V=0.277", "#FEF9C3", AMBER)
    node(8,  6.8, "CartService (C#)\nS=35.2ms | V=0.040",  "#DCFCE7", GREEN)

    node(1,  5.0, "RecommendationSvc\nS=3.83ms | V=0.090",   "#F3E8FF", PURPLE, fs=8)
    node(3.5,5.0, "AdService (Java)\nS=19.88ms | V=0.022",  "#FFEDD5", "#F97316", fs=8)
    node(6.5,5.0, "CheckoutService (Go)\nS=33.52ms | V=0.037","#E0F2FE", SKY, fs=8)

    node(8.5,5.0, "Redis State Store\nS=2.0ms | V=0.038",   "#F1F5F9", GRAY, fs=8)

    node(5,  3.2, "ShippingService (Go)\nS=13.45ms | V=0.014", "#FEF3C7", "#92400E", fs=8)
    node(7,  3.2, "PaymentService (Node)\nS=47.94ms | V=0.005","#FFE4E6", "#BE123C", fs=8)
    node(3,  3.2, "EmailService (Python)\nS=1.29ms | V=0.005", "#ECFDF5", "#065F46", fs=8)

    # Arrows
    arrow(5, 8.1, 5, 8.9)  # ingress → frontend
    arrow(5, 8.15, 2, 7.2)
    arrow(5, 8.15, 5, 7.2)
    arrow(5, 8.15, 8, 7.2)
    arrow(2, 6.45, 1, 5.35)
    arrow(5, 6.45, 3.5, 5.35)
    arrow(8, 6.45, 6.5, 5.35)
    arrow(8, 6.45, 8.5, 5.35)
    arrow(6.5,4.65, 5, 3.55)
    arrow(6.5,4.65, 7, 3.55)
    arrow(6.5,4.65, 3, 3.55)

    ax.set_title("Figure 1: Reconstructed Microservice Call Graph — Google Online Boutique "
                 "(October 8, 2026 | 6,642 spans | 687 traces)",
                 fontsize=10, pad=8, fontweight="bold")
    out = FIGS / "figure1_reconstructed_call_graph.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [1] {out.name}")
    return out


# ── Figure 2: LQN Three-Tier Architecture ────────────────────────────────────
def make_figure2():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_facecolor(LIGHT); ax.axis("off")
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)

    def tier_box(x, y, w, h, label, color, ec):
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.15",
                              facecolor=color, edgecolor=ec, lw=2, alpha=0.35)
        ax.add_patch(rect)
        ax.text(x+w/2, y+h+0.25, label, ha="center", fontsize=11,
                fontweight="bold", color=ec)

    def svc_box(x, y, label, color, ec):
        bb = dict(boxstyle="round,pad=0.35", facecolor=color, edgecolor=ec, lw=1.5)
        ax.text(x, y, label, ha="center", va="center", fontsize=8.5, bbox=bb)

    tier_box(0.3, 6.5, 9.4, 2.5, "Tier 1 — Entry Point (λ₀ = 10 req/s)",
             "#FEE2E2", RED)
    tier_box(0.3, 3.5, 9.4, 2.5, "Tier 2 — Business Logic",
             "#DBEAFE", BLUE)
    tier_box(0.3, 0.5, 9.4, 2.5, "Tier 3 — Data / Infrastructure",
             "#DCFCE7", GREEN)

    svc_box(5, 7.7,  "Frontend Gateway\nS₀=18.88ms, D₀=18.88ms\nρ=18.88% — BOTTLENECK",
            "#FEE2E2", RED)

    for x, lbl in [(1.5,  "ProductCatalog\nS=0.32ms"),
                   (3.2,  "CurrencyService\nS=1.60ms"),
                   (5.0,  "RecommendationSvc\nS=3.83ms"),
                   (6.8,  "AdService\nS=19.88ms"),
                   (8.5,  "CheckoutService\nS=33.52ms")]:
        svc_box(x, 4.75, lbl, "#DBEAFE", BLUE)

    for x, lbl in [(2.0, "CartService\nS=35.23ms"),
                   (4.2, "PaymentService\nS=47.94ms"),
                   (6.2, "ShippingService\nS=13.45ms"),
                   (8.2, "Redis\nS=2.0ms")]:
        svc_box(x, 1.75, lbl, "#DCFCE7", GREEN)

    def harrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color="#666", lw=1.1))

    harrow(5, 9.2, 5, 8.2)  # ingress
    ax.text(5, 9.4, "External Client (Locust 5 req/s)", ha="center",
            fontsize=9.5, fontweight="bold", color="#1E3A5F")

    harrow(5, 7.35, 3.2, 5.1)
    harrow(5, 7.35, 5.0, 5.1)
    harrow(5, 7.35, 8.5, 5.1)
    harrow(8.5, 4.4, 4.2, 2.1)
    harrow(8.5, 4.4, 6.2, 2.1)
    harrow(3.2, 4.4, 2.0, 2.1)
    harrow(5.0, 4.4, 8.2, 2.1)

    ax.set_title("Figure 2: Open Jackson Queueing Network — Layered Three-Tier Architecture\n"
                 "(M/M/1 nodes, BCMP product-form solution, 11 services)",
                 fontsize=10, pad=8, fontweight="bold")
    out = FIGS / "figure2_lqn_three_tier_architecture.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [2] {out.name}")
    return out


# ── Figure 3: Utilisation bar chart ──────────────────────────────────────────
def make_figure3():
    names = [s[0] for s in SERVICES]
    rhos  = [s[4] for s in SERVICES]
    colors = [RED if n == "Frontend" else BLUE for n in names]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(names, rhos, color=colors, edgecolor="white", linewidth=0.5)

    for bar, v in zip(bars, rhos):
        ax.text(v + 0.2, bar.get_y() + bar.get_height()/2,
                f"{v:.2f}%", va="center", fontsize=8.5)

    ax.axvline(100, color="black", lw=1.5, ls="--", label="Saturation (100%)")
    ax.set_xlabel("CPU Utilisation ρᵢ (%)")
    ax.set_title(
        f"Figure 3: Predicted Microservice CPU Utilisation at λ₀ = 10 req/s\n"
        f"Frontend ρ = 18.88% — 13.43× higher than second-heaviest (CartService 1.41%)",
        fontsize=10, fontweight="bold")
    ax.set_xlim(0, 24)
    red_patch = mpatches.Patch(color=RED, label="Frontend (bottleneck)")
    blue_patch = mpatches.Patch(color=BLUE, label="Other services")
    ax.legend(handles=[red_patch, blue_patch], loc="lower right")
    ax.invert_yaxis()

    out = FIGS / "figure3_utilisation_spectrum.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [3] {out.name}")
    return out


# ── Figure 4: Model vs Observed ───────────────────────────────────────────────
def make_figure4():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: time-series comparison
    ax = axes[0]
    ax.plot(LAMBDA_OBS, R_OBS,  "o-",  color=RED,  lw=2, ms=8,
            label=f"Observed (Docker Desktop)")
    ax.plot(LAMBDA_OBS, R_PRED, "s--", color=BLUE, lw=2, ms=8,
            label="QN Model Prediction")
    ax.axhline(500, color=AMBER, lw=1.5, ls=":", label="500 ms SLA limit")
    for lam, obs, pred in zip(LAMBDA_OBS, R_OBS, R_PRED):
        ape = abs(obs - pred) / obs * 100
        ax.annotate(f"APE={ape:.0f}%", xy=(lam, (obs+pred)/2),
                    xytext=(lam+0.3, (obs+pred)/2),
                    fontsize=7.5, color="#555")
    ax.set_xlabel("Arrival Rate λ₀ (req/s)")
    ax.set_ylabel("Response Time (ms)")
    ax.set_title(f"Model vs Observed Response Times\nWMAPE={WMAPE}%, R²={R2}")
    ax.legend(fontsize=8)

    # Right: APE by tier
    ax2 = axes[1]
    apes = [abs(o - p) / o * 100 for o, p in zip(R_OBS, R_PRED)]
    bar_colors = [GREEN if a < 50 else AMBER if a < 75 else RED for a in apes]
    bars = ax2.bar([f"λ={l:.0f}" for l in LAMBDA_OBS], apes,
                   color=bar_colors, edgecolor="white")
    for b, a in zip(bars, apes):
        ax2.text(b.get_x()+b.get_width()/2, b.get_height()+1,
                 f"{a:.1f}%", ha="center", fontsize=9, fontweight="bold")
    ax2.axhline(WMAPE, color=RED, lw=1.5, ls="--", label=f"WMAPE={WMAPE}%")
    ax2.set_ylabel("Absolute Percentage Error (%)")
    ax2.set_title("Error by Workload Tier\n(Docker WSL2 contention dominates)")
    ax2.legend()
    ax2.set_ylim(0, 100)

    fig.suptitle("Figure 4: Analytical QN Model vs. Empirical Observations — October 8, 2026",
                 fontsize=11, fontweight="bold", y=1.01)
    out = FIGS / "figure4_predictions_vs_measurements.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [4] {out.name}")
    return out


# ── Figure 5: Hockey-stick latency curve ─────────────────────────────────────
def make_figure5():
    lam_range = np.linspace(0.1, 52.0, 500)
    # M/M/1 response time: R = S/(1-rho), rho=lambda*S/1000
    def R(lam, S_ms=S0_MS):
        rho = lam * S_ms / 1000.0
        return S_ms / (1 - rho) if rho < 1 else float("inf")

    rt = np.array([R(l) for l in lam_range])
    valid = rt < 10000

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(lam_range[valid], rt[valid], color=BLUE, lw=2.5,
            label="M/M/1 Model R(λ) = S₀/(1−ρ₀)")
    ax.axhline(500, color=RED, lw=1.8, ls="--", label="500 ms SLA Hard Limit")
    ax.axvline(LAM_SAT, color=AMBER, lw=1.8, ls=":",
               label=f"Saturation λ_sat = {LAM_SAT} req/s")
    ax.axvline(10, color=GREEN, lw=1.5, ls="-.",
               label="Operating Point λ₀ = 10 req/s")

    # Mark operating point
    r_at_10 = R(10)
    ax.annotate(f"λ=10: R={r_at_10:.1f} ms\nρ=18.88%",
                xy=(10, r_at_10), xytext=(15, r_at_10 + 150),
                fontsize=9, color=GREEN,
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.2))

    # Shade safe zone
    lam_sla = (1 - 500.0/S0_MS * (-1)) if 500 > S0_MS else (1 - S0_MS/500)
    sla_lam = (1 - S0_MS/500) / (S0_MS/1000)
    safe = lam_range[valid] < min(sla_lam, LAM_SAT)
    ax.fill_between(lam_range[valid], 0, rt[valid],
                    where=lam_range[valid] <= sla_lam,
                    alpha=0.08, color=GREEN, label="SLA-safe zone")
    ax.fill_between(lam_range[valid], 0, rt[valid],
                    where=lam_range[valid] > sla_lam,
                    alpha=0.08, color=RED, label="SLA breach zone")

    ax.set_xlabel("Arrival Rate λ₀ (req/s)")
    ax.set_ylabel("Mean Response Time R (ms)")
    ax.set_ylim(0, 1500)
    ax.set_xlim(0, 55)
    ax.set_title(
        f"Figure 5: System Latency Hockey-Stick Curve — Single Frontend Replica\n"
        f"S₀ = {S0_MS} ms | λ_sat = {LAM_SAT} req/s | SLA 500 ms breach at ~{sla_lam:.1f} req/s",
        fontsize=10, fontweight="bold")
    ax.legend(loc="upper left", fontsize=8)

    out = FIGS / "figure5_hockey_stick_knee_curve.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [5] {out.name}")
    return out


# ── Figure 6: Multi-replica scaling ──────────────────────────────────────────
def make_figure6():
    lam_range = np.linspace(0.1, 200, 1000)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left: latency vs lambda for c=1..6
    ax = axes[0]
    palette = [RED, AMBER, GREEN, BLUE, PURPLE, GRAY]
    for c, color in zip(C_REPS, palette):
        rts = []
        for lam in lam_range:
            r = _mmc_rt(S0_MS, lam, c)
            rts.append(min(r, 5000))
        ls = "-" if c == 3 else ("--" if c == 1 else "-.")
        lw = 2.5 if c == 3 else 1.5
        ax.plot(lam_range, rts, color=color, lw=lw, ls=ls,
                label=f"c={c} (cap={CAP_10[c-1]:.0f} req/s)")

    ax.axhline(500, color="black", lw=1.2, ls=":", label="500 ms SLA")
    ax.axvline(10, color="black", lw=1, ls="--", alpha=0.5, label="λ=10 req/s")
    ax.set_xlabel("Arrival Rate λ₀ (req/s)")
    ax.set_ylabel("Mean Response Time R (ms)")
    ax.set_xlim(0, 200); ax.set_ylim(0, 3000)
    ax.set_title("M/M/c Response Time vs. Load\n(Frontend replicas, S₀=18.88 ms)")
    ax.legend(fontsize=7.5, ncol=2)

    # Right: capacity bar + USL efficiency line
    ax2 = axes[1]
    bar_colors = [GREEN if c == 3 else BLUE for c in C_REPS]
    bars = ax2.bar(C_REPS, CAP_10, color=bar_colors, alpha=0.75,
                   edgecolor="white", label="Max Capacity (req/s)")
    for b, cap in zip(bars, CAP_10):
        ax2.text(b.get_x()+b.get_width()/2, b.get_height()+2,
                 f"{cap:.0f}", ha="center", fontsize=8.5, fontweight="bold")

    ax3 = ax2.twinx()
    ax3.plot(C_REPS, USL_EFF, "D--", color=RED, lw=2, ms=7, label="USL Efficiency η(c)")
    ax3.axhline(93.6, color=GREEN, lw=1.2, ls=":", alpha=0.7)
    ax3.set_ylabel("USL Scaling Efficiency η(c) (%)", color=RED)
    ax3.set_ylim(70, 110)
    ax3.tick_params(axis="y", labelcolor=RED)

    ax2.set_xlabel("Frontend Replicas c")
    ax2.set_ylabel("Maximum System Capacity (req/s)")
    ax2.set_title("Capacity & USL Efficiency vs. Replicas\n(c=3 OPTIMAL: 148.75 req/s, 93.6% USL)")
    ax2.set_xticks(C_REPS)
    # Annotate c=3
    ax2.annotate("OPTIMAL\nc=3", xy=(3, 148.75), xytext=(3.4, 160),
                 fontsize=9, color=GREEN, fontweight="bold",
                 arrowprops=dict(arrowstyle="-|>", color=GREEN))

    fig.suptitle("Figure 6: M/M/c Multi-Replica Scaling Analysis — Frontend Horizontal Pod Autoscaling",
                 fontsize=10, fontweight="bold", y=1.01)
    out = FIGS / "figure6_multi_replica_scaling.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [6] {out.name}")
    return out


# ── Figure 7: Sensitivity tornado chart ──────────────────────────────────────
def make_figure7():
    items = sorted(SENS.items(), key=lambda x: x[1])
    names = [k for k, v in items]
    vals  = [v for k, v in items]
    total = sum(SENS.values())
    rois  = [v / total * 100 for v in vals]
    colors = [RED if n == "Frontend" else BLUE for n in names]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    # Left: sensitivity scores
    ax = axes[0]
    bars = ax.barh(names, vals, color=colors, edgecolor="white")
    for b, v in zip(bars, vals):
        ax.text(v + 0.01, b.get_y()+b.get_height()/2,
                f"{v:.4f} ms/ms", va="center", fontsize=8.5)
    ax.set_xlabel("Sensitivity ∂R/∂Sᵢ (ms per ms service time reduction)")
    ax.set_title("Sensitivity Score by Service\n(∂R/∂Sᵢ = Vᵢ / (1−ρᵢ)²)")
    ax.invert_yaxis()

    # Right: ROI pie / bar
    ax2 = axes[1]
    roi_sorted = sorted(zip(names, rois), key=lambda x: -x[1])
    rnames = [n for n, _ in roi_sorted]
    rvals  = [v for _, v in roi_sorted]
    bar_colors2 = [RED if n == "Frontend" else BLUE for n in rnames]
    bars2 = ax2.barh(rnames, rvals, color=bar_colors2, edgecolor="white")
    for b, v in zip(bars2, rvals):
        ax2.text(v + 0.3, b.get_y()+b.get_height()/2,
                 f"{v:.1f}%", va="center", fontsize=8.5)
    ax2.set_xlabel("Share of Total System ROI (%)")
    ax2.set_title("Optimisation ROI Distribution\n(Frontend = 56.44% of total leverage)")
    ax2.invert_yaxis()
    ax2.set_xlim(0, 65)

    fig.suptitle("Figure 7: Sensitivity Tornado Chart — Where System Speedup Comes From\n"
                 "Frontend captures 56.44% of total optimisation leverage | "
                 "October 8, 2026 empirical data",
                 fontsize=10, fontweight="bold", y=1.02)
    out = FIGS / "figure7_sensitivity_tornado.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [7] {out.name}")
    return out


# Run all generators
fig_paths = {
    "Figure 1": make_figure1(),
    "Figure 2": make_figure2(),
    "Figure 3": make_figure3(),
    "Figure 4": make_figure4(),
    "Figure 5": make_figure5(),
    "Figure 6": make_figure6(),
    "Figure 7": make_figure7(),
}
print(f"\nAll {len(fig_paths)} figures generated.\n")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE B — FIX FIGURE 7 CAPTION TYPO + EMBED ALL FIGURES
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("PHASE B — Fix caption + embed all 7 figures into docx")
print("=" * 60)

shutil.copy2(DOCX, BASE / "SPEFinal_pre_figure_embed.docx")
doc = Document(DOCX)

# Map caption text fragments → figure file
CAPTION_TO_FIG = {
    "Figure 1: Reconstructed":                  fig_paths["Figure 1"],
    "Figure 2: Layered Queueing Network":       fig_paths["Figure 2"],
    "Figure 3: Predicted Microservice Utilisa": fig_paths["Figure 3"],
    "Figure 4: Analytical Model Predictions":   fig_paths["Figure 4"],
    "Figure 5: Model-Predicted System Latency": fig_paths["Figure 5"],
    "Figure 6: Predicted System Response Time": fig_paths["Figure 6"],
    # Para 137 wrong caption "Figure 3: Sensitivity..." → also matches Figure 7
}

# Also fix the Fig 7 caption typo before embedding
CAPTION_TO_FIG_EXACT = {
    "Figure 3: Sensitivity Tornado Chart":      (fig_paths["Figure 7"], "Figure 7"),
}

body = doc._element.body
inserted = []

for i, para in enumerate(doc.paragraphs):
    txt = para.text.strip()

    # Fix typo: "Figure 3: Sensitivity..." → "Figure 7: Sensitivity..."
    for wrong, (img_path, correct_label) in CAPTION_TO_FIG_EXACT.items():
        if wrong in txt:
            # Fix the text runs
            for run in para.runs:
                if "Figure 3" in run.text and "Sensitivity" in run.text:
                    run.text = run.text.replace("Figure 3", "Figure 7", 1)
                    print(f"  Fixed caption typo at para {i}: "
                          f"'Figure 3: Sensitivity...' → 'Figure 7: Sensitivity...'")
            # Also fix in case text spans multiple runs — brute approach
            combined = "".join(r.text for r in para.runs)
            if "Figure 3: Sensitivity" in combined and para.runs:
                para.runs[0].text = combined.replace(
                    "Figure 3: Sensitivity", "Figure 7: Sensitivity", 1)
                for r in para.runs[1:]:
                    r.text = ""

            # Now insert image above this caption
            img_path_to_use = img_path
            img_para = doc.add_paragraph()
            img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = img_para.add_run()
            run.add_picture(str(img_path_to_use), width=Inches(5.5))
            para._element.addprevious(img_para._element)
            inserted.append(("Figure 7", i))
            print(f"  Embedded {img_path_to_use.name} before para {i}")
            break

    # Insert regular figures
    for caption_frag, img_path in CAPTION_TO_FIG.items():
        if caption_frag in txt:
            img_para = doc.add_paragraph()
            img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = img_para.add_run()
            run.add_picture(str(img_path), width=Inches(5.5))
            para._element.addprevious(img_para._element)
            inserted.append((caption_frag[:20], i))
            print(f"  Embedded {img_path.name} before para {i}")
            break

print(f"\nTotal figures embedded: {len(inserted)}")
for label, idx in inserted:
    print(f"  {label}  (above para {idx})")

# Save
doc.save(DOCX)
print(f"\n✅  Saved: {DOCX.name}")

# Sync course docx
shutil.copy2(DOCX, COURSE_DOCX)
print(f"✅  Synced: {COURSE_DOCX.name}")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE C — Re-export PDF
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("PHASE C — Re-export PDF")
print("=" * 60)

try:
    import win32com.client
    pdf_path = str(BASE / "SPEFinal_final.pdf")
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    d = word.Documents.Open(str(DOCX), ReadOnly=False)
    d.ExportAsFixedFormat(pdf_path, 17, OpenAfterExport=False)
    d.Close(SaveChanges=False)
    word.Quit()
    size = Path(pdf_path).stat().st_size
    print(f"✅  PDF exported: SPEFinal_final.pdf ({size:,} bytes)")
except Exception as e:
    print(f"⚠️  PDF export via COM failed: {e}")
    print("    Please open SPEFinal.docx in Word and export manually.")

print("\nDONE. Run 'python scripts/full_docx_audit.py' to verify.")
