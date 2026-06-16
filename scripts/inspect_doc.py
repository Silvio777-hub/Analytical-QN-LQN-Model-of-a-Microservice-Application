"""
inspect_doc.py  –  Print every paragraph in REPORT.docx with its index,
style name, and first 120 chars of text.  Also flags paragraphs that
contain OfficeMath (equations) or are followed by an inline image run.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import os
from docx import Document
from docx.oxml.ns import qn


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_PATH = os.path.join(BASE_DIR, "REPORT.docx")

def has_math(para):
    return para._element.find(qn("m:oMathPara")) is not None or \
           para._element.find(qn("m:oMath")) is not None

def has_picture(para):
    return para._element.find('.//' + qn("a:blip")) is not None

def main():
    doc = Document(REPORT_PATH)
    print(f"Total paragraphs: {len(doc.paragraphs)}")
    print(f"Total tables: {len(doc.tables)}\n")
    print(f"{'IDX':>5}  {'STYLE':<30}  FLAGS  TEXT")
    print("-" * 110)
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        flags = ""
        if has_math(p):
            flags += "[EQ]"
        if has_picture(p):
            flags += "[IMG]"
        if text or flags:
            snippet = (text[:100] + "…") if len(text) > 100 else text
            print(f"{i:>5}  {p.style.name:<30}  {flags:<8}  {snippet}")

    print("\n--- TABLE SUMMARY ---")
    for ti, tbl in enumerate(doc.tables):
        print(f"Table #{ti}: {len(tbl.rows)} rows × {len(tbl.columns)} cols")
        if tbl.rows:
            header = " | ".join(c.text.strip()[:20] for c in tbl.rows[0].cells)
            print(f"  Header: {header}")

if __name__ == "__main__":
    main()
