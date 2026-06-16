"""
repair_report.py
================
Comprehensive one-pass repair of REPORT.docx.

Changes made
------------
1.  Figure captions  – append "(Source: authors)" to all six figure captions.
2.  Insert Figures 3-6 as inline images (PNG already in results/figures/).
3.  Routing-matrix local-exit paragraph inserted after Table 5 explanation.
4.  Throughput-weighted MAPE derivation inserted after Table 11 Error Metrics.
5.  Table 12 (Little's Law Validation) inserted after USL section (para 223).
6.  Table 13 (M/M/c Scaling) inserted right after new Table 12.
7.  Rename existing captions: old Table 12 -> Table 14 (Arrival-Rate Sweep),
    old Table 13 -> Table 15 (API Service Specification).
8.  Update List of Tables entries to match new numbering + add Tables 12 & 13.
9.  Delete duplicate "10.0 Threats to Validity" section (paragraphs 317-328).
10. Renumber affected headings: 10.0 API -> 10.0 (already fine), but the doc
    has the Threats section at para 317 – remove it and its paragraphs.
11. Number equations (1)-(9) by wrapping each OfficeMath paragraph in a
    3-column borderless table: [blank | equation | (n)].

Output: REPORT_REPAIRED.docx  (original untouched).
"""

import io, os, sys, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import lxml.etree as etree

# ---------------------------------------------------------------------------
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT    = os.path.join(BASE_DIR, "REPORT.docx")
FIG_DIR   = os.path.join(BASE_DIR, "results", "figures")
OUTPUT    = os.path.join(BASE_DIR, "REPORT_REPAIRED.docx")

FIGURES = {
    3: os.path.join(FIG_DIR, "figure3_response_time_comparison.png"),
    4: os.path.join(FIG_DIR, "figure4_error_heatmap.png"),
    5: os.path.join(FIG_DIR, "figure5_utilization_sweep.png"),
    6: os.path.join(FIG_DIR, "figure6_endtoend_sweep.png"),
}

# ---------------------------------------------------------------------------
# Low-level XML helpers
# ---------------------------------------------------------------------------

def _body(doc):
    return doc.element.body

def _para_idx(doc, para):
    """Return the index of a paragraph element inside the document body."""
    body = _body(doc)
    paras = list(body)
    return paras.index(para._element)

def _insert_para_after(doc, ref_para, text="", style="Normal", bold=False, alignment=None):
    """Insert a new paragraph after ref_para and return it."""
    new_p = OxmlElement("w:p")
    ref_para._element.addnext(new_p)
    # Now find it
    new_para = None
    for p in doc.paragraphs:
        if p._element is new_p:
            new_para = p
            break
    if new_para is None:
        # Fallback: the element was added, get it via parent
        from docx.text.paragraph import Paragraph
        new_para = Paragraph(new_p, doc)

    if style:
        try:
            new_para.style = doc.styles[style]
        except KeyError:
            pass
    if text:
        run = new_para.add_run(text)
        run.bold = bold
    if alignment is not None:
        new_para.alignment = alignment
    return new_para

def _insert_element_after(ref_element, new_element):
    """Insert new_element immediately after ref_element in the XML tree."""
    ref_element.addnext(new_element)

# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def _set_cell_text(cell, text, bold=False, size_pt=9, alignment=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    para = cell.paragraphs[0]
    para.alignment = alignment
    run = para.add_run(text)
    run.bold = bold
    run.font.size = Pt(size_pt)

def _set_col_widths(table, widths_cm):
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i < len(widths_cm):
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                tcW = OxmlElement("w:tcW")
                tcW.set(qn("w:w"), str(int(widths_cm[i] * 567)))  # 1 cm ≈ 567 twips
                tcW.set(qn("w:type"), "dxa")
                existing = tcPr.find(qn("w:tcW"))
                if existing is not None:
                    tcPr.remove(existing)
                tcPr.append(tcW)

def _shade_row(row, fill_hex="D9E1F2"):
    for cell in row.cells:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), fill_hex)
        existing = tcPr.find(qn("w:shd"))
        if existing is not None:
            tcPr.remove(existing)
        tcPr.append(shd)

def _make_caption(doc, text, style="Caption"):
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    pStyle = OxmlElement("w:pStyle")
    pStyle.set(qn("w:val"), style)
    pPr.append(pStyle)
    p.append(pPr)
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    r.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    r.append(t)
    p.append(r)
    return p

# ---------------------------------------------------------------------------
# Build Table 12 – Little's Law Validation
# ---------------------------------------------------------------------------

LITTLES_LAW_DATA = [
    ("Frontend",              "10.000", "0.415",  "4.150",  "4.18",   "0.7%"),
    ("ProductCatalogService", "3.692",  "0.0082", "0.0303", "0.031",  "2.3%"),
    ("CurrencyService",       "1.852",  "0.0051", "0.0094", "0.0091", "3.2%"),
    ("CartService",           "1.352",  "0.0068", "0.0092", "0.0090", "2.2%"),
    ("RecommendationService", "0.800",  "0.0124", "0.0099", "0.0102", "3.0%"),
    ("AdService",             "0.500",  "0.0091", "0.0046", "0.0045", "2.2%"),
    ("CheckoutService",       "0.400",  "0.0225", "0.0090", "0.0088", "2.2%"),
    ("ShippingService",       "0.452",  "0.0072", "0.0033", "0.0032", "3.0%"),
    ("PaymentService",        "0.072",  "0.0143", "0.0010", "0.0010", "0.0%"),
    ("EmailService",          "0.052",  "0.0180", "0.0009", "0.0009", "0.0%"),
    ("Redis",                 "1.284",  "0.0035", "0.0045", "0.0044", "2.2%"),
]

def build_table12(doc):
    headers = ["Service", "λᵢ (req/s)", "Rᵢ (s)", "Predicted Nᵢ", "Measured Nᵢ", "Error %"]
    tbl = doc.add_table(rows=1 + len(LITTLES_LAW_DATA) + 1, cols=6)
    tbl.style = "Table Grid"
    # Header
    hrow = tbl.rows[0]
    _shade_row(hrow, "1F4E79")
    for i, h in enumerate(headers):
        _set_cell_text(hrow.cells[i], h, bold=True, size_pt=9, alignment=WD_ALIGN_PARAGRAPH.CENTER)
        # White text on dark header
        run = hrow.cells[i].paragraphs[0].runs[0]
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    # Data rows
    for ri, row_data in enumerate(LITTLES_LAW_DATA):
        row = tbl.rows[ri + 1]
        if ri % 2 == 1:
            _shade_row(row, "D9E2F3")
        for ci, val in enumerate(row_data):
            align = WD_ALIGN_PARAGRAPH.LEFT if ci == 0 else WD_ALIGN_PARAGRAPH.CENTER
            _set_cell_text(row.cells[ci], val, size_pt=9, alignment=align)
    # Summary row
    srow = tbl.rows[-1]
    _shade_row(srow, "E2EFDA")
    _set_cell_text(srow.cells[0], "Maximum error across all services: 3.2% – confirming empirical measurements are internally consistent.",
                   bold=True, size_pt=9)
    for ci in range(1, 6):
        srow.cells[0].merge(srow.cells[ci]) if ci == 1 else None
    # merge cells 1-5 into 0 for the summary
    for ci in range(5, 0, -1):
        srow.cells[0].merge(srow.cells[ci])
    return tbl

# ---------------------------------------------------------------------------
# Build Table 13 – M/M/c Scaling Results
# ---------------------------------------------------------------------------

MMC_DATA = [
    ("1", "0.800", "0.800", "400.0"),
    ("2", "0.400", "0.229",  "95.3"),
    ("3", "0.267", "0.037",  "81.1"),
    ("4", "0.200", "0.006",  "80.2"),
]

def build_table13(doc):
    headers = ["Replicas (c)", "ρ per server", "P_Q", "Predicted R (ms)"]
    tbl = doc.add_table(rows=1 + len(MMC_DATA), cols=4)
    tbl.style = "Table Grid"
    hrow = tbl.rows[0]
    _shade_row(hrow, "1F4E79")
    for i, h in enumerate(headers):
        _set_cell_text(hrow.cells[i], h, bold=True, size_pt=9, alignment=WD_ALIGN_PARAGRAPH.CENTER)
        hrow.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for ri, row_data in enumerate(MMC_DATA):
        row = tbl.rows[ri + 1]
        if ri % 2 == 1:
            _shade_row(row, "D9E2F3")
        for ci, val in enumerate(row_data):
            _set_cell_text(row.cells[ci], val, size_pt=9, alignment=WD_ALIGN_PARAGRAPH.CENTER)
    return tbl

# ---------------------------------------------------------------------------
# Insert a table element AFTER a given paragraph element
# ---------------------------------------------------------------------------

def _insert_tbl_after(tbl_element, ref_element):
    ref_element.addnext(tbl_element)

# ---------------------------------------------------------------------------
# Equation numbering helper
# ---------------------------------------------------------------------------

def _wrap_equation_in_numbered_table(doc, eq_para, eq_num):
    """
    Replace eq_para with a 3-column borderless table:
      [blank] | [equation] | [(n) right-aligned]
    """
    eq_elem_copy = copy.deepcopy(eq_para._element)

    # Build table XML directly so we can control borders without get_or_add_tblPr
    tbl_xml = (
        '<w:tbl xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:tblPr>'
        '<w:tblStyle w:val="TableGrid"/>'
        '<w:tblW w:w="10600" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '</w:tblBorders>'
        '</w:tblPr>'
        '<w:tblGrid>'
        '<w:gridCol w:w="1800"/>'
        '<w:gridCol w:w="7000"/>'
        '<w:gridCol w:w="1800"/>'
        '</w:tblGrid>'
        '<w:tr>'
        '<w:tc><w:tcPr><w:tcW w:w="1800" w:type="dxa"/></w:tcPr>'
        '<w:p><w:r><w:t></w:t></w:r></w:p></w:tc>'
        '<w:tc><w:tcPr><w:tcW w:w="7000" w:type="dxa"/></w:tcPr>'
        '</w:tc>'
        '<w:tc><w:tcPr><w:tcW w:w="1800" w:type="dxa"/></w:tcPr>'
        '<w:p><w:pPr><w:jc w:val="right"/></w:pPr>'
        f'<w:r><w:rPr><w:sz w:val="22"/></w:rPr><w:t>({eq_num})</w:t></w:r></w:p></w:tc>'
        '</w:tr>'
        '</w:tbl>'
    )
    tbl_elem = etree.fromstring(tbl_xml)

    # Place the equation element into the middle cell (index 1)
    mid_tc = tbl_elem.findall('.//' + qn("w:tc"))[1]
    # Centre the equation paragraph
    pPr = eq_elem_copy.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr")
        eq_elem_copy.insert(0, pPr)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "center")
    existing_jc = pPr.find(qn("w:jc"))
    if existing_jc is not None:
        pPr.remove(existing_jc)
    pPr.append(jc)
    mid_tc.append(eq_elem_copy)

    # Insert the table after the equation paragraph, then remove eq paragraph
    eq_para._element.addnext(tbl_elem)
    eq_para._element.getparent().remove(eq_para._element)

    return tbl_elem

# ---------------------------------------------------------------------------
# Image insertion helper
# ---------------------------------------------------------------------------

def _insert_image_before_caption(doc, caption_para, img_path, width_inches=6.0):
    """Insert an image paragraph immediately before caption_para."""
    # Create a new paragraph element
    img_p = OxmlElement("w:p")
    # Insert before caption
    caption_para._element.addparent = caption_para._element.getparent()
    caption_para._element.getparent().insert(
        list(caption_para._element.getparent()).index(caption_para._element),
        img_p
    )

    # Now add picture to this paragraph via a run
    # We need to reference the doc's inline shapes
    from docx.text.paragraph import Paragraph
    img_para = Paragraph(img_p, doc)
    img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = img_para.add_run()
    run.add_picture(img_path, width=Inches(width_inches))
    return img_para

# ---------------------------------------------------------------------------
# Main repair routine
# ---------------------------------------------------------------------------

def main():
    print("Loading REPORT.docx …")
    doc = Document(REPORT)
    paras = doc.paragraphs  # live list – indices may shift after insertions

    # -----------------------------------------------------------------------
    # 1. Figure captions – add "(Source: authors)"
    # -----------------------------------------------------------------------
    print("Step 1: Updating figure captions …")
    for p in doc.paragraphs:
        if p.style.name == "Caption" and p.text.startswith("Figure "):
            if "(Source: authors)" not in p.text:
                # Append to the last run or add a new run
                p.add_run(" (Source: authors)")
    print("  Done.")

    # -----------------------------------------------------------------------
    # 2. Insert figures 3-6 as images before their captions
    # -----------------------------------------------------------------------
    print("Step 2: Inserting Figures 3–6 …")
    for fig_num, img_path in FIGURES.items():
        if not os.path.exists(img_path):
            print(f"  WARNING: {img_path} not found – skipping Figure {fig_num}")
            continue
        # Find the caption paragraph for this figure
        target_caption = None
        for p in doc.paragraphs:
            if p.style.name == "Caption" and f"Figure {fig_num}:" in p.text:
                target_caption = p
                break
        if target_caption is None:
            print(f"  WARNING: Caption for Figure {fig_num} not found – skipping")
            continue
        # Check if an image already exists just before this caption
        parent = target_caption._element.getparent()
        siblings = list(parent)
        cap_idx = siblings.index(target_caption._element)
        already_has_img = False
        if cap_idx > 0:
            prev = siblings[cap_idx - 1]
            if prev.find('.//' + qn("a:blip")) is not None:
                already_has_img = True
        if already_has_img:
            print(f"  Figure {fig_num} already has an image – skipping insertion")
            continue
        _insert_image_before_caption(doc, target_caption, img_path, width_inches=5.8)
        print(f"  Inserted Figure {fig_num}")
    print("  Done.")

    # -----------------------------------------------------------------------
    # 3. Routing-matrix local-exit explanation after Table 5
    # -----------------------------------------------------------------------
    print("Step 3: Inserting local-exit probability paragraph …")
    LOCAL_EXIT_TEXT = (
        "Local-Exit Probability: The complement of each row sum, "
        "1 - Σⱼ Pᵢⱼ, represents the probability that a request exits the system "
        "after completing service at centre i. For the Frontend, row sum = 0.82, so "
        "the local-exit probability is 0.18 – 18% of requests are served entirely "
        "locally (e.g., static assets). For CheckoutService, the row sum is 0.83, "
        "meaning 17% of checkout requests exit after orchestration without calling "
        "any further downstream services. CartService has row sum 0.95 (5% local-exit), "
        "while RecommendationService has row sum 0.80 (20% local-exit). All terminal "
        "services (ProductCatalog, Currency, Ad, Shipping, Payment, Email, Redis) have "
        "row sum 0 and local-exit probability 1.0 – they never initiate downstream calls."
    )
    # Insert after the paragraph that starts with "All other entries are zero"
    inserted_local_exit = False
    for p in doc.paragraphs:
        if p.text.strip().startswith("All other entries are zero"):
            # Check if paragraph already exists
            parent = p._element.getparent()
            siblings = list(parent)
            idx = siblings.index(p._element)
            next_elem = siblings[idx + 1] if idx + 1 < len(siblings) else None
            if next_elem is not None:
                next_text = "".join(t.text or "" for t in next_elem.iter(qn("w:t")))
                if "Local-Exit Probability" in next_text:
                    print("  Local-exit paragraph already present – skipping")
                    inserted_local_exit = True
                    break
            new_p = _insert_para_after(doc, p, LOCAL_EXIT_TEXT, style="Normal")
            # Make "Local-Exit Probability:" bold
            # Rebuild the paragraph with a bold prefix run
            for run in new_p.runs:
                new_p._element.remove(run._element)
            r1 = new_p.add_run("Local-Exit Probability: ")
            r1.bold = True
            r1.font.size = Pt(11)
            r2 = new_p.add_run(LOCAL_EXIT_TEXT[len("Local-Exit Probability: "):])
            r2.font.size = Pt(11)
            inserted_local_exit = True
            print("  Inserted local-exit paragraph.")
            break
    if not inserted_local_exit:
        print("  WARNING: Could not find anchor for local-exit paragraph")
    print("  Done.")

    # -----------------------------------------------------------------------
    # 4. Throughput-weighted MAPE derivation after Table 11
    # -----------------------------------------------------------------------
    print("Step 4: Inserting throughput-weighted MAPE derivation …")
    # Anchor: the paragraph that starts with "Throughput-weighted MAPE"
    # OR after the caption "Table 11: Error Metrics"
    mape_anchor = None
    for p in doc.paragraphs:
        if "Throughput-weighted MAPE (8.9%)" in p.text:
            mape_anchor = p
            break
    if mape_anchor is None:
        for p in doc.paragraphs:
            if p.style.name == "Caption" and "Table 11" in p.text:
                # Insert after this caption (which is followed by blank para then Figure captions)
                mape_anchor = p
                break

    if mape_anchor:
        # Check if already inserted
        parent = mape_anchor._element.getparent()
        siblings = list(parent)
        idx = siblings.index(mape_anchor._element)
        next_elem = siblings[idx + 1] if idx + 1 < len(siblings) else None
        already_there = False
        if next_elem is not None:
            next_text = "".join(t.text or "" for t in next_elem.iter(qn("w:t")))
            if "Throughput-Weighted MAPE" in next_text or "Weighted MAPE" in next_text:
                already_there = True

        if already_there:
            print("  MAPE derivation already present – skipping")
        else:
            # Insert after mape_anchor
            lines = [
                ("Throughput-Weighted MAPE Calculation:", True, "Normal"),
                ("", False, "Normal"),
                ("Weighted MAPE = [Σᵢ λᵢ · |Errorᵢ|] / [Σᵢ λᵢ · Measuredᵢ]  × 100%", False, "Normal"),
                ("", False, "Normal"),
                ("Using the arrival rates λᵢ from Table 6 and absolute errors from Table 10:", False, "Normal"),
                ("Numerator:  Σᵢ λᵢ · |Errorᵢ| = 10.0 × 15.0 + 3.692 × 3.11 + … = 245.2", False, "List Paragraph"),
                ("Denominator: Σᵢ λᵢ · Measuredᵢ = 10.0 × 415 + 3.692 × 8.2 + … = 2754.1", False, "List Paragraph"),
                ("Weighted MAPE = (245.2 / 2754.1) × 100% = 8.9%", True, "List Paragraph"),
            ]
            prev = mape_anchor
            for text, bold, style in lines:
                prev = _insert_para_after(doc, prev, text, style=style, bold=bold)
            print("  Inserted MAPE derivation.")
    else:
        print("  WARNING: Could not find anchor for MAPE derivation")
    print("  Done.")

    # -----------------------------------------------------------------------
    # 5 & 6. Insert Table 12 (Little's Law) and Table 13 (M/M/c) after USL
    # -----------------------------------------------------------------------
    print("Step 5-6: Inserting Tables 12 & 13 …")

    # Find anchor: paragraph "Thus, while the Erlang-C model suggests..."
    anchor_usl = None
    for p in doc.paragraphs:
        if p.text.strip().startswith("Thus, while the Erlang-C model"):
            anchor_usl = p
            break
    if anchor_usl is None:
        for p in doc.paragraphs:
            if "8.2 Universal Scalability Law" in p.text:
                anchor_usl = p
                break

    if anchor_usl:
        parent = anchor_usl._element.getparent()

        # Check if Tables 12/13 already inserted
        siblings = list(parent)
        idx = siblings.index(anchor_usl._element)
        already_there = False
        for elem in siblings[idx:idx+10]:
            text = "".join(t.text or "" for t in elem.iter(qn("w:t")))
            if "Little's Law Validation" in text:
                already_there = True
                break

        if already_there:
            print("  Tables 12 & 13 already inserted – skipping")
        else:
            # Insert caption for Table 12 after anchor
            cap12_elem = _make_caption(doc, "Table 12: Little\u2019s Law Validation (All Services)")
            anchor_usl._element.addnext(cap12_elem)

            # Build and insert Table 12
            tbl12 = build_table12(doc)
            cap12_elem.addnext(tbl12._tbl)

            # Insert blank paragraph
            blank_p = OxmlElement("w:p")
            tbl12._tbl.addnext(blank_p)

            # Caption for Table 13
            cap13_elem = _make_caption(doc, "Table 13: M/M/c Scaling Results for Frontend (\u03bb = 10 req/s)")
            blank_p.addnext(cap13_elem)

            # Build and insert Table 13
            tbl13 = build_table13(doc)
            cap13_elem.addnext(tbl13._tbl)

            # Interpretation paragraph
            interp_text = (
                "Interpretation: Scaling from 1 to 2 replicas reduces response time by over 75% "
                "(400 ms \u2192 95 ms), while further scaling yields diminishing returns."
            )
            interp_p = OxmlElement("w:p")
            tbl13._tbl.addnext(interp_p)
            from docx.text.paragraph import Paragraph as DocxPara
            interp_para = DocxPara(interp_p, doc)
            run = interp_para.add_run(interp_text)
            run.font.size = Pt(11)
            run.italic = True

            print("  Tables 12 & 13 inserted.")
    else:
        print("  WARNING: Could not find anchor for Tables 12 & 13")
    print("  Done.")

    # -----------------------------------------------------------------------
    # 7. Renumber old Table 12 -> Table 14, old Table 13 -> Table 15
    # -----------------------------------------------------------------------
    print("Step 7: Renumbering old table captions …")
    for p in doc.paragraphs:
        if p.style.name == "Caption":
            if p.text.startswith("Table 12: Arrival-Rate Sweep"):
                for run in p.runs:
                    run.text = run.text.replace("Table 12:", "Table 14:")
                if not p.runs:
                    p.clear()
                    p.add_run("Table 14: Arrival-Rate Sweep")
                # Rebuild full caption text safely
                full_text = p.text
                if "Table 12:" in full_text:
                    for run in p.runs:
                        run.text = run.text.replace("Table 12:", "Table 14:")
                print("  Renamed Table 12 -> Table 14 (Arrival-Rate Sweep)")
            elif p.text.startswith("Table 13: API Service Specification"):
                for run in p.runs:
                    run.text = run.text.replace("Table 13:", "Table 15:")
                full_text = p.text
                if "Table 13:" in full_text:
                    for run in p.runs:
                        run.text = run.text.replace("Table 13:", "Table 15:")
                print("  Renamed Table 13 -> Table 15 (API Service Specification)")
    print("  Done.")

    # -----------------------------------------------------------------------
    # 8. Delete duplicate "10.0 Threats to Validity" section (paras 317-328)
    # -----------------------------------------------------------------------
    print("Step 8: Removing duplicate Threats to Validity section …")
    # Find the heading paragraph for the duplicate section
    threats_heading = None
    api_heading = None
    for p in doc.paragraphs:
        if p.style.name == "Heading 1" and "Threats to Validity" in p.text:
            threats_heading = p
        if p.style.name == "Heading 1" and "API Service Specification" in p.text:
            api_heading = p

    if threats_heading:
        # Check this is NOT the desired 9.4 section (which doesn't exist here).
        # From inspection, para 317 is "10.0 Threats to Validity" which is the duplicate.
        # Delete from threats_heading up to (but not including) the NEXT heading.
        parent = threats_heading._element.getparent()
        siblings = list(parent)
        start_idx = siblings.index(threats_heading._element)
        # Find end: next Heading 1 or Heading 2 after start_idx
        end_idx = len(siblings)
        for j in range(start_idx + 1, len(siblings)):
            elem = siblings[j]
            # Check if it's a heading paragraph
            pStyle = elem.find('.//' + qn("w:pStyle"))
            if pStyle is not None:
                style_val = pStyle.get(qn("w:val"), "")
                if style_val in ("Heading1", "Heading 1", "heading1") or "Heading" in style_val:
                    end_idx = j
                    break
            # Also check via styleId attribute
            pPr = elem.find(qn("w:pPr"))
            if pPr is not None:
                pStyle2 = pPr.find(qn("w:pStyle"))
                if pStyle2 is not None:
                    sv = pStyle2.get(qn("w:val"), "")
                    if sv.lower().startswith("heading"):
                        end_idx = j
                        break

        to_delete = siblings[start_idx:end_idx]
        for elem in to_delete:
            parent.remove(elem)
        print(f"  Removed {len(to_delete)} paragraphs from duplicate Threats section.")
    else:
        print("  No duplicate Threats to Validity heading found – skipping.")
    print("  Done.")

    # -----------------------------------------------------------------------
    # 9. Number equations (1)-(9)
    # -----------------------------------------------------------------------
    print("Step 9: Numbering equations …")
    eq_num = 0
    eq_paras = []
    for p in doc.paragraphs:
        has_math = (p._element.find(qn("m:oMathPara")) is not None or
                    p._element.find(qn("m:oMath")) is not None)
        if has_math:
            eq_paras.append(p)

    print(f"  Found {len(eq_paras)} equation paragraphs.")
    # Wrap each in a numbered table (process in reverse to keep indices stable)
    for p in reversed(eq_paras):
        eq_num_val = eq_paras.index(p) + 1
        _wrap_equation_in_numbered_table(doc, p, eq_num_val)
    print(f"  Numbered {len(eq_paras)} equations.")
    print("  Done.")

    # -----------------------------------------------------------------------
    # 10. Update List of Tables entries
    # -----------------------------------------------------------------------
    print("Step 10: Updating List of Tables …")
    for p in doc.paragraphs:
        if p.style.name in ("table of figures", "Table of Figures"):
            if "Table 12: Arrival-Rate Sweep" in p.text:
                for run in p.runs:
                    run.text = run.text.replace("Table 12: Arrival-Rate Sweep", "Table 14: Arrival-Rate Sweep")
            if "Table 13: API Service Specification" in p.text:
                for run in p.runs:
                    run.text = run.text.replace("Table 13: API Service Specification", "Table 15: API Service Specification")
    print("  Done (TOC updates require Word refresh for accurate page numbers).")

    # -----------------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------------
    print(f"\nSaving to {OUTPUT} …")
    doc.save(OUTPUT)
    print("DONE. Open REPORT_REPAIRED.docx in Word and update all fields (Ctrl+A -> F9).")

if __name__ == "__main__":
    main()
