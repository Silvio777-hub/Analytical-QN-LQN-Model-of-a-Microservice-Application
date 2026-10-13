"""
generate_presentation.py
========================
Generates a professional widescreen PowerPoint presentation (16:9)
for the SPE Final Project defense / viva.

Updated with canonical October 8, 2026 reconciled empirical data:
  - 6,642 spans across 687 traces (authoritative Jaeger telemetry)
  - Frontend exclusive CPU demand S₀ = 18.88 ms (13.43× demand imbalance)
  - Single-replica capacity ceiling X₁ = 52.97 req/s
  - Multi-tier live validation: WMAPE = 82.81%, R² = −0.986 across 4 tiers
  - Horizontal scaling: c = 3 replicas expands capacity to 148.75 req/s (93.6% USL)
  - Sensitivity analysis: Frontend captures 56.44% of total optimization ROI
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# Professional Color Palette
BG_DARK = RGBColor(15, 23, 42)        # Navy Slate (#0F172A)
BG_LIGHT = RGBColor(248, 249, 250)    # Clean Off-White (#F8F9FA)
PRIMARY = RGBColor(27, 42, 74)        # Deep Corporate Navy (#1B2A4A)
SECONDARY = RGBColor(71, 85, 105)     # Slate Muted (#475569)
ACCENT_BLUE = RGBColor(14, 116, 144)  # Deep Cyan (#0E7490)
ACCENT_CYAN = RGBColor(6, 182, 212)   # Bright Cyan (#06B6D4)
CARD_BG = RGBColor(255, 255, 255)     # Pure White
CARD_BORDER = RGBColor(226, 232, 240) # Light Border (#E2E8F0)
TEXT_DARK = RGBColor(15, 23, 42)
TEXT_MUTED = RGBColor(100, 116, 139)
HIGHLIGHT_GREEN = RGBColor(16, 185, 129)
HIGHLIGHT_AMBER = RGBColor(245, 158, 11)


def add_header(slide, title_text, category_text="SOFTWARE PERFORMANCE ENGINEERING"):
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.73), Inches(0.9))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = ACCENT_BLUE
    
    p_title = tf.add_paragraph()
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = PRIMARY
    p_title.space_before = Pt(2)


def add_card(slide, left, top, width, height, bg=CARD_BG, border=CARD_BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg
    shape.line.color.rgb = border
    shape.line.width = Pt(1.5)
    return shape


# ==========================================
# SLIDE 1: Title Slide (Dark Theme)
# ==========================================
slide1 = prs.slides.add_slide(blank_layout)
bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = BG_DARK
bg1.line.fill.background()

tb1 = slide1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(10.933), Inches(4.5))
tf1 = tb1.text_frame
tf1.word_wrap = True

p1_sub = tf1.paragraphs[0]
p1_sub.text = "RESEARCH & TECHNICAL REPORT DEFENSE • ACADEMIC YEAR 2025–2026"
p1_sub.font.size = Pt(12)
p1_sub.font.bold = True
p1_sub.font.color.rgb = ACCENT_CYAN

p1_title = tf1.add_paragraph()
p1_title.text = "Analytical Queueing Network Modeling\nof a Polyglot Microservice Application"
p1_title.font.size = Pt(36)
p1_title.font.bold = True
p1_title.font.color.rgb = RGBColor(255, 255, 255)
p1_title.space_before = Pt(12)
p1_title.space_after = Pt(16)

p1_desc = tf1.add_paragraph()
p1_desc.text = "Capacity Planning, Scalability Limits & Bottleneck Analysis on Google Online Boutique"
p1_desc.font.size = Pt(18)
p1_desc.font.color.rgb = RGBColor(203, 213, 225)
p1_desc.space_after = Pt(28)

p1_meta = tf1.add_paragraph()
p1_meta.text = "Author: Janneh Silvio  |  Telemetry: Jaeger, Prometheus, OpenTelemetry (Oct 8, 2026 Live Dataset)"
p1_meta.font.size = Pt(13)
p1_meta.font.color.rgb = ACCENT_CYAN


# ==========================================
# SLIDE 2: Executive Summary & Core Results
# ==========================================
slide2 = prs.slides.add_slide(blank_layout)
add_header(slide2, "Executive Summary: Analytical Modeling vs. Trial-and-Error", "Project Overview")

stats = [
    ("Sole Bottleneck", "Frontend Gateway", "18.88 ms CPU (13.43× imbalance)", HIGHLIGHT_AMBER),
    ("Optimal Scaling", "c = 3 Replicas", "148.75 req/s at 93.6% USL eff.", HIGHLIGHT_GREEN),
    ("Capacity Ceiling", "52.97 req/s", "Single-pod saturation limit", ACCENT_BLUE),
    ("Optimization ROI", "56.44% in Gateway", "1.52 ms/ms speedup leverage", PRIMARY),
]

for i, (label, val, sub, col) in enumerate(stats):
    left = Inches(0.8 + i * 2.98)
    card = add_card(slide2, left, Inches(1.5), Inches(2.8), Inches(1.5))
    tb = slide2.shapes.add_textbox(left + Inches(0.15), Inches(1.6), Inches(2.5), Inches(1.3))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.text = label.upper()
    p0.font.size = Pt(10)
    p0.font.bold = True
    p0.font.color.rgb = TEXT_MUTED
    
    p1 = tf.add_paragraph()
    p1.text = val
    p1.font.size = Pt(17)
    p1.font.bold = True
    p1.font.color.rgb = col
    
    p2 = tf.add_paragraph()
    p2.text = sub
    p2.font.size = Pt(11)
    p2.font.color.rgb = SECONDARY

left_card = add_card(slide2, Inches(0.8), Inches(3.2), Inches(5.75), Inches(3.7))
tb_lc = slide2.shapes.add_textbox(Inches(1.0), Inches(3.4), Inches(5.35), Inches(3.3))
tf_lc = tb_lc.text_frame
tf_lc.word_wrap = True

p_lc_h = tf_lc.paragraphs[0]
p_lc_h.text = "The Problem with Physical Load Testing"
p_lc_h.font.size = Pt(16)
p_lc_h.font.bold = True
p_lc_h.font.color.rgb = PRIMARY

points_l = [
    ("Cost & Footprint: ", "Running multi-hour cluster sweeps consumes substantial cloud budget and developer hours."),
    ("Noise & Shared Host Contention: ", "Container scheduling jitter and virtual network bridging mask fundamental architectural capacity."),
    ("Non-Predictive: ", "Physical tests reveal failure points after the fact, but cannot evaluate arbitrary scaling topologies instantaneously.")
]
for bold_prefix, text in points_l:
    p = tf_lc.add_paragraph()
    p.space_before = Pt(8)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix
    r1.font.bold = True
    r1.font.size = Pt(13)
    r1.font.color.rgb = TEXT_DARK
    r2 = p.add_run()
    r2.text = text
    r2.font.size = Pt(13)
    r2.font.color.rgb = SECONDARY

right_card = add_card(slide2, Inches(6.78), Inches(3.2), Inches(5.75), Inches(3.7))
tb_rc = slide2.shapes.add_textbox(Inches(6.98), Inches(3.4), Inches(5.35), Inches(3.3))
tf_rc = tb_rc.text_frame
tf_rc.word_wrap = True

p_rc_h = tf_rc.paragraphs[0]
p_rc_h.text = "The Analytical Queueing Solution"
p_rc_h.font.size = Pt(16)
p_rc_h.font.bold = True
p_rc_h.font.color.rgb = PRIMARY

points_r = [
    ("Mathematical Foundations: ", "Combines Open Jackson Queueing Networks (M/M/1, M/M/c) and Layered Queueing Networks (LQN)."),
    ("Instantaneous Evaluation: ", "Evaluates end-to-end response times, queue lengths, and pod saturation bounds in sub-millisecond compute time."),
    ("Precision Engineering ROI: ", "Identifies that 56.4% of system speedup ROI is concentrated in Frontend, with ProductCatalog (23.8%) secondary.")
]
for bold_prefix, text in points_r:
    p = tf_rc.add_paragraph()
    p.space_before = Pt(8)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix
    r1.font.bold = True
    r1.font.size = Pt(13)
    r1.font.color.rgb = TEXT_DARK
    r2 = p.add_run()
    r2.text = text
    r2.font.size = Pt(13)
    r2.font.color.rgb = SECONDARY


# ==========================================
# SLIDE 3: Benchmark Architecture & Telemetry
# ==========================================
slide3 = prs.slides.add_slide(blank_layout)
add_header(slide3, "System Topology & Empirical Telemetry Capture", "Google Online Boutique")

card3 = add_card(slide3, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
tb3 = slide3.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf3 = tb3.text_frame
tf3.word_wrap = True

p3_h = tf3.paragraphs[0]
p3_h.text = "Empirical Tracing Ground Truth"
p3_h.font.size = Pt(16)
p3_h.font.bold = True
p3_h.font.color.rgb = PRIMARY

points3 = [
    ("Benchmark: ", "Google Online Boutique (11 polyglot microservices: Go, Node.js, C#, Python, Java, C Redis) deployed in containers."),
    ("Workload Generation: ", "Locust load generator executing realistic user session transactions at target arrival rates."),
    ("Authoritative Archive: ", "6,642 spans captured across 687 traces during the authoritative live test on October 8, 2026."),
    ("Instrumentation: ", "Jaeger distributed tracing + Prometheus counter snapshots for container metrics and traffic topology reconstruction."),
    ("Empirical Coverage: ", "All 10 microservices measured directly from distributed traces; Redis state store parameterized at standard 2.0 ms baseline.")
]
for bold_prefix, text in points3:
    p = tf3.add_paragraph()
    p.space_before = Pt(10)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = TEXT_DARK
    r2 = p.add_run()
    r2.text = text
    r2.font.size = Pt(12)
    r2.font.color.rgb = SECONDARY

fig1_path = os.path.abspath("results/figures/figure1_reconstructed_call_graph.png")
if os.path.exists(fig1_path):
    slide3.shapes.add_picture(fig1_path, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))


# ==========================================
# SLIDE 4: Mathematical Formulation & LQN
# ==========================================
slide4 = prs.slides.add_slide(blank_layout)
add_header(slide4, "Analytical Modeling: Open Jackson QN & LQN Demarcation", "Mathematical Foundation")

card4 = add_card(slide4, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
tb4 = slide4.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf4 = tb4.text_frame
tf4.word_wrap = True

p4_h = tf4.paragraphs[0]
p4_h.text = "The LQN Demand Demarcation Principle"
p4_h.font.size = Pt(16)
p4_h.font.bold = True
p4_h.font.color.rgb = PRIMARY

p_lqn_exp = tf4.add_paragraph()
p_lqn_exp.text = "Classical Jackson QNs assume pure server execution. In microservices, upstream gateways block synchronously awaiting downstream gRPC calls."
p_lqn_exp.font.size = Pt(12)
p_lqn_exp.font.color.rgb = SECONDARY
p_lqn_exp.space_before = Pt(6)

points4 = [
    ("LQN Demarcation Formula: ", "S_i = R_gross − Σ (V_i,j · R_child,j)\nIsolates pure in-process CPU computation (Frontend S₀ = 18.88 ms) from child wait time."),
    ("Traffic Inversion: ", "λ = (I − Pᵀ)⁻¹ · λ_ext\nSolves internal microservice visit ratios from transition probability matrix P."),
    ("M/M/1 Residence Time: ", "R_i = S_i / (1 − ρ_i), where ρ_i = λ_i · S_i\nCaptures non-linear queueing explosion as server utilisation approaches 1.0."),
    ("Analytical System Response: ", "R_sys = Σ (V_i · R_i) = 23.27 ms (uncontended theoretical floor at λ₀ = 10 req/s).")
]
for bold_prefix, text in points4:
    p = tf4.add_paragraph()
    p.space_before = Pt(8)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = TEXT_DARK
    r2 = p.add_run()
    r2.text = text
    r2.font.size = Pt(12)
    r2.font.color.rgb = SECONDARY

fig2_path = os.path.abspath("results/figures/figure2_lqn_three_tier_architecture.png")
if os.path.exists(fig2_path):
    slide4.shapes.add_picture(fig2_path, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))


# ==========================================
# SLIDE 5: Service Demands Table
# ==========================================
slide5 = prs.slides.add_slide(blank_layout)
add_header(slide5, "Empirical Parameterization: All 11 Microservices", "Model Parameters")

rows, cols = 12, 6
left, top, width, height = Inches(0.8), Inches(1.5), Inches(11.73), Inches(5.3)
table_shape = slide5.shapes.add_table(rows, cols, left, top, width, height)
tbl = table_shape.table

headers = ["Microservice", "Language", "Visit Ratio (Vᵢ)", "Demand (Sᵢ)", "Total Demand (Dᵢ)", "Empirical Telemetry Source"]
col_widths = [Inches(2.5), Inches(1.1), Inches(1.5), Inches(1.3), Inches(1.6), Inches(3.73)]
for j, w in enumerate(col_widths):
    tbl.columns[j].width = w

for j, h in enumerate(headers):
    cell = tbl.cell(0, j)
    cell.text = h
    cell.fill.solid()
    cell.fill.fore_color.rgb = PRIMARY
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)

table_data = [
    ("Frontend (Gateway)", "Go", "1.0000", "18.88 ms", "18.88 ms", "Jaeger live traces (2,386 samples, BOTTLENECK)"),
    ("CartService", "C#", "0.0399", "35.23 ms", "1.41 ms", "Jaeger live traces (221 samples)"),
    ("CheckoutService", "Go", "0.0367", "33.52 ms", "1.23 ms", "Jaeger live traces (992 samples)"),
    ("CurrencyService", "Node.js", "0.2771", "1.60 ms", "0.44 ms", "Jaeger live traces (564 samples)"),
    ("AdService", "Java", "0.0218", "19.88 ms", "0.43 ms", "Jaeger live traces (79 samples)"),
    ("RecommendationService", "Python", "0.0898", "3.83 ms", "0.34 ms", "Jaeger live traces (404 samples)"),
    ("PaymentService", "Node.js", "0.0051", "47.94 ms", "0.24 ms", "Jaeger live traces (96 samples)"),
    ("ProductCatalogService", "Go", "0.6369", "0.32 ms", "0.21 ms", "Jaeger live traces (1,574 samples)"),
    ("ShippingService", "Go", "0.0142", "13.45 ms", "0.19 ms", "Jaeger live traces (131 samples)"),
    ("Redis State Store", "C", "0.0379", "2.00 ms", "0.08 ms", "Operational baseline (CartService cache target)"),
    ("EmailService", "Python", "0.0051", "1.29 ms", "0.01 ms", "Jaeger live traces (95 samples)"),
]

for i, row in enumerate(table_data):
    for j, val in enumerate(row):
        cell = tbl.cell(i + 1, j)
        cell.text = val
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(241, 245, 249) if i % 2 == 0 else RGBColor(255, 255, 255)
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(10)
            if j == 0 and "Frontend" in val:
                p.font.bold = True
                p.font.color.rgb = HIGHLIGHT_AMBER
            elif j == 3 and "18.88" in val:
                p.font.bold = True
                p.font.color.rgb = PRIMARY
            else:
                p.font.color.rgb = TEXT_DARK


# ==========================================
# SLIDE 6: Bottleneck Identification
# ==========================================
slide6 = prs.slides.add_slide(blank_layout)
add_header(slide6, "Bottleneck Identification: The 13.43× Demand Imbalance", "System Analysis")

card6 = add_card(slide6, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
tb6 = slide6.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf6 = tb6.text_frame
tf6.word_wrap = True

p6_h = tf6.paragraphs[0]
p6_h.text = "The Bottleneck Law in Action"
p6_h.font.size = Pt(16)
p6_h.font.bold = True
p6_h.font.color.rgb = PRIMARY

points6 = [
    ("Bottleneck Law: ", "λ_sat = 1 / max_i(D_i) = 1 / 0.01888 s = 52.97 req/s.\nA single pod cannot exceed 52.97 req/s regardless of backend sizing."),
    ("13.43× Demand Divergence: ", "Frontend CPU demand is 18.88 ms; second-heaviest service is CartService at 1.41 ms."),
    ("CPU Utilization at Nominal 10 req/s: ", "• Frontend CPU = 18.88%\n• CartService CPU = 1.41%\n• All other 9 backends operate at < 0.50% CPU."),
    ("Platform Engineering Insight: ", "Backend microservices have negligible CPU saturation. Tuning backend services yields negligible system gain until Frontend is horizontally scaled.")
]
for bold_prefix, text in points6:
    p = tf6.add_paragraph()
    p.space_before = Pt(10)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = TEXT_DARK
    r2 = p.add_run()
    r2.text = text
    r2.font.size = Pt(12)
    r2.font.color.rgb = SECONDARY

fig3_path = os.path.abspath("results/figures/figure3_utilisation_spectrum.png")
if os.path.exists(fig3_path):
    slide6.shapes.add_picture(fig3_path, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))


# ==========================================
# SLIDE 7: Model Validation & Error Analysis
# ==========================================
slide7 = prs.slides.add_slide(blank_layout)
add_header(slide7, "Model Validation: Multi-Tier Comparison & Honest Error Analysis", "Empirical Validation")

card7 = add_card(slide7, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
tb7 = slide7.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf7 = tb7.text_frame
tf7.word_wrap = True

p7_h = tf7.paragraphs[0]
p7_h.text = "Rigorous Multi-Tier Validation"
p7_h.font.size = Pt(16)
p7_h.font.bold = True
p7_h.font.color.rgb = PRIMARY

points7 = [
    ("4 Empirical Tiers Tested: ", "Evaluated at λ ∈ {2.0, 5.0, 8.0, 10.0} req/s in Docker Desktop cluster under live Locust load."),
    ("Validation Metrics: ", "Weighted Mean Absolute Percentage Error (WMAPE) = 82.81%, R² = −0.986 across the 4 workload tiers."),
    ("Physical Source of Divergence: ", "Single-host Docker Desktop resource contention (WSL2 scheduling jitter, NAT bridging, 16 co-located containers) saturates near 5 req/s."),
    ("Academic Honesty: ", "Unlike simulated reports claiming 98% accuracy, we transparently publish the gap between uncontended queueing theory and shared-host virtualization limits.")
]
for bold_prefix, text in points7:
    p = tf7.add_paragraph()
    p.space_before = Pt(10)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = TEXT_DARK
    r2 = p.add_run()
    r2.text = text
    r2.font.size = Pt(12)
    r2.font.color.rgb = SECONDARY

fig4_path = os.path.abspath("results/figures/figure4_predictions_vs_measurements.png")
if os.path.exists(fig4_path):
    slide7.shapes.add_picture(fig4_path, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))


# ==========================================
# SLIDE 8: Load Sweep & 500ms SLA Knee
# ==========================================
slide8 = prs.slides.add_slide(blank_layout)
add_header(slide8, "Traffic Load Sweep: Non-Linear Knee & 500 ms SLA Breach", "Capacity Limits")

card8 = add_card(slide8, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
tb8 = slide8.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf8 = tb8.text_frame
tf8.word_wrap = True

p8_h = tf8.paragraphs[0]
p8_h.text = "The Hockey-Stick Queueing Curve"
p8_h.font.size = Pt(16)
p8_h.font.bold = True
p8_h.font.color.rgb = PRIMARY

points8 = [
    ("Arrival Rate Sweep: ", "Evaluated theoretical throughput curve from λ₀ = 0 to 52.97 req/s for a single Frontend pod."),
    ("Uncontended Region (0–20 req/s): ", "Response times remain sub-35 ms, with Frontend CPU under 38%."),
    ("Nominal Baseline (10 req/s): ", "Frontend CPU = 18.88%, theoretical uncontended latency R = 23.27 ms."),
    ("500 ms SLA Breach Boundary: ", "Uncontended M/M/1 model reaches 500 ms SLA boundary above 50 req/s as ρ → 1.0."),
    ("Single-Pod Asymptotic Ceiling: ", "Hard physical limit at λ_sat = 52.97 req/s; requires multi-pod replication for higher throughput.")
]
for bold_prefix, text in points8:
    p = tf8.add_paragraph()
    p.space_before = Pt(10)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = TEXT_DARK
    r2 = p.add_run()
    r2.text = text
    r2.font.size = Pt(12)
    r2.font.color.rgb = SECONDARY

fig5_path = os.path.abspath("results/figures/figure5_hockey_stick_knee_curve.png")
if os.path.exists(fig5_path):
    slide8.shapes.add_picture(fig5_path, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))


# ==========================================
# SLIDE 9: Horizontal Scaling (M/M/c & USL)
# ==========================================
slide9 = prs.slides.add_slide(blank_layout)
add_header(slide9, "Autoscaling Optimization: M/M/c & Universal Scalability Law", "Horizontal Scaling")

card9 = add_card(slide9, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
tb9 = slide9.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf9 = tb9.text_frame
tf9.word_wrap = True

p9_h = tf9.paragraphs[0]
p9_h.text = "The c = 3 Replicas Sweet Spot"
p9_h.font.size = Pt(16)
p9_h.font.bold = True
p9_h.font.color.rgb = PRIMARY

points9 = [
    ("Erlang-C Multi-Server Model: ", "At λ₀ = 10 req/s, deploying c = 3 Frontend pods reduces queueing probability to C(3, 0.1888) = 0.11%."),
    ("Residence Time Near Physical Floor: ", "Frontend residence drops to 18.89 ms at c = 3, virtually eliminating queue wait times."),
    ("Gunther's USL Capacity Model: ", "With contention σ = 0.0248 and coherency κ = 0.0031:\n• c = 3 capacity = 148.75 req/s (2.81× capacity expansion)\n• Scaling efficiency = 93.6%."),
    ("Diminishing Marginal Gains: ", "Beyond c = 3, USL efficiency degrades (c = 6 yields 82.2% efficiency with minimal additional latency improvement).")
]
for bold_prefix, text in points9:
    p = tf9.add_paragraph()
    p.space_before = Pt(8)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = TEXT_DARK
    r2 = p.add_run()
    r2.text = text
    r2.font.size = Pt(12)
    r2.font.color.rgb = SECONDARY

fig6_path = os.path.abspath("results/figures/figure6_multi_replica_scaling.png")
if os.path.exists(fig6_path):
    slide9.shapes.add_picture(fig6_path, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))


# ==========================================
# SLIDE 10: Sensitivity Analysis & ROI
# ==========================================
slide10 = prs.slides.add_slide(blank_layout)
add_header(slide10, "Sensitivity Analysis: Engineering Return on Investment (ROI)", "Optimization Leverage")

card10 = add_card(slide10, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
tb10 = slide10.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf10 = tb10.text_frame
tf10.word_wrap = True

p10_h = tf10.paragraphs[0]
p10_h.text = "Where Should Developers Spend Time?"
p10_h.font.size = Pt(16)
p10_h.font.bold = True
p10_h.font.color.rgb = PRIMARY

points10 = [
    ("Sensitivity Derivative: ", "∂R_sys / ∂S_i = V_i / (1 − ρ_i)²\nQuantifies end-to-end latency eliminated per 1 ms saved in service demand S_i."),
    ("Frontend Primary Leverage: ", "∂R/∂S₀ = 1.5197 ms/ms. Frontend captures 56.44% of all system performance optimization leverage."),
    ("Substantial Secondary Leverage: ", "ProductCatalogService (V = 0.637) captures 23.76% of ROI; CurrencyService captures 10.39%."),
    ("Targeted Engineering Focus: ", "Top 3 services account for over 90% of optimization impact; remaining 8 microservices combine for < 10% ROI.")
]
for bold_prefix, text in points10:
    p = tf10.add_paragraph()
    p.space_before = Pt(8)
    r1 = p.add_run()
    r1.text = "• " + bold_prefix
    r1.font.bold = True
    r1.font.size = Pt(12)
    r1.font.color.rgb = TEXT_DARK
    r2 = p.add_run()
    r2.text = text
    r2.font.size = Pt(12)
    r2.font.color.rgb = SECONDARY

fig7_path = os.path.abspath("results/figures/figure7_sensitivity_tornado.png")
if os.path.exists(fig7_path):
    slide10.shapes.add_picture(fig7_path, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))


# ==========================================
# SLIDE 11: Sources of Error & Limitations
# ==========================================
slide11 = prs.slides.add_slide(blank_layout)
add_header(slide11, "Sources of Error, Assumptions & Honest Limitations", "Methodological Rigor")

items11 = [
    ("1. Shared Host Docker Contention", "16 containers sharing one WSL2 VM and network bridge causes high tail inflation (WMAPE = 82.81%), contrasting with uncontended cloud execution."),
    ("2. High Empirical Variance (CoV > 2.0)", "Services exhibit high coefficient of variation (Frontend CoV = 19.05, ProductCatalog = 29.44) due to scheduling jitter; M/M/1 acts as analytical baseline."),
    ("3. Telemetry Truncation Artifacts", "At λ = 8.0 req/s, success rate dropped to 74.2%, causing slower requests to time out and truncating the observed mean latency."),
    ("4. Synchronous RPC Call Trees", "Gateway goroutines block waiting for child gRPC calls; LQN demarcation separates pure CPU computation from child wait times."),
    ("5. Redis State Store Defaulting", "Redis Cart cache operates at default 2.0 ms baseline; accounted for via visit ratio routing from CartService (0.95 probability)."),
    ("6. Measurement Statistical Confidence", "Authoritative run captures 6,642 spans across 687 traces, providing statistically robust empirical service distributions.")
]

for idx, (title, desc) in enumerate(items11):
    col = idx % 2
    row = idx // 2
    x = Inches(0.8 + col * 5.98)
    y = Inches(1.5 + row * 1.85)
    
    card = add_card(slide11, x, y, Inches(5.75), Inches(1.7))
    tb = slide11.shapes.add_textbox(x + Inches(0.15), y + Inches(0.1), Inches(5.45), Inches(1.5))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = PRIMARY
    
    p1 = tf.add_paragraph()
    p1.text = desc
    p1.font.size = Pt(11)
    p1.font.color.rgb = SECONDARY
    p1.space_before = Pt(4)


# ==========================================
# SLIDE 12: Actionable Platform Recommendations
# ==========================================
slide12 = prs.slides.add_slide(blank_layout)
add_header(slide12, "Actionable Platform Engineering Recommendations", "Production Implementation")

recs = [
    ("1. Horizontally Scale Frontend to c = 3 Replicas", "Sweet Spot", "Expands capacity from 52.97 to 148.75 req/s (2.81× expansion) at 93.6% USL efficiency, driving queueing delay under 0.11%."),
    ("2. Optimize High-ROI Services (Frontend, Catalog, Currency)", "ROI: 90.6%", "Concentrate software profiling on Frontend (56.4% ROI), ProductCatalog (23.8%), and Currency (10.4%) to eliminate cascading latency."),
    ("3. Configure Kubernetes HPA Target at ρ* = 66.7% CPU", "HPA Policy", "Set target CPU utilization to 66.7% (scale-up trigger at 8.33 req/s/replica) to prevent queue explosion before the 500 ms SLA threshold."),
    ("4. Add Percentile-Based Latency Alerting (P95/P99)", "Observability", "Tail latency amplification occurs before average CPU spikes; early P95 alerting prevents cascading connection timeouts."),
    ("5. Isolate High-Traffic Workloads in Dedicated Node Pools", "Platform", "Prevent shared-host CPU and network contention by separating gateway and storage tiers from compute-heavy ML backends.")
]

for idx, (title, badge, desc) in enumerate(recs):
    y = Inches(1.45 + idx * 1.12)
    card = add_card(slide12, Inches(0.8), y, Inches(11.73), Inches(1.02))
    tb = slide12.shapes.add_textbox(Inches(1.0), y + Inches(0.08), Inches(11.33), Inches(0.85))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    r_t = p0.add_run()
    r_t.text = title + "  "
    r_t.font.bold = True
    r_t.font.size = Pt(14)
    r_t.font.color.rgb = PRIMARY
    
    r_b = p0.add_run()
    r_b.text = f"[{badge}]"
    r_b.font.bold = True
    r_b.font.size = Pt(12)
    r_b.font.color.rgb = ACCENT_BLUE
    
    p1 = tf.add_paragraph()
    p1.text = desc
    p1.font.size = Pt(12)
    p1.font.color.rgb = SECONDARY
    p1.space_before = Pt(3)


# ==========================================
# SLIDE 13: Conclusion Slide (Dark Theme)
# ==========================================
slide13 = prs.slides.add_slide(blank_layout)
bg13 = slide13.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg13.fill.solid()
bg13.fill.fore_color.rgb = BG_DARK
bg13.line.fill.background()

tb13 = slide13.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.333), Inches(4.5))
tf13 = tb13.text_frame
tf13.word_wrap = True

p13_cat = tf13.paragraphs[0]
p13_cat.text = "CONCLUSION • SOFTWARE PERFORMANCE ENGINEERING"
p13_cat.font.size = Pt(12)
p13_cat.font.bold = True
p13_cat.font.color.rgb = ACCENT_CYAN

p13_h = tf13.add_paragraph()
p13_h.text = "Analytical Models Bridge Telemetry\nand Architectural Decisions"
p13_h.font.size = Pt(32)
p13_h.font.bold = True
p13_h.font.color.rgb = RGBColor(255, 255, 255)
p13_h.space_before = Pt(12)
p13_h.space_after = Pt(14)

p13_body = tf13.add_paragraph()
p13_body.text = "• Jackson QN and LQN models provide instantaneous capacity forecasts that physical tests cannot match.\n• Telemetry demarcation isolates genuine CPU bottlenecks from synchronous child-RPC blocking.\n• Sensitivity analysis guarantees that developer effort is concentrated where 56.4% of user value is realized.\n• Combining analytical queueing with empirical observability forms a complete, predictive SPE practice."
p13_body.font.size = Pt(15)
p13_body.font.color.rgb = RGBColor(203, 213, 225)

p13_close = tf13.add_paragraph()
p13_close.text = "Thank you! Questions & Discussion."
p13_close.font.size = Pt(18)
p13_close.font.bold = True
p13_close.font.color.rgb = ACCENT_CYAN
p13_close.space_before = Pt(24)

# Save
output_path = "SPE_2025-26_Final_Presentation_Janneh_Silvio.pptx"
prs.save(output_path)
print(f"Successfully generated presentation: {output_path}")
