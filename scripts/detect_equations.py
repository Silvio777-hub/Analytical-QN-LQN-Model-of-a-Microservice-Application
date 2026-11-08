"""
detect_equations.py
Scan SPEFinal.docx for displayed equation paragraphs and print their indices.
Writes output to scripts/equation_para_list.txt (UTF-8) to avoid console codec issues.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from docx import Document

doc = Document('SPEFinal.docx')
eq_paras = []

MATH_SYMS = set('λμρσδεπΣ∑∫≤≥≠→←↑↓⟨⟩𝑁𝑅𝑆𝑊𝑋𝐷𝑈𝐶𝐸')
START_LETTERS = set('NRSWXDUCET')

for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if not txt or '=' not in txt:
        continue
    if len(txt) > 400 or len(txt) < 5:
        continue
    # Must look like an equation: either contains math unicode or starts with uppercase
    # variable-like letter and has an = sign
    has_math_sym = any(c in MATH_SYMS for c in txt)
    starts_like_eq = txt[0] in START_LETTERS and '=' in txt and len(txt) < 200
    # Exclude table-of-contents-style lines
    if '......' in txt or '…' in txt:
        continue
    # Exclude long prose sentences
    words = txt.split()
    if len(words) > 30:
        continue
    if has_math_sym or starts_like_eq:
        eq_paras.append((i, txt))

lines = []
for idx, (pi, txt) in enumerate(eq_paras):
    lines.append(f'EQ {idx+1:02d} | para {pi:03d} | {txt[:100]}')

out_path = 'scripts/equation_para_list.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print(f"Found {len(eq_paras)} equation paragraphs. Written to {out_path}")
