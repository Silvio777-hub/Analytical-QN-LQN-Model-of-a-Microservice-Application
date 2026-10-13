"""
align_table_appendix_numbering.py
==================================
Fixes the two structural numbering defects:
1. Fix duplicate Table 7 in body:
   - Para 135: Table 7 -> Table 8: M/M/c Horizontal Pod Autoscaling Performance & USL Efficiency
   - Para 142: Table 8 -> Table 9: Sensitivity Analysis & Engineering Optimization Priority Ranking
   (This perfectly matches List of Tables in front matter where Table 8 is M/M/c and Table 9 is Sensitivity)

2. Fix Section 8 post-appendix collision:
   - Para 172: Section 8: Multi-Tier Live Empirical Validation... -> Appendix C – Multi-Tier Live Empirical Validation & HPA Autoscaling Policy
   - Para 174: 8.1 -> C.1 Multi-Tier Live Empirical Validation (Oct 8, 2026)
   - Para 181: 8.2 -> C.2 Mathematical Kubernetes HPA Autoscaling Policy
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import shutil
from pathlib import Path
from docx import Document

DOCX = Path("SPEFinal.docx")
COURSE = Path("Software Performance Engineering Course.docx")
PDF = Path("SPEFinal_final.pdf")

doc = Document(DOCX)

# 1. Fix Table Captions
for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if txt == "Table 7: M/M/c Horizontal Pod Autoscaling Performance & USL Efficiency":
        p.text = "Table 8: M/M/c Horizontal Pod Autoscaling Performance & USL Efficiency"
        print(f"Fixed Para {i}: Table 7 -> Table 8 (M/M/c)")
    elif txt == "Table 8: Sensitivity Analysis & Engineering Optimization Priority Ranking":
        p.text = "Table 9: Sensitivity Analysis & Engineering Optimization Priority Ranking"
        print(f"Fixed Para {i}: Table 8 -> Table 9 (Sensitivity)")
    elif txt.startswith("Section 8: Multi-Tier Live Empirical Validation"):
        p.text = "Appendix C – Multi-Tier Live Empirical Validation & HPA Autoscaling Policy"
        print(f"Fixed Para {i}: Section 8 -> Appendix C")
    elif txt.startswith("8.1  Multi-Tier Live Empirical"):
        p.text = "C.1  Multi-Tier Live Empirical Validation (Oct 8, 2026)"
        print(f"Fixed Para {i}: 8.1 -> C.1")
    elif txt.startswith("8.2  Mathematical Kubernetes HPA"):
        p.text = "C.2  Mathematical Kubernetes HPA Autoscaling Policy"
        print(f"Fixed Para {i}: 8.2 -> C.2")

doc.save(DOCX)
print("Saved SPEFinal.docx")

shutil.copy2(DOCX, COURSE)
print("Synced Software Performance Engineering Course.docx")

# Re-export PDF via Word COM
try:
    import win32com.client
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    d = word.Documents.Open(str(DOCX.resolve()), ReadOnly=False)
    d.ExportAsFixedFormat(str(PDF.resolve()), 17, OpenAfterExport=False)
    d.Close(SaveChanges=False)
    word.Quit()
    print(f"Exported PDF successfully: {PDF.stat().st_size:,} bytes")
except Exception as e:
    print(f"Word PDF export: {e}")
