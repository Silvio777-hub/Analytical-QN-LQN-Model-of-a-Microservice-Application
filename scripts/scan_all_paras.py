"""
scan_all_paras.py
Print ALL paragraphs with their indices to identify equation paragraphs precisely.
Writes to scripts/all_paras.txt (UTF-8).
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from docx import Document

doc = Document('SPEFinal.docx')

out_path = 'scripts/all_paras.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    for i, p in enumerate(doc.paragraphs):
        txt = p.text.strip()
        style = p.style.name if p.style else 'Normal'
        f.write(f"[{i:03d}] [{style}] {txt[:150]}\n")

print(f"Written {len(doc.paragraphs)} paragraphs to {out_path}")
