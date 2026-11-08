"""
inspect_eq_paras.py
Print surrounding context for candidate equation paragraphs to identify true displayed equations.
Output is UTF-8 safe.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from docx import Document

doc = Document('SPEFinal.docx')
paras = doc.paragraphs

# Candidate para indices from detect_equations.py output
candidates = [46, 47, 50, 51, 53, 58, 62, 81, 85, 88, 93, 94, 106, 114, 118, 131, 134, 140]

for pi in candidates:
    p = paras[pi]
    txt = p.text.strip()
    style = p.style.name if p.style else 'Normal'
    # Print 3-para window
    print(f"\n--- Para {pi} [style={style}] ---")
    for j in range(max(0, pi-1), min(len(paras), pi+2)):
        snippet = paras[j].text.strip()[:120].replace('\n',' ')
        marker = ">>" if j == pi else "  "
        print(f"  {marker} [{j:03d}] {snippet}")
