"""
add_equation_numbers.py
Add right-aligned sequential equation numbers (1) through (7) to displayed equation paragraphs
in SPEFinal.docx using python-docx tab stops.
"""
import sys, io, shutil, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt
from lxml import etree

DOCX_PATH   = 'SPEFinal.docx'
BACKUP_PATH = 'SPEFinal_pre_eq_numbers.docx'

# (para_index, eq_number, expected_text_fragment)
EQUATIONS = [
    (47,  1, 'M/M/1 Residence Time'),          # R_i = S_i / (1 − ρ_i)
    (62,  2, 'LQN Demarcation'),                # S_i = D_(parent,i) − Σ ...
    (80,  3, 'Traffic Balance Equation'),        # (I − Pᵀ) · λ = λ_ext
    (88,  4, 'Visit Ratio Formulation'),         # V_i = λ_i / λ_0
    (94,  5, 'Total Service Demand'),            # D_i = V_i · S_i
    (106, 6, 'Maximum Saturation Throughput'),   # λ_sat = 1 / max_i(D_i)
    (139, 7, 'Sensitivity analysis applies partial'),  # ∂R_sys / ∂S_i = V_i / (1 − ρ_i)^2
]

def add_right_tab_and_number(para, eq_num, tab_pos_cm=15.5):
    """Add a right-aligned tab stop at tab_pos_cm and append TAB + (eq_num) to the paragraph."""
    pPr = para._p.get_or_add_pPr()

    # Add tab stop
    tabs = pPr.find(qn('w:tabs'))
    if tabs is None:
        tabs = OxmlElement('w:tabs')
        pPr.append(tabs)

    tab_el = OxmlElement('w:tab')
    tab_el.set(qn('w:val'), 'right')
    tab_el.set(qn('w:pos'), str(int(tab_pos_cm * 567)))   # 1 cm = 567 twips
    tabs.append(tab_el)

    # Create a run with tab + equation number in same font as paragraph
    new_run = OxmlElement('w:r')

    # Copy run properties from first run if available, so font matches
    existing_runs = para._p.findall(qn('w:r'))
    if existing_runs:
        rPr_src = existing_runs[0].find(qn('w:rPr'))
        if rPr_src is not None:
            new_rPr = copy.deepcopy(rPr_src)
            # Remove any bold/italic overrides to keep number plain Roman
            for el in new_rPr.findall(qn('w:b')):
                new_rPr.remove(el)
            for el in new_rPr.findall(qn('w:i')):
                new_rPr.remove(el)
            new_run.insert(0, new_rPr)

    # Tab character
    tab_char = OxmlElement('w:tab')
    new_run.append(tab_char)

    # Equation number text
    t_el = OxmlElement('w:t')
    t_el.text = f'({eq_num})'
    t_el.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    new_run.append(t_el)

    para._p.append(new_run)


def main():
    shutil.copy2(DOCX_PATH, BACKUP_PATH)
    print(f'Backup created: {BACKUP_PATH}')

    doc = Document(DOCX_PATH)
    paras = doc.paragraphs

    applied = []
    skipped = []

    for (pi, eq_num, expected_fragment) in EQUATIONS:
        p = paras[pi]
        txt = p.text.strip()
        # Verify fragment is present in the paragraph
        if expected_fragment.lower() in txt.lower():
            # Check we haven't already added this equation number
            if f'({eq_num})' in txt:
                skipped.append((pi, eq_num, 'already numbered'))
                print(f'  SKIP para {pi:03d} EQ ({eq_num}): already present')
                continue
            add_right_tab_and_number(p, eq_num)
            applied.append((pi, eq_num, txt[:80]))
            print(f'  EQ ({eq_num}) added to para {pi:03d}: ...{txt[:70]}...')
        else:
            skipped.append((pi, eq_num, f'fragment not found'))
            print(f'  SKIP para {pi:03d} EQ ({eq_num}): fragment "{expected_fragment}" NOT found in:')
            print(f'    "{txt[:100]}"')

    doc.save(DOCX_PATH)
    print(f'\nSaved: {DOCX_PATH}')
    print(f'Applied: {len(applied)} / {len(EQUATIONS)} equation numbers.')
    if skipped:
        print(f'Skipped ({len(skipped)}): {[s[:2] for s in skipped]}')


if __name__ == '__main__':
    main()
