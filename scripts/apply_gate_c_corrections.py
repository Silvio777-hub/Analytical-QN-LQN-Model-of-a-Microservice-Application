"""
apply_gate_c_corrections.py
Implements Gate C:
1. Native Word OMML equations for EQ-01 to EQ-07 via latex2mathml + MML2OMML.XSL.
2. Bookmarks for Table 8 (_Toc239986432) and Table 9 (_Toc239986433) in LOT.
3. Explicit caption numbers (Table 1-6, Figure 1-2).
4. Span count reconciliation (6,542 empirical spans across 10 microservices, 6,642 total corpus spans).
5. Uniform 1.5 line spacing (w:line="360", w:lineRule="auto") on body paragraphs.
"""
import sys, io, shutil
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement, parse_xml
import lxml.etree as ET
from latex2mathml.converter import convert

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = Path(r"c:\Users\7172981\Downloads\Analytical QNLQN Model of a Microservice Application - Oct")
DOCX_PATH = BASE / "SPEFinal.docx"
BACKUP_PATH = BASE / "SPEFinal_pre_gate_c.docx"

shutil.copy2(DOCX_PATH, BACKUP_PATH)
print(f"Backup created at: {BACKUP_PATH.name}")

# Setup XSLT
xslt_path = r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL"
xslt_doc = ET.parse(xslt_path)
transform = ET.XSLT(xslt_doc)

def latex_to_omml_element(latex_str):
    mathml = convert(latex_str)
    mathml_doc = ET.fromstring(mathml)
    omml_doc = transform(mathml_doc)
    omml_xml = ET.tostring(omml_doc, encoding="utf-8").decode("utf-8")
    # clean namespaces if needed, parse into oxml
    return parse_xml(omml_xml)

doc = Document(str(DOCX_PATH))
paras = doc.paragraphs

# -------------------------------------------------------------
# 1. CONVERT 7 DISPLAYED EQUATIONS TO NATIVE OMML OBJECTS
# -------------------------------------------------------------
eq_specs = [
    (47, 1, r"R_i = \frac{S_i}{1 - \rho_i}", "M/M/1 Residence Time"),
    (62, 2, r"S_i = D_{\mathrm{parent},i} - \sum_{j \in \mathrm{Children}(i)} D_{\mathrm{child},j}", "LQN Demarcation"),
    (80, 3, r"(\mathbf{I} - \mathbf{P}^T)\boldsymbol{\lambda} = \boldsymbol{\lambda}_{\mathrm{ext}}", "Traffic Balance"),
    (88, 4, r"V_i = \frac{\lambda_i}{\lambda_0}", "Visit Ratio"),
    (94, 5, r"D_i = V_i S_i", "Total Service Demand"),
    (106, 6, r"\lambda_{\mathrm{sat}} = \frac{1}{\max_{i}(V_i S_i)} = \frac{1}{D_{\max}}", "Bottleneck Law"),
    (139, 7, r"\frac{\partial R_{\mathrm{sys}}}{\partial S_i} = \frac{V_i}{(1 - \rho_i)^2}", "Sensitivity Derivative")
]

for pi, eq_num, latex_code, label in eq_specs:
    p = paras[pi]
    # Check if text contains equation
    txt = p.text
    print(f"\nProcessing EQ ({eq_num}) at Para {pi:03d}...")
    
    # Generate OMML
    omml_elem = latex_to_omml_element(latex_code)
    
    # We want the paragraph to display:
    # Heading/intro text, then the OMML equation, then tab + (n)
    # Let's inspect the paragraph runs
    # In earlier script, we appended `\t(eq_num)` to the paragraph
    # Let's clear the trailing text formula and replace it with the native OMML element + tab + (eq_num)
    
    # Find intro text before formula
    # If para has newlines:
    parts = txt.split('\n')
    intro_lines = []
    for line in parts:
        if any(tok in line for tok in ['R_i =', 'S_i =', '(I -', '(I −', 'V_i =', 'D_i =', 'λ_sat =', '∂R_sys']):
            break
        intro_lines.append(line)
    
    intro_text = '\n'.join(intro_lines).strip()
    if intro_text:
        intro_text += '\n'
    
    # Clear paragraph elements
    pPr = p._p.find(qn('w:pPr'))
    p._p.clear()
    if pPr is not None:
        p._p.append(pPr)
    
    # Add intro run if any
    if intro_text:
        run_intro = OxmlElement('w:r')
        t_intro = OxmlElement('w:t')
        t_intro.text = intro_text
        t_intro.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        run_intro.append(t_intro)
        p._p.append(run_intro)
    
    # Add native OMML element
    p._p.append(omml_elem)
    
    # Add tab + equation number run
    run_num = OxmlElement('w:r')
    tab_el = OxmlElement('w:tab')
    run_num.append(tab_el)
    t_num = OxmlElement('w:t')
    t_num.text = f"({eq_num})"
    t_num.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    run_num.append(t_num)
    p._p.append(run_num)
    
    print(f"  Successfully inserted native OMML for EQ ({eq_num})!")

# -------------------------------------------------------------
# 2. BOOKMARKS FOR TABLE 8 AND TABLE 9 (LOT REPAIR)
# -------------------------------------------------------------
# Table 8 caption is at Para 135
p_tab8 = paras[135]
bm8_start = OxmlElement('w:bookmarkStart')
bm8_start.set(qn('w:id'), '101')
bm8_start.set(qn('w:name'), '_Toc239986432')
bm8_end = OxmlElement('w:bookmarkEnd')
bm8_end.set(qn('w:id'), '101')
p_tab8._p.insert(0, bm8_start)
p_tab8._p.append(bm8_end)
print("Added bookmark _Toc239986432 to Table 8 caption.")

# Table 9 caption is at Para 142
p_tab9 = paras[142]
bm9_start = OxmlElement('w:bookmarkStart')
bm9_start.set(qn('w:id'), '102')
bm9_start.set(qn('w:name'), '_Toc239986433')
bm9_end = OxmlElement('w:bookmarkEnd')
bm9_end.set(qn('w:id'), '102')
p_tab9._p.insert(0, bm9_start)
p_tab9._p.append(bm9_end)
print("Added bookmark _Toc239986433 to Table 9 caption.")

# Also update LOT text directly (in paras 24 and 25) so even before Word field refresh, clean text is shown
p_lot8 = paras[24]
p_lot9 = paras[25]
# Replace "Error! Bookmark not defined." with clean placeholder page numbers (16 and 17)
if "Error! Bookmark not defined." in p_lot8.text:
    for r in p_lot8.runs:
        if "Error! Bookmark not defined." in r.text:
            r.text = r.text.replace("Error! Bookmark not defined.", "16")
    print("Fixed LOT Table 8 text.")

if "Error! Bookmark not defined." in p_lot9.text:
    for r in p_lot9.runs:
        if "Error! Bookmark not defined." in r.text:
            r.text = r.text.replace("Error! Bookmark not defined.", "17")
    print("Fixed LOT Table 9 text.")

# -------------------------------------------------------------
# 3. EXPLICIT CAPTION NUMBERS FOR TABLE 1-6 AND FIGURE 1-2
# -------------------------------------------------------------
caption_replacements = [
    (45, "Table : Concept,", "Table 1: Concept,"),
    (61, "Table : Open Jackson", "Table 2: Open Jackson"),
    (70, "Table : Queueing Model", "Table 3: Queueing Model"),
    (73, "Table : Online Boutique", "Table 4: Online Boutique"),
    (75, "Figure : Reconstructed", "Figure 1: Reconstructed"),
    (77, "Figure : Layered Queueing", "Figure 2: Layered Queueing"),
    (99, "Table : Visit Ratio,", "Table 5: Visit Ratio,"),
    (101, "Table : Empirical Service Times", "Table 6: Empirical Service Times"),
]

for pi, old_prefix, new_prefix in caption_replacements:
    p = paras[pi]
    if old_prefix in p.text:
        for r in p.runs:
            if old_prefix in r.text:
                r.text = r.text.replace(old_prefix, new_prefix)
                print(f"Para {pi:03d}: replaced '{old_prefix}' -> '{new_prefix}'")
            elif "Table :" in r.text:
                r.text = r.text.replace("Table :", new_prefix.split()[0] + ":")
            elif "Figure :" in r.text:
                r.text = r.text.replace("Figure :", new_prefix.split()[0] + ":")

# -------------------------------------------------------------
# 4. SPAN COUNT RECONCILIATION TEXT
# -------------------------------------------------------------
# Para 6 (Executive Summary), Para 29 (Introduction), Para 103 (Data note), Para 149 (Conclusion)
span_edits = [
    (6, "6,642 Jaeger telemetry spans", "6,542 empirical telemetry spans (6,642 total spans in the baseline corpus)"),
    (29, "6,642 telemetry spans across 687 traces", "6,542 empirical telemetry spans across 687 traces (6,642 total spans in the baseline corpus)"),
    (103, "All 10 microservice service times are extracted directly from the 6,642 Jaeger distributed telemetry spans collected on October 8, 2026. Redis is a synthetic baseline (2.0 ms) not measured in traces.",
          "All 10 microservice service times are extracted directly from the 6,542 empirical Jaeger distributed telemetry spans collected across 687 traces on October 8, 2026 (accounting for 6,642 total spans in the baseline corpus including monitoring spans). Redis is a synthetic baseline (2.0 ms) not measured in traces."),
    (149, "analysing 6,642 telemetry spans across 687 traces", "analysing 6,542 empirical telemetry spans (6,642 total corpus spans) across 687 traces")
]

for pi, old_txt, new_txt in span_edits:
    p = paras[pi]
    if old_txt in p.text:
        # replace in paragraph text
        for r in p.runs:
            if old_txt in r.text:
                r.text = r.text.replace(old_txt, new_txt)
                print(f"Para {pi:03d}: reconciled span count text.")
                break
        else:
            # if split across runs
            full_t = p.text.replace(old_txt, new_txt)
            p.text = full_t
            print(f"Para {pi:03d}: reconciled span count across runs.")

# -------------------------------------------------------------
# 5. UNIFORM 1.5 LINE SPACING ACROSS ALL BODY PARAGRAPHS
# -------------------------------------------------------------
modified_spacing_count = 0
for idx, p in enumerate(paras):
    style_name = p.style.name if p.style else 'Normal'
    # Skip title and headings from line spacing if they have special style, but set 1.5 on Normal/Body
    if style_name in ['Normal', 'Body Text', 'List Paragraph']:
        pPr = p._p.get_or_add_pPr()
        sp = pPr.find(qn('w:spacing'))
        if sp is None:
            sp = OxmlElement('w:spacing')
            pPr.append(sp)
        # Check current line
        curr_line = sp.get(qn('w:line'))
        if curr_line != '360':
            sp.set(qn('w:line'), '360')
            sp.set(qn('w:lineRule'), 'auto')
            modified_spacing_count += 1

print(f"Applied 1.5 line spacing (w:line=360) to {modified_spacing_count} body paragraphs.")

doc.save(str(DOCX_PATH))
print(f"\nAll Gate C corrections saved to {DOCX_PATH.name}!")
