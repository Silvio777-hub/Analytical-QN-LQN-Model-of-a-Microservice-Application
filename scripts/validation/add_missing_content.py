import argparse
import os
from pathlib import Path
from docx import Document
from docx.shared import Inches

# Hard‑coded missing content definitions
MISSING_FIGURES = [
    ("Figure 1", "Reconstructed Microservice Call Graph for Google Online Boutique", "fig_1_call_graph.png"),
    ("Figure 2", "Layered Queueing Network (LQN) Three‑Tier Architecture", "fig_2_lqn_arch.png"),
    ("Figure 3", "Microservice Utilisation Spectrum at 10 req/s Nominal Load", "fig_3_utilisation.png"),
    ("Figure 4", "Analytical Model Predictions vs. Real‑World Kubernetes Benchmark Measurements", "fig_4_predictions_vs_measurements.png"),
    ("Figure 5", "System Latency Hockey‑Stick Knee Curve and 500 ms SLA Boundary", "fig_5_hockey_stick.png"),
    ("Figure 6", "System Response Time Under Multi‑Replica Frontend Scaling (c = 1 to 6)", "fig_6_scaling.png"),
    ("Figure 7", "Sensitivity Tornado Chart: Where System Speedup Comes From", "fig_7_tornado.png"),
]

MISSING_TABLES = [
    ("Table 1", "Concept, Symbol, Definition, and Everyday Analogy"),
    ("Table 2", "Open Jackson QN vs. Layered Queueing Network (LQN) Architecture"),
    ("Table 3", "Queueing Model Foundational Parameters"),
    ("Table 4", "Online Boutique Microservices Runtime, Protocol, and Architectural Role"),
    ("Table 8", "M/M/c Horizontal Pod Autoscaling Performance & USL Efficiency"),
    ("Table 9", "Sensitivity Analysis & Engineering Optimization Priority Ranking"),
    ("Table 10", "Technical Glossary of Core Queueing and Performance Terms"),
    ("Table 11", "Comprehensive Mathematical Formulas Reference Matrix"),
    ("Table 12", "Architectural and Operational Benchmark Constants"),
]


def insert_image(paragraph, image_path, width_inches=6):
    run = paragraph.add_run()
    run.add_picture(str(image_path), width=Inches(width_inches))


def add_missing_content(doc_path: Path, figures_dir: Path, tables_dir: Path = None):
    doc = Document(str(doc_path))
    # Insert missing figures after a placeholder if exists, else at end
    placeholder_idx = None
    for i, para in enumerate(doc.paragraphs):
        if "{{MISSING_FIGURES}}" in para.text:
            placeholder_idx = i
            para.text = para.text.replace("{{MISSING_FIGURES}}", "")
            break
    # Insert figures
    for fig_title, fig_desc, fig_file in MISSING_FIGURES:
        img_path = figures_dir / fig_file
        if not img_path.is_file():
            # Skip if the image file does not exist – insert a note instead
            note = f"[Missing image: {fig_file}]"
            if placeholder_idx is not None:
                doc.paragraphs[placeholder_idx].insert_paragraph_before(note)
                placeholder_idx += 1
            else:
                doc.add_paragraph(note)
            continue
        # Create a new paragraph for the image
        if placeholder_idx is not None:
            p = doc.paragraphs[placeholder_idx].insert_paragraph_before()
            placeholder_idx += 1
        else:
            p = doc.add_paragraph()
        insert_image(p, img_path)
        # Caption
        caption = f"{fig_title}: {fig_desc}"
        doc.add_paragraph(caption)

    # Insert a heading for tables
    doc.add_paragraph("Missing Tables (placeholders added)", style="Heading 2")
    for tbl_title, tbl_desc in MISSING_TABLES:
        # If a tables directory with images is supplied, try to embed the image
        tbl_img = None
        if tables_dir:
            possible = tables_dir / f"{tbl_title.replace(' ', '_').lower()}.png"
            if possible.is_file():
                tbl_img = possible
        if tbl_img:
            p = doc.add_paragraph()
            insert_image(p, tbl_img)
            doc.add_paragraph(f"{tbl_title}: {tbl_desc}")
        else:
            # Insert a placeholder paragraph describing the missing table
            doc.add_paragraph(f"{tbl_title}: {tbl_desc} – (Table content to be added here)")

    doc.save(str(doc_path))
    print(f"Added missing figures/tables to {doc_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Add missing figures and tables to DOCX reports.")
    parser.add_argument("docs", nargs="+", help="Paths to DOCX files to modify.")
    parser.add_argument("--figures", required=True, help="Directory containing figure PNG files.")
    parser.add_argument("--tables", help="Optional directory containing table PNG files.")
    args = parser.parse_args()
    figs_dir = Path(args.figures)
    tbls_dir = Path(args.tables) if args.tables else None
    for doc_path in args.docs:
        add_missing_content(Path(doc_path), figs_dir, tbls_dir)


if __name__ == "__main__":
    main()
