"""
fix_figures_embed_v2.py
=======================
Fixes the front-matter contamination from v1 and correctly embeds
all 7 figures only within the BODY of the document (after the LOF/TOC
front matter), then re-exports PDF.

The LOF section ends around para 30. We only insert images before
captions whose paragraph index >= MIN_BODY_PARA.
Additionally, each caption is matched at most ONCE per caption label
so duplicate body captions don't get double images.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import shutil
from pathlib import Path

from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE      = Path(r"c:\Users\7172981\Downloads\Analytical QNLQN Model of a Microservice Application - Oct")
FIGS      = BASE / "results" / "figures"
DOCX      = BASE / "SPEFinal.docx"
BACKUP    = BASE / "SPEFinal_pre_figure_embed.docx"
COURSE    = BASE / "Software Performance Engineering Course.docx"

# Minimum paragraph index to be considered a body caption
# (anything before this is front-matter: TOC, LOF, LOT, Abstract)
MIN_BODY_PARA = 40

# Figure file map (caption fragment -> png file)
FIGURE_MAP = [
    ("Figure 1: Reconstructed",                  FIGS / "figure1_reconstructed_call_graph.png"),
    ("Figure 2: Layered Queueing Network",        FIGS / "figure2_lqn_three_tier_architecture.png"),
    ("Figure 3: Predicted Microservice Utilisa",  FIGS / "figure3_utilisation_spectrum.png"),
    ("Figure 4: Analytical Model Predictions",    FIGS / "figure4_predictions_vs_measurements.png"),
    ("Figure 5: Model-Predicted System Latency",  FIGS / "figure5_hockey_stick_knee_curve.png"),
    ("Figure 6: Predicted System Response Time",  FIGS / "figure6_multi_replica_scaling.png"),
    # Figure 7 — also covers the typo "Figure 3: Sensitivity..."
    ("Figure 7: Sensitivity Tornado",             FIGS / "figure7_sensitivity_tornado.png"),
    ("Figure 3: Sensitivity Tornado",             FIGS / "figure7_sensitivity_tornado.png"),
]

print("=" * 60)
print("Restoring from pre-figure-embed backup...")
print("=" * 60)
if not BACKUP.exists():
    print(f"ERROR: Backup not found at {BACKUP}")
    sys.exit(1)
shutil.copy2(BACKUP, DOCX)
print(f"Restored from {BACKUP.name}")

doc = Document(DOCX)
paras = doc.paragraphs
print(f"Total paragraphs in restored doc: {len(paras)}")

# Show first few paras to verify restoration
for i in range(8, 22):
    print(f"  Para {i:3d}: {repr(paras[i].text[:60])}")

print("\n" + "=" * 60)
print("Fixing Figure 7 caption typo...")
print("=" * 60)

for i, p in enumerate(paras):
    if i < MIN_BODY_PARA:
        continue
    txt = p.text.strip()
    if "Figure 3: Sensitivity Tornado" in txt:
        # Fix in all runs
        full = "".join(r.text for r in p.runs)
        if "Figure 3: Sensitivity" in full:
            p.runs[0].text = full.replace("Figure 3: Sensitivity", "Figure 7: Sensitivity", 1)
            for r in p.runs[1:]:
                r.text = ""
            print(f"  Para {i}: Fixed caption → 'Figure 7: Sensitivity Tornado...'")

print("\n" + "=" * 60)
print(f"Embedding figures (only in body, para >= {MIN_BODY_PARA})...")
print("=" * 60)

# Track which captions have already been matched to avoid double-inserting
# when same caption text appears multiple times in body
already_inserted = {}   # fragment -> count

for i, para in enumerate(doc.paragraphs):
    if i < MIN_BODY_PARA:
        continue

    txt = para.text.strip()

    for fragment, img_path in FIGURE_MAP:
        if fragment not in txt:
            continue
        if not img_path.exists():
            print(f"  SKIP {fragment!r}: image file not found at {img_path}")
            continue

        count = already_inserted.get(fragment, 0)
        if count >= 2:
            # Each caption label should appear at most twice in the body
            # (section caption + possible header reference) — 3rd+ is unexpected
            print(f"  SKIP para {i}: '{fragment}' already inserted {count}x")
            continue

        # Insert an image paragraph immediately before this caption
        img_para = doc.add_paragraph()
        img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        img_para.add_run().add_picture(str(img_path), width=Inches(5.5))
        para._element.addprevious(img_para._element)

        already_inserted[fragment] = count + 1
        print(f"  [{already_inserted[fragment]}] Embedded {img_path.name} before para {i} "
              f"('{fragment[:30]}...')")
        break   # only match first fragment for each para

print(f"\nTotal embed operations: {sum(already_inserted.values())}")

doc.save(DOCX)
print(f"\n✅ Saved: {DOCX.name}")

shutil.copy2(DOCX, COURSE)
print(f"✅ Synced: {COURSE.name}")

# Quick verification
doc2 = Document(DOCX)
n_imgs = len(doc2.inline_shapes)
print(f"\nVerification: {n_imgs} inline images in saved doc")
# Check no images in front matter
front_matter_imgs = 0
for i, p in enumerate(doc2.paragraphs[:MIN_BODY_PARA]):
    ns = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"
    if p._element.findall(f".//{ns}inline"):
        front_matter_imgs += 1
        print(f"  WARNING: Image still in front matter at para {i}")
if front_matter_imgs == 0:
    print("  ✅ Front matter is clean (no images in LOF/TOC section)")

# Re-export PDF
print("\n" + "=" * 60)
print("Re-exporting PDF...")
print("=" * 60)
try:
    import win32com.client
    pdf = str(BASE / "SPEFinal_final.pdf")
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    d = word.Documents.Open(str(DOCX), ReadOnly=False)
    d.ExportAsFixedFormat(pdf, 17, OpenAfterExport=False)
    d.Close(SaveChanges=False)
    word.Quit()
    print(f"✅ PDF exported: {Path(pdf).stat().st_size:,} bytes")
except Exception as e:
    print(f"⚠️  PDF export failed: {e}")
