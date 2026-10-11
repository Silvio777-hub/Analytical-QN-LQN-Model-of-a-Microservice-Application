"""
full_docx_audit.py  — comprehensive scan of the ACTUAL SPE_final.docx
Prints every paragraph and table cell that contains a known problem string,
plus cross-consistency values found in the document.
"""
import sys
from docx import Document
sys.stdout.reconfigure(encoding='utf-8')

doc = Document('SPEFinal.docx')

PROBLEMS = {
    'Code Analysis': 'CRITICAL',
    'code analysis': 'CRITICAL',
    'Source Code Estimate': 'CRITICAL',
    '6.80': 'CRITICAL',
    '85.00': 'HIGH',
    '0.85': 'HIGH',
    '2.14': 'HIGH',
    '12 h': 'HIGH',
    '12-h': 'HIGH',
    'placeholder': 'MEDIUM',
    'TODO': 'MEDIUM',
    'TBD': 'MEDIUM',
    'FIXME': 'MEDIUM',
    '-57': 'INFO',       # WMAPE check
    '9.20': 'INFO',
    '0.9926': 'INFO',
    '94.70': 'INFO',
    '95.91': 'WARN',     # wrong leverage value?
    '94.0': 'INFO',
    '80.00': 'INFO',
    '43.2': 'INFO',
    '17,200': 'INFO',
    '16,190': 'INFO',
}

print("="*70)
print("PARAGRAPH SCAN")
print("="*70)
for i, p in enumerate(doc.paragraphs):
    t = p.text
    found = [(k, v) for k, v in PROBLEMS.items() if k in t]
    if found:
        flags = ', '.join(f"[{v}:{k}]" for k, v in found)
        print(f"\nPara {i:3d} [{p.style.name}] {flags}")
        print(f"  TEXT: {t[:300]}")

print("\n" + "="*70)
print("TABLE SCAN")
print("="*70)
for ti, table in enumerate(doc.tables):
    for ri, row in enumerate(table.rows):
        for ci, cell in enumerate(row.cells):
            ct = cell.text
            found = [(k, v) for k, v in PROBLEMS.items() if k in ct]
            if found:
                flags = ', '.join(f"[{v}:{k}]" for k, v in found)
                print(f"\n  Table {ti}, Row {ri}, Col {ci} {flags}")
                print(f"  TEXT: {ct[:200]}")

print("\n" + "="*70)
print("TABLE 1 FULL DUMP (service times table)")
print("="*70)
if len(doc.tables) > 1:
    t1 = doc.tables[1]
    for ri, row in enumerate(t1.rows):
        texts = [c.text.strip() for c in row.cells]
        print(f"  Row {ri}: {texts}")

print("\n" + "="*70)
print("KEY CONSISTENCY VALUES")
print("="*70)
checks = {
    'WMAPE': ['-57', '9.20'],
    'Frontend leverage': ['94.70', '95.91'],
    'R²': ['0.9926'],
    'USL efficiency': ['93.6', '94.0'],
    'Optimal replicas': ['c = 3', 'c=3'],
    '80 ms vs 116 ms': ['116'],
    'Routing 0.82 footnote': ['0.82', 'static-asset'],
}
all_text = '\n'.join(p.text for p in doc.paragraphs)
for name, patterns in checks.items():
    hits = [p for p in patterns if p in all_text]
    miss = [p for p in patterns if p not in all_text]
    status = 'PASS' if not miss else 'FAIL/MISSING'
    print(f"  {status:12s} {name}: found={hits}, missing={miss}")
