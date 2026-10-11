"""
Insert 7 Publication Figures into SPE_final.docx in their Rightful Places
========================================================================
Finds the exact section captions in the Word Document:
  1. Figure 1: Reconstructed Microservice Call Graph for Google Online Boutique
  2. Figure 2: Layered Queueing Network (LQN) Three-Tier Architecture
  3. Figure 3: Microservice Utilisation Spectrum at 10 req/s Nominal Load
  4. Figure 4: Analytical Model Predictions vs. Real-World Kubernetes Benchmark Measurements
  5. Figure 5: System Latency Hockey-Stick Knee Curve and 500 ms SLA Boundary
  6. Figure 6: System Response Time Under Multi-Replica Frontend Scaling (c = 1 to 6)
  7. Figure 7: Sensitivity Tornado Chart: Where System Speedup Comes From

Inserts the corresponding 300-DPI PNG image directly after each caption block.
Also removes any trailing raw figure dump in Appendix B.
"""

from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCX_PATH = PROJECT_ROOT / "SPE_final.docx"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures"

FIGURE_MAPPING = [
    ("Figure 1: Reconstructed Microservice Call Graph", FIGURES_DIR / "figure1_reconstructed_call_graph.png", Inches(6.0)),
    ("Figure 2: Layered Queueing Network (LQN) Three-Tier", FIGURES_DIR / "figure2_lqn_three_tier_architecture.png", Inches(5.8)),
    ("Figure 3: Microservice Utilisation Spectrum", FIGURES_DIR / "figure3_utilisation_spectrum.png", Inches(5.8)),
    ("Figure 4: Analytical Model Predictions vs. Real-World", FIGURES_DIR / "figure4_predictions_vs_measurements.png", Inches(5.8)),
    ("Figure 5: System Latency Hockey-Stick Knee Curve", FIGURES_DIR / "figure5_hockey_stick_knee_curve.png", Inches(5.8)),
    ("Figure 6: System Response Time Under Multi-Replica", FIGURES_DIR / "figure6_multi_replica_scaling.png", Inches(5.8)),
    ("Figure 7: Sensitivity Tornado Chart", FIGURES_DIR / "figure7_sensitivity_tornado.png", Inches(5.8)),
]


def insert_figures_in_place():
    print(f"Loading {DOCX_PATH.name}...")
    doc = Document(str(DOCX_PATH))
    
    # First, let's remove any raw dumped images at the end of Appendix B
    # Appendix B starts around "Appendix B – Summary of Key Benchmark Numbers"
    appendix_b_idx = None
    for i, p in enumerate(doc.paragraphs):
        if "Appendix B – Summary of Key Benchmark Numbers" in p.text:
            appendix_b_idx = i
            break
            
    if appendix_b_idx is not None:
        # Check paragraphs after appendix B for trailing dumped figures
        for p in list(doc.paragraphs[appendix_b_idx:]):
            if any(p.text.startswith(prefix) for prefix in [
                "Figure 1: comparison response time",
                "Figure 2: error heatmap",
                "Figure 3: fig 7 1",
                "Figure 4: fig 7 2",
                "Figure 5: fig 7 3",
                "Figure 6: fig 7 4",
                "Figure 8: scatter response time",
                "Figure 9: system response time",
                "Figure 10: utilization vs arrival rate",
            ]):
                p.text = ""
                # Also remove XML drawings if present in this paragraph
                for d in p._p.xpath('.//w:drawing'):
                    p._p.remove(d)

    # Now insert figures in the rightful places
    for caption_prefix, img_path, width in FIGURE_MAPPING:
        if not img_path.exists():
            print(f"  WARNING: Image {img_path.name} not found, skipping.")
            continue
            
        target_para = None
        for i, p in enumerate(doc.paragraphs):
            # We want the body caption (not the Table of Figures entry)
            if caption_prefix in p.text and i > 40:
                target_para = p
                break
                
        if target_para is not None:
            # Check if there is already an image in the paragraph right after or right before
            # Insert a new paragraph directly after target_para
            new_p = target_para.insert_paragraph_before()
            new_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = new_p.add_run()
            run.add_picture(str(img_path), width=width)
            print(f"  Inserted {img_path.name} above caption: '{target_para.text[:60]}...'")
        else:
            print(f"  WARNING: Caption '{caption_prefix}' not found in body text.")

    doc.save(str(DOCX_PATH))
    print(f"Saved updated document with inserted figures to {DOCX_PATH.name}")


if __name__ == "__main__":
    insert_figures_in_place()
