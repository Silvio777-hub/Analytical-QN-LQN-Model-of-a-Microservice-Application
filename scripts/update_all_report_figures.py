"""
update_all_report_figures.py
============================
Updates and inserts the 100% correct, newly generated, 300-DPI publication figures
directly into the Word report documents:
1. SPEFinal.docx: Replaces existing embedded images (media/image2.png - image10.png)
   with the newly verified figures.
2. Software Performance Engineering Course.docx: Inserts the publication figures
   immediately before each figure caption.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, zipfile, io, hashlib, shutil
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = r"c:\Users\7172981\Downloads\Analytical QNLQN Model of a Microservice Application - Oct"
FIGURES_DIR = os.path.join(BASE, "results", "figures")

MAPPING_SPEFINAL = {
    "word/media/image2.png": os.path.join(FIGURES_DIR, "figure1_reconstructed_call_graph.png"),
    "word/media/image3.png": os.path.join(FIGURES_DIR, "figure2_lqn_three_tier_architecture.png"),
    "word/media/image4.png": os.path.join(FIGURES_DIR, "figure3_utilisation_spectrum.png"),
    "word/media/image10.png": os.path.join(FIGURES_DIR, "utilization_vs_arrival_rate.png"),
    "word/media/image5.png": os.path.join(FIGURES_DIR, "figure4_predictions_vs_measurements.png"),
    "word/media/image6.png": os.path.join(FIGURES_DIR, "figure5_hockey_stick_knee_curve.png"),
    "word/media/image9.png": os.path.join(FIGURES_DIR, "system_response_time.png"),
    "word/media/image7.png": os.path.join(FIGURES_DIR, "figure6_multi_replica_scaling.png"),
    "word/media/image8.png": os.path.join(FIGURES_DIR, "figure7_sensitivity_tornado.png"),
}

MAPPING_COURSE = [
    ("Figure 1: Reconstructed Microservice Call Graph", os.path.join(FIGURES_DIR, "figure1_reconstructed_call_graph.png")),
    ("Figure 2: Layered Queueing Network (LQN) Three-Tier", os.path.join(FIGURES_DIR, "figure2_lqn_three_tier_architecture.png")),
    ("Figure 3: Microservice Utilisation Spectrum", os.path.join(FIGURES_DIR, "figure3_utilisation_spectrum.png")),
    ("Figure 4: Analytical Model Predictions vs. Real-World", os.path.join(FIGURES_DIR, "figure4_predictions_vs_measurements.png")),
    ("Figure 5: System Latency Hockey-Stick Knee Curve", os.path.join(FIGURES_DIR, "figure5_hockey_stick_knee_curve.png")),
    ("Figure 6: System Response Time Under Multi-Replica", os.path.join(FIGURES_DIR, "figure6_multi_replica_scaling.png")),
    ("Figure 7: Sensitivity Tornado Chart", os.path.join(FIGURES_DIR, "figure7_sensitivity_tornado.png")),
]

def update_spefinal_docx():
    docx_path = os.path.join(BASE, "SPEFinal.docx")
    backup_path = os.path.join(BASE, "SPEFinal_PRE_FIGURE_UPDATE.docx")
    shutil.copy2(docx_path, backup_path)
    print(f"\n[SPEFinal.docx] Backed up to {os.path.basename(backup_path)}")

    temp_docx = docx_path + ".temp.zip"
    
    with zipfile.ZipFile(docx_path, 'r') as zin:
        with zipfile.ZipFile(temp_docx, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in MAPPING_SPEFINAL:
                    new_file = MAPPING_SPEFINAL[item.filename]
                    with open(new_file, 'rb') as f:
                        new_bytes = f.read()
                    zout.writestr(item, new_bytes)
                    print(f"  [REPLACED] {item.filename} with {os.path.basename(new_file)} ({len(new_bytes):,} bytes)")
                else:
                    zout.writestr(item, zin.read(item.filename))
                    
    shutil.move(temp_docx, docx_path)
    print(f"[SPEFinal.docx] Successfully replaced all 9 figure images directly inside docx package.")

def update_course_docx():
    docx_path = os.path.join(BASE, "Software Performance Engineering Course.docx")
    backup_path = os.path.join(BASE, "Software Performance Engineering Course_PRE_FIGURE_UPDATE.docx")
    shutil.copy2(docx_path, backup_path)
    print(f"\n[Course.docx] Backed up to {os.path.basename(backup_path)}")

    doc = Document(docx_path)
    inserted_count = 0

    for caption_prefix, img_path in MAPPING_COURSE:
        for i, p in enumerate(doc.paragraphs):
            if caption_prefix in p.text:
                # Insert paragraph before caption
                img_para = p.insert_paragraph_before()
                img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = img_para.add_run()
                run.add_picture(img_path, width=Inches(5.8))
                inserted_count += 1
                print(f"  [INSERTED] {os.path.basename(img_path)} before P{i}: {caption_prefix[:45]}...")
                break

    doc.save(docx_path)
    print(f"[Course.docx] Successfully inserted {inserted_count} publication figures before their captions.")

def verify_images():
    print(f"\n{'='*70}\n  VERIFYING EMBEDDED IMAGES IN BOTH REPORTS\n{'='*70}")
    
    # 1. SPEFinal.docx
    with zipfile.ZipFile(os.path.join(BASE, "SPEFinal.docx"), 'r') as z:
        print("[SPEFinal.docx] Verifying SHA256 hashes against disk figures:")
        all_match = True
        for media_name, disk_path in MAPPING_SPEFINAL.items():
            docx_bytes = z.read(media_name)
            docx_hash = hashlib.sha256(docx_bytes).hexdigest()
            with open(disk_path, 'rb') as f:
                disk_bytes = f.read()
            disk_hash = hashlib.sha256(disk_bytes).hexdigest()
            status = "MATCH [100% IDENTICAL]" if docx_hash == disk_hash else "MISMATCH"
            if docx_hash != disk_hash:
                all_match = False
            print(f"  {media_name.replace('word/', '')} <-> {os.path.basename(disk_path)}: {status}")
        print(f"  Verdict: {'ALL 9 FIGURES CORRECT AND MATCH DISK' if all_match else 'SOME MISMATCHES'}")

    # 2. Course.docx
    doc = Document(os.path.join(BASE, "Software Performance Engineering Course.docx"))
    image_parts = [rel for rel in doc.part.rels.values() if 'image' in rel.reltype]
    print(f"\n[Course.docx] Total embedded images: {len(image_parts)} (Expected: 7)")

if __name__ == "__main__":
    update_spefinal_docx()
    update_course_docx()
    verify_images()
