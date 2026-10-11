"""
embed_new_figures_into_report.py
=================================
Appends the two new Oct-8 deliverable figures into SPEFinal.docx as a new
'Section 8: Multi-Tier Validation & HPA Autoscaling Policy' appendix section.

Figures added:
  1. multitier_empirical_validation.png  - Live Docker 4-tier validation curve
  2. hpa_cost_optimization.png           - Mathematical HPA policy & cost frontier
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOC_NAMES = [
    "SPEFinal.docx",
    "Software Performance Engineering Course.docx"
]
FIGURES_DIR = os.path.join(PROJECT_ROOT, "results", "figures")

FIG_MULTITIER = os.path.join(FIGURES_DIR, "multitier_empirical_validation.png")
FIG_HPA       = os.path.join(FIGURES_DIR, "hpa_cost_optimization.png")


def add_heading(doc, text, level=1, color=None):
    para = doc.add_heading(text, level=level)
    if color:
        for run in para.runs:
            run.font.color.rgb = RGBColor(*color)
    return para


def add_figure(doc, img_path, caption, width_inches=6.0):
    if not os.path.exists(img_path):
        print(f"  [SKIP] Figure not found: {img_path}")
        return
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    run.add_picture(img_path, width=Inches(width_inches))

    cap = doc.add_paragraph(caption)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.runs[0].font.size = Pt(9)
    cap.runs[0].font.italic = True
    cap.runs[0].font.color.rgb = RGBColor(80, 80, 80)
    doc.add_paragraph()  # spacing


def embed_section_8(doc_path):
    if not os.path.exists(doc_path):
        print(f"[SKIP] Document not found: {doc_path}")
        return

    print(f"Checking: {doc_path}")
    doc = Document(doc_path)

    # Check if Section 8 is already present
    already_has = any("Section 8: Multi-Tier" in p.text for p in doc.paragraphs)
    if already_has:
        print(f"  [ALREADY PRESENT] Section 8 already embedded in {os.path.basename(doc_path)}")
        return

    # Add page break before new section
    doc.add_page_break()

    # --- Section Heading ---
    add_heading(doc,
        "Section 8: Multi-Tier Live Empirical Validation & HPA Autoscaling Policy",
        level=1)

    doc.add_paragraph(
        "This section documents two additional advanced analyses completed as part of the "
        "October 8, 2026 live Docker validation run, extending the canonical baseline presented "
        "in the preceding sections."
    )

    # --- 8.1 Multi-Tier Validation ---
    add_heading(doc, "8.1  Multi-Tier Live Empirical Validation (Oct 8, 2026)", level=2)

    doc.add_paragraph(
        "The queueing network model was validated at four target arrival rates "
        "(λ ∈ {2, 5, 8, 10} req/s) against live HTTP measurements from the Google Online Boutique "
        "running inside Docker Desktop on a Windows development workstation (16 containers, shared host). "
        "Table 8.1 summarises the live telemetry results."
    )

    # Table 8.1
    table = doc.add_table(rows=5, cols=7)
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    headers = ["λ Target (req/s)", "Observed RPS", "Success Rate",
               "Mean Latency (ms)", "P95 Latency (ms)", "QN Predicted (ms)", "Gap (ms)"]
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        hdr_cells[i].paragraphs[0].runs[0].font.bold = True

    data = [
        ("2.0",  "1.64", "81.7%", "354.2",  "1,365.2", "101.5",  "+252.7"),
        ("5.0",  "4.21", "84.0%", "996.8",  "5,979.3", "139.6",  "+857.2"),
        ("8.0",  "4.60", "74.2%", "857.0",  "8,012.7", "228.5",  "+628.5"),
        ("10.0", "4.82", "72.3%", "2,887.9","8,016.4", "406.3", "+2,481.6"),
    ]
    for r_idx, row_data in enumerate(data):
        row_cells = table.rows[r_idx + 1].cells
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = val

    doc.add_paragraph()
    doc.add_paragraph(
        "Table 8.1: Live Docker multi-tier measurements vs. analytical QN model predictions. "
        "The positive gap reflects Docker Desktop for Windows host resource contention "
        "(Hyper-V/WSL2 scheduling overhead, Docker NAT bridge, shared CPU across 16 containers) "
        "which is absent in a cloud-native production deployment. The QN model service demands "
        "(S₀ = 80 ms) are calibrated to Jaeger span durations — pure in-process execution time — "
        "not external HTTP wall-clock times. Overall: WMAPE = 82.81%, R² = −0.986."
    ).runs[0].font.italic = True

    # Figure 8.1
    add_figure(doc, FIG_MULTITIER,
        "Figure 8.1: Multi-tier empirical validation curve. Left panel: analytical QN model "
        "(hockey-stick knee at λ = 12.5 req/s) vs. live Docker measurements (resource-contention "
        "inflation annotated per tier). Right panel: effective throughput ceiling at ~5 req/s "
        "due to single Windows host saturation at λ ≥ 5 req/s.",
        width_inches=6.2)

    # --- 8.2 HPA Policy ---
    add_heading(doc, "8.2  Mathematical Kubernetes HPA Autoscaling Policy", level=2)

    doc.add_paragraph(
        "Using the M/M/1 steady-state response time formula R = S₀ / (1 − ρ), the optimal "
        "Kubernetes Horizontal Pod Autoscaler (HPA) CPU utilisation target was derived analytically "
        "to guarantee the 500 ms SLA with a 30-second pod spin-up safety margin."
    )

    # HPA Policy Table
    table2 = doc.add_table(rows=4, cols=2)
    table2.style = "Table Grid"
    policy_data = [
        ("Recommended HPA CPU Target", "66.6%  (ρ* = 1 − S₀/R_target = 68.0%, × 0.98 margin)"),
        ("Per-Pod Scale-Up Trigger Rate", "8.33 req/s per replica"),
        ("Per-Pod Hard Saturation Cliff", "10.50 req/s per replica (ρ = 84%, R = 500 ms)"),
        ("Pareto-Optimal Replica Count", "c = 3 pods  |  31.5 req/s SLA capacity  |  $130.34/mo"),
    ]
    for r_idx, (param, val) in enumerate(policy_data):
        row_cells = table2.rows[r_idx].cells
        row_cells[0].text = param
        row_cells[0].paragraphs[0].runs[0].font.bold = True
        row_cells[1].text = val

    doc.add_paragraph()
    doc.add_paragraph(
        "Table 8.2: Analytically-derived HPA autoscaling policy parameters for the Online Boutique "
        "frontend microservice."
    ).runs[0].font.italic = True

    # Figure 8.2
    add_figure(doc, FIG_HPA,
        "Figure 8.2: Mathematical HPA autoscaling policy. Left panel: M/M/1 response time vs. "
        "CPU utilisation curve with the recommended 66.6% HPA trigger (purple dashed), 250 ms "
        "operational target (green) and 500 ms SLA hard limit (red). Safe zone shaded green; "
        "queueing explosion risk shaded red. Right panel: multi-replica scaling frontier — "
        "capacity (bars) and monthly infrastructure cost (line) for c = 1…5 pods, "
        "with Pareto-optimal c = 3 annotated.",
        width_inches=6.2)

    # Save
    doc.save(doc_path)
    print(f"[SUCCESS] Embedded Section 8 with 2 new figures into: {doc_path}")


def main():
    for name in DOC_NAMES:
        path = os.path.join(PROJECT_ROOT, name)
        embed_section_8(path)


if __name__ == "__main__":
    main()
