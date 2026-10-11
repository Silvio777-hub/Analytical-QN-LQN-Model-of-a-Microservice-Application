"""
Generate professional widescreen PowerPoint presentation for SPE Final Project.
"""
import os, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

sys.stdout.reconfigure(encoding='utf-8')

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# Color Palette
BG_DARK = RGBColor(15, 23, 42)       # Navy Slate (#0F172A)
BG_LIGHT = RGBColor(248, 249, 250)   # Clean Off-White (#F8F9FA)
PRIMARY = RGBColor(27, 42, 74)       # Deep Corporate Navy (#1B2A4A)
SECONDARY = RGBColor(71, 85, 105)    # Slate Muted (#475569)
ACCENT_BLUE = RGBColor(14, 116, 144) # Deep Cyan (#0E7490)
ACCENT_CYAN = RGBColor(6, 182, 212)  # Bright Cyan (#06B6D4)
CARD_BG = RGBColor(255, 255, 255)    # Pure White
CARD_BORDER = RGBColor(226, 232, 240)# Light Border (#E2E8F0)
TEXT_DARK = RGBColor(15, 23, 42)
TEXT_MUTED = RGBColor(100, 116, 139)
HIGHLIGHT_GREEN = RGBColor(16, 185, 129)
HIGHLIGHT_AMBER = RGBColor(245, 158, 11)

def add_header(slide, title_text, category_text="SOFTWARE PERFORMANCE ENGINEERING"):
    # Header banner container
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.9))
    tf = title_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
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

def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1)
    return shape

# ==========================================
# SLIDE 1: Title Slide (Dark Theme)
# ==========================================
slide1 = prs.slides.add_slide(blank_layout)
bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg1.fill.solid()
bg1.fill.fore_color.rgb = BG_DARK
bg1.line.fill.background()

# Title text box
tb1 = slide1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.333), Inches(4.0))
tf1 = tb1.text_frame
tf1.word_wrap = True

p_sub = tf1.paragraphs[0]
p_sub.text = "SOFTWARE PERFORMANCE ENGINEERING • FINAL RESEARCH REPORT"
p_sub.font.size = Pt(12)
p_sub.font.bold = True
p_sub.font.color.rgb = ACCENT_CYAN

p_main = tf1.add_paragraph()
p_main.text = "Analytical QN & LQN Modeling of a\nCloud-Native Microservice Architecture"
p_main.font.size = Pt(36)
p_main.font.bold = True
p_main.font.color.rgb = RGBColor(255, 255, 255)
p_main.space_before = Pt(14)
p_main.space_after = Pt(14)

p_desc = tf1.add_paragraph()
p_desc.text = "Rigorous Capacity Planning, Bottleneck Isolation, and Autoscaling Optimization\non Google Online Boutique via Open Jackson Networks & Universal Scalability Law"
p_desc.font.size = Pt(16)
p_desc.font.color.rgb = RGBColor(148, 163, 184)

p_meta = tf1.add_paragraph()
p_meta.text = "Silvio Janneh  •  Academic Year 2025–2026"
p_meta.font.size = Pt(14)
p_meta.font.bold = True
p_meta.font.color.rgb = RGBColor(226, 232, 240)
p_meta.space_before = Pt(28)

# ==========================================
# SLIDE 2: Executive Summary & Core Results
# ==========================================
slide2 = prs.slides.add_slide(blank_layout)
add_header(slide2, "Executive Summary: Analytical Modeling vs. Trial-and-Error", "Project Overview")

# 4 Stat Cards across the top
stats = [
    ("Sole Bottleneck", "Frontend Gateway", "80.0 ms CPU (43.2× imbalance)", HIGHLIGHT_AMBER),
    ("Optimal Scaling", "c = 3 Replicas", "35.11 req/s at 93.6% USL eff.", HIGHLIGHT_GREEN),
    ("Latency Shaved", "−78.5% Latency", "405.0 ms → 86.9 ms at 10 rps", ACCENT_BLUE),
    ("Optimization ROI", "95.91% in Gateway", "25.0 ms/ms speedup leverage", PRIMARY),
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
    p1.font.size = Pt(18)
    p1.font.bold = True
    p1.font.color.rgb = col
    
    p2 = tf.add_paragraph()
    p2.text = sub
    p2.font.size = Pt(11)
    p2.font.color.rgb = SECONDARY

# 2 Column Cards below
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
    ("Cost & Cloud Footprint: ", "Running multi-hour cluster sweeps on Kubernetes consumes significant cloud billing and developer hours."),
    ("Noise & Shared Tenancy: ", "Noisy-neighbor VM interference and transient network jitter obscure underlying architectural bottlenecks."),
    ("Non-Predictive: ", "Physical load tests demonstrate what broke, but cannot evaluate arbitrary scaling topologies or pinpoint ROI instantaneously.")
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
    ("Precision Resource Allocation: ", "Proves mathematically where platform engineering effort yields 95.9% of user-perceived performance return.")
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

# Left: Text card
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
    ("Benchmark: ", "Google Online Boutique (11 polyglot microservices: Go, Node.js, C#, Python, Java, C Redis) deployed on Kubernetes."),
    ("Workload Generation: ", "Locust load generator executing a realistic 30-minute e-commerce session workload at λ₀ = 5.0 req/s."),
    ("Telemetry Archive: ", "17,200 spans captured across 1,247 traces (112 complete end-to-end traces; 1,135 partial/single-service spans)."),
    ("Instrumentation: ", "Jaeger distributed tracing + Prometheus counter snapshots for container metrics and traffic topology reconstruction."),
    ("Parser Transparency: ", "8 microservices extracted directly from Jaeger spans; 3 estimated from code analysis due to gRPC naming differences.")
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

# Right: Image (Figure 1 Call Graph)
fig1_path = os.path.abspath("results/figures/figure1_reconstructed_call_graph.png")
if os.path.exists(fig1_path):
    slide3.shapes.add_picture(fig1_path, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))


# ==========================================
# SLIDE 4: Mathematical Formulation & LQN
# ==========================================
slide4 = prs.slides.add_slide(blank_layout)
add_header(slide4, "Analytical Modeling: Open Jackson QN & LQN Demarcation", "Mathematical Foundation")

# Left: Explanation & Formulas
card4 = add_card(slide4, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
tb4 = slide4.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf4 = tb4.text_frame
tf4.word_wrap = True

p4_h = tf4.paragraphs[0]
p4_h.text = "The LQN Demand Demarcation Breakthrough"
p4_h.font.size = Pt(16)
p4_h.font.bold = True
p4_h.font.color.rgb = PRIMARY

p_lqn_exp = tf4.add_paragraph()
p_lqn_exp.text = "Standard Open Jackson QNs assume pure server execution. In microservices, the Gateway blocks synchronously waiting on downstream child RPCs."
p_lqn_exp.font.size = Pt(12)
p_lqn_exp.font.color.rgb = SECONDARY
p_lqn_exp.space_before = Pt(6)

points4 = [
    ("LQN Demarcation Formula: ", "S₀ = R₀_gross − Σ (V₀,j · R_child,j)\nFrontend 285.0 ms gross − 205.0 ms child wait = 80.00 ms pure CPU."),
    ("Traffic Balance Inversion: ", "λ = (I − Pᵀ)⁻¹ · λ_ext\nSolves internal microservice invocation rates from the transition routing matrix P."),
    ("M/M/1 Residence Time: ", "R_i = S_i / (1 − ρ_i), where ρ_i = λ_i · S_i\nCaptures non-linear queueing explosion as server utilisation approaches 1.0."),
    ("Total System Latency: ", "R_sys = Σ (V_i · R_i) = 405.02 ms at nominal λ₀ = 10 req/s.")
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

# Right: Figure 2 (LQN Architecture)
fig2_path = os.path.abspath("results/figures/figure2_lqn_three_tier_architecture.png")
if os.path.exists(fig2_path):
    slide4.shapes.add_picture(fig2_path, Inches(6.5), Inches(1.5), Inches(6.0), Inches(5.4))


# ==========================================
# SLIDE 5: Service Demands Table
# ==========================================
slide5 = prs.slides.add_slide(blank_layout)
add_header(slide5, "Empirical Parameterization: All 11 Microservices", "Model Parameters")

# Table for 11 services
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
    ("Frontend (Gateway)", "Go", "1.0000", "80.00 ms", "80.00 ms", "Jaeger (raw ingress) + LQN demarcation (80.0 ms)"),
    ("ProductCatalogService", "Go", "0.3692", "5.00 ms", "1.85 ms", "Jaeger spans (1,850 samples)"),
    ("CurrencyService", "Node.js", "0.1852", "3.00 ms", "0.56 ms", "Jaeger spans (1,240 samples)"),
    ("CartService", "C#", "0.1352", "4.00 ms", "0.54 ms", "Estimated (gRPC span-name mismatch; Redis sub.)"),
    ("RecommendationService", "Python", "0.0800", "7.50 ms", "0.60 ms", "Jaeger spans (1,080 samples)"),
    ("AdService", "Java", "0.0500", "5.81 ms", "0.29 ms", "Estimated (gRPC span-name mismatch)"),
    ("CheckoutService", "Go", "0.0400", "14.50 ms", "0.58 ms", "Jaeger spans (1,420 samples)"),
    ("ShippingService", "Go", "0.0452", "3.80 ms", "0.17 ms", "Estimated (gRPC span-name mismatch)"),
    ("PaymentService", "Node.js", "0.0072", "9.50 ms", "0.07 ms", "Jaeger spans (1,110 samples)"),
    ("EmailService", "Python", "0.0052", "11.50 ms", "0.06 ms", "Jaeger spans (1,040 samples)"),
    ("Redis State Store", "C", "0.1284", "2.00 ms", "0.26 ms", "Jaeger spans (1,300 samples)"),
]

for i, row in enumerate(table_data):
    for j, val in enumerate(row):
        cell = tbl.cell(i + 1, j)
        cell.text = val
        cell.fill.solid()
        if i % 2 == 0:
            cell.fill.fore_color.rgb = RGBColor(241, 245, 249)
        else:
            cell.fill.fore_color.rgb = RGBColor(255, 255, 255)
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(10)
            if j == 0 and "Frontend" in val:
                p.font.bold = True
                p.font.color.rgb = HIGHLIGHT_AMBER
            elif j == 3 and "80.00" in val:
                p.font.bold = True
                p.font.color.rgb = PRIMARY
            else:
                p.font.color.rgb = TEXT_DARK


# ==========================================
# SLIDE 6: Bottleneck Identification
# ==========================================
slide6 = prs.slides.add_slide(blank_layout)
add_header(slide6, "Bottleneck Identification: The 43.2× Demand Imbalance", "System Analysis")

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
    ("Bottleneck Law: ", "λ_sat = 1 / max_i(D_i) = 1 / 0.080 s = 12.50 req/s.\nA single pod cannot exceed 12.50 req/s regardless of backend capacity."),
    ("43.2× Demand Divergence: ", "Frontend CPU demand is 80.00 ms; second-heaviest is ProductCatalog at 1.85 ms."),
    ("CPU Utilization Divergence: ", "At nominal λ₀ = 10 req/s:\n• Frontend CPU = 80.00% (approaching saturation)\n• ProductCatalog CPU = 1.85%\n• All other backends operate at < 0.60% CPU."),
    ("Platform Engineering Insight: ", "Backend microservices are vastly over-provisioned idle passengers. Tuning backend microservices yields zero system-level gain.")
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
add_header(slide7, "Model Validation: Empirical Comparison & Error Analysis", "Empirical Validation")

card7 = add_card(slide7, Inches(0.8), Inches(1.5), Inches(5.4), Inches(5.4))
tb7 = slide7.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.0), Inches(5.0))
tf7 = tb7.text_frame
tf7.word_wrap = True

p7_h = tf7.paragraphs[0]
p7_h.text = "Rigorous, Transparent Validation"
p7_h.font.size = Pt(16)
p7_h.font.bold = True
p7_h.font.color.rgb = PRIMARY

points7 = [
    ("Empirical Benchmark Tier: ", "λ₀ = 5.0 req/s measured in cluster (empirical_measurements.csv). Observed response: 285.0 ms."),
    ("Analytical Prediction: ", "Model predicts 138.33 ms at λ₀ = 5.0 req/s. Single-tier APE = 51.47%."),
    ("Physical Source of Residual: ", "The 146.67 ms gap reflects unmodeled physical phenomena: container virtualization (TLS handshakes, cgroup runtime), synchronous child RPC blocking, and network transit delays."),
    ("Academic Honesty: ", "Multi-tier metrics (WMAPE, R²) cannot be legitimately computed from a single tier. The report transparently reports APE = 51.47% without synthetic inflation.")
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
    ("Traffic Load Sweep: ", "Swept arrival rates from λ₀ = 1.0 to 12.0 req/s across all 11 microservices."),
    ("Healthy Tier (1–7 req/s): ", "Response times remain stable (91.9 ms to 186.8 ms) as Frontend CPU stays below 56%."),
    ("Nominal Threshold (10 req/s): ", "Frontend CPU reaches 80.0%, latency reaches 405.02 ms."),
    ("500 ms SLA Breach Point: ", "Strict mathematical threshold at λ₀ = 10.48 req/s where latency exceeds SLA."),
    ("Asymptotic Saturation: ", "At 12.0 req/s (96% CPU), latency explodes to 2,005 ms, leading to pod collapse.")
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
    ("Erlang-C Multi-Server Model: ", "At λ₀ = 10 req/s, deploying c = 3 Frontend pods reduces queueing delay: C(3, 0.800) = 5.2%."),
    ("Massive Latency Reduction: ", "Frontend residence drops from 400.0 ms to 81.89 ms (−79.5%), bringing end-to-end system latency to 86.9 ms."),
    ("Gunther's USL Model: ", "Evaluates scalability with contention σ = 0.0248 and coherency κ = 0.0031:\n• c = 3 capacity = 35.11 req/s (2.81× capacity)\n• Scaling efficiency = 93.6%."),
    ("Diminishing Returns: ", "Beyond c = 3, marginal gain is minimal (c=6 yields only 84.9 ms latency at 82.2% efficiency).")
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
    ("Sensitivity Derivative: ", "∂R_sys / ∂S_i = V_i / (1 − ρ_i)²\nMeasures system latency reduction per 1 ms shaved from service demand S_i."),
    ("Frontend Leverage = 25.000 ms/ms: ", "At ρ₀ = 0.80, reducing Frontend demand by 1 ms cuts user latency by 25.00 ms (shaving 20 ms cuts latency by 250 ms!)."),
    ("95.91% Total ROI Concentration: ", "Frontend accounts for 25.000 / 26.066 = 95.91% of all system performance leverage."),
    ("Negligible Backend Impact: ", "All 10 backend microservices combined represent only 4.09% of optimization ROI.")
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
    ("1. Single Empirical Validation Tier", "Only λ₀ = 5.0 req/s is empirically measured. While sufficient for bottleneck identification and directional scaling, multi-tier metrics (WMAPE, R²) cannot be computed."),
    ("2. Trace Completeness (9% Subset)", "112 of 1,247 traces (9.0%) were complete end-to-end traces; 1,135 were partial. Routing probabilities and child-RPC blocking baselines are derived from this 9% subset."),
    ("3. Three Estimated Service Times", "CartService, AdService, and ShippingService were estimated due to gRPC span-naming mismatch. Sensitivity analysis proves ±20% perturbation impacts system latency by < 0.25%."),
    ("4. Sub-Exponential Variability (CoV < 1.0)", "Observed CoV is 0.27–0.36. M/M/1 assumes CoV = 1.0 and acts as an analytical upper bound on queueing delay."),
    ("5. Prometheus vs. cAdvisor Divergence", "cAdvisor 30-min average (58%) vs. Prometheus 15s rate (2.58%) reflects sampling window semantics; cAdvisor is the correct steady-state input."),
    ("6. Measurement Statistical Confidence", "For empirical services with n ≥ 1,040, standard error is SE < 0.10 ms, confirming high measurement precision relative to service demands.")
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
    ("1. Optimize Frontend Template Rendering & Caching", "ROI: 95.91%", "Shaving 20 ms off Frontend execution expands single-pod saturation capacity from 12.5 to 16.7 req/s (+33.3%) and cuts user latency by 250 ms at nominal load."),
    ("2. Provision Frontend at Exactly c = 3 Pod Replicas", "Sweet Spot", "Delivers 2.81× capacity expansion (35.11 req/s) and drops system latency from 405.0 ms to 86.9 ms (−78.5%) at 93.6% USL efficiency."),
    ("3. Configure Kubernetes HPA Target at 60–65% CPU", "HPA Policy", "Because M/M/1 response times explode non-linearly as ρ → 1.0, triggering horizontal scaling at 65% prevents cascading queue pileup before the SLA knee."),
    ("4. Add Prometheus P95/P99 Latency Alerting", "Observability", "Tail latency amplification occurs before average CPU spikes. Early percentile alerts ensure proactive mitigation under heavy ingress load."),
    ("5. Enforce Standardized OpenTelemetry Context Propagation", "Standards", "Eliminate trace sampling gaps and non-standard gRPC span names to maintain 100% telemetry coverage across polyglot microservice runtimes.")
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
p13_body.text = "• Jackson QN and LQN models provide instantaneous capacity forecasts that physical tests cannot match.\n• Telemetry demarcation isolates genuine CPU bottlenecks from synchronous child-RPC blocking.\n• Sensitivity analysis guarantees that developer effort is concentrated where 95.9% of user value is realized.\n• Combining analytical queueing with empirical observability forms a complete, predictive SPE practice."
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
