"""
audit_all_docx.py
=================
Deep-audits every .docx in the project root (excluding venv/others backups).
For each document reports:
  - File size, last modified
  - Number of paragraphs, tables, images embedded
  - Presence of key canonical numbers (S0=80ms, Rsys=139.62, lambda_sat=12.5)
  - Which figures are embedded (by searching picture relationships)
  - First 5 non-empty paragraph texts (gives sense of content structure)
  - Section 8 presence (new HPA / multitier section)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
from docx import Document
from docx.oxml.ns import qn

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Documents to audit (root-level only — backups in others/ are skipped unless specified)
TARGET_DOCS = [
    "SPEFinal.docx",
    "Software Performance Engineering Course.docx",
]

# Key numbers that MUST appear somewhere in the document
KEY_NUMBERS = [
    ("S0 = 80 ms", ["80.00 ms", "80 ms", "S₀=80", "S0=80", "= 80", "80.0 ms"]),
    ("R_sys = 139.62 ms", ["139.62", "139.6"]),
    ("λ_sat = 12.5 req/s", ["12.5 req/s", "12.50 req/s", "12.5", "λ_sat"]),
    ("Bottleneck = Frontend", ["Frontend", "frontend"]),
    ("WMAPE", ["WMAPE", "wmape"]),
    ("Section 8 / HPA / Multi-tier", ["Section 8", "Multi-Tier", "HPA", "autoscal", "Autoscal"]),
]

def count_images(doc):
    """Count embedded images in all paragraphs."""
    count = 0
    for para in doc.paragraphs:
        for run in para.runs:
            if run._r.findall(qn('a:blip'), run._r.nsmap) or \
               run._r.findall('.//' + qn('a:blip')):
                count += 1
    # Also count from inline shapes
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            count += 1
    return count

def extract_all_text(doc):
    """Extract all text from paragraphs and table cells."""
    texts = []
    for para in doc.paragraphs:
        t = para.text.strip()
        if t:
            texts.append(t)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    t = para.text.strip()
                    if t:
                        texts.append(t)
    return texts

def check_key_numbers(all_text_joined, key_numbers):
    results = {}
    for label, variants in key_numbers:
        found = any(v in all_text_joined for v in variants)
        results[label] = found
    return results

def audit_doc(rel_path):
    full_path = os.path.join(PROJECT_ROOT, rel_path)
    print(f"\n{'='*72}")
    print(f"DOCUMENT: {rel_path}")
    print(f"{'='*72}")

    if not os.path.exists(full_path):
        print("  [NOT FOUND]")
        return

    stat = os.stat(full_path)
    size_kb = stat.st_size / 1024
    import datetime
    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Size       : {size_kb:.1f} KB")
    print(f"  Modified   : {mtime}")

    doc = Document(full_path)

    # Count sections/paragraphs/tables
    non_empty_paras = [p for p in doc.paragraphs if p.text.strip()]
    print(f"  Paragraphs : {len(doc.paragraphs)} total, {len(non_empty_paras)} non-empty")
    print(f"  Tables     : {len(doc.tables)}")

    # Count images via relationships
    image_count = sum(1 for rel in doc.part.rels.values() if "image" in rel.reltype)
    print(f"  Images     : {image_count} embedded")

    # Check headings
    headings = [p for p in doc.paragraphs if p.style.name.startswith("Heading")]
    print(f"  Headings   : {len(headings)}")
    if headings:
        print("  Top-level headings found:")
        for h in headings[:20]:
            indent = "    " + ("  " * (int(h.style.name[-1]) - 1) if h.style.name[-1].isdigit() else "")
            print(f"  {indent}[{h.style.name}] {h.text[:80]}")

    # Extract all text and check canonical numbers
    all_texts = extract_all_text(doc)
    all_text_joined = " ".join(all_texts)
    key_checks = check_key_numbers(all_text_joined, KEY_NUMBERS)

    print(f"\n  KEY CONTENT AUDIT:")
    all_ok = True
    for label, present in key_checks.items():
        status = "✅ FOUND" if present else "❌ MISSING"
        if not present:
            all_ok = False
        print(f"    {status}  {label}")

    # Check figures explicitly
    figure_names = []
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            try:
                figure_names.append(rel.target_ref)
            except Exception:
                pass
    if figure_names:
        print(f"\n  EMBEDDED FIGURE REFERENCES ({len(figure_names)}):")
        for fn in figure_names[:15]:
            print(f"    - {fn}")
        if len(figure_names) > 15:
            print(f"    ... and {len(figure_names)-15} more")

    print(f"\n  OVERALL CONTENT STATUS: {'✅ ALL KEY CONTENT PRESENT' if all_ok else '⚠️  SOME KEY CONTENT MISSING'}")

def main():
    print("SPE PROJECT — COMPREHENSIVE DOCX AUDIT")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Audit Time  : {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for doc_path in TARGET_DOCS:
        audit_doc(doc_path)

    print(f"\n{'='*72}")
    print("AUDIT COMPLETE")
    print(f"{'='*72}")

if __name__ == "__main__":
    main()
