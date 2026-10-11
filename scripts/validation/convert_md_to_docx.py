import os
import re
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def convert_md_to_docx(md_path, docx_path):
    doc = Document()

    # Set page margins (1 inch all around)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles & Colors
    NAVY = RGBColor(0x0A, 0x25, 0x40)
    DARK_BLUE = RGBColor(0x1A, 0x36, 0x5D)
    TEXT_DARK = RGBColor(0x2D, 0x37, 0x48)

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_table = False
    table_lines = []

    def flush_table():
        nonlocal in_table, table_lines
        if not table_lines:
            return
        
        # Parse table markdown
        rows_data = []
        for line in table_lines:
            line_str = line.strip()
            if line_str.startswith("|") and line_str.endswith("|"):
                # Ignore separator lines like |---|---|
                if re.match(r"^\|[\s\:\-\|]+\|$", line_str):
                    continue
                cells = [c.strip() for c in line_str.split("|")[1:-1]]
                rows_data.append(cells)
        
        if rows_data:
            num_rows = len(rows_data)
            num_cols = max(len(r) for r in rows_data)
            table = doc.add_table(rows=num_rows, cols=num_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            for r_idx, row in enumerate(rows_data):
                for c_idx, cell_text in enumerate(row):
                    if c_idx < num_cols:
                        cell = table.cell(r_idx, c_idx)
                        # Clean math delimiters like $S_i$ or \rho
                        clean_text = cell_text.replace("$", "").replace("\\rho", "ρ").replace("\\lambda", "λ")
                        cell.text = clean_text
                        
                        # Style headers vs data
                        if r_idx == 0:
                            set_cell_background(cell, "0A2540") # Navy header
                            for p in cell.paragraphs:
                                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                for run in p.runs:
                                    run.font.bold = True
                                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                                    run.font.size = Pt(10)
                        else:
                            bg_color = "EDF2F7" if r_idx % 2 == 1 else "FFFFFF"
                            set_cell_background(cell, bg_color)
                            for p in cell.paragraphs:
                                for run in p.runs:
                                    run.font.size = Pt(9.5)
                                    run.font.color.rgb = TEXT_DARK
        
        doc.add_paragraph() # Spacing
        in_table = False
        table_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Handle frontmatter separator
        if stripped == "---":
            if in_table:
                flush_table()
            i += 1
            continue

        # Check for markdown table line
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(stripped)
            i += 1
            continue

        if in_table:
            flush_table()

        if not stripped:
            i += 1
            continue

        # Headings
        if stripped.startswith("# "):
            p = doc.add_paragraph()
            run = p.add_run(stripped[2:].strip())
            run.font.size = Pt(22)
            run.font.bold = True
            run.font.color.rgb = NAVY
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(8)
        elif stripped.startswith("## "):
            p = doc.add_paragraph()
            run = p.add_run(stripped[3:].strip())
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = DARK_BLUE
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
        elif stripped.startswith("### "):
            p = doc.add_paragraph()
            run = p.add_run(stripped[4:].strip())
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = DARK_BLUE
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            p = doc.add_paragraph(style='List Bullet')
            clean_text = stripped[2:].strip()
            # Handle inline bolding **text**
            parts = re.split(r'(\*\*.*?\*\*)', clean_text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = p.add_run(part[2:-2])
                    run.font.bold = True
                else:
                    run = p.add_run(part)
                run.font.size = Pt(11)
                run.font.color.rgb = TEXT_DARK
            p.paragraph_format.space_after = Pt(4)
        elif re.match(r'^\d+\.\s', stripped):
            p = doc.add_paragraph(style='List Number')
            clean_text = re.sub(r'^\d+\.\s', '', stripped)
            parts = re.split(r'(\*\*.*?\*\*)', clean_text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = p.add_run(part[2:-2])
                    run.font.bold = True
                else:
                    run = p.add_run(part)
                run.font.size = Pt(11)
                run.font.color.rgb = TEXT_DARK
            p.paragraph_format.space_after = Pt(4)
        elif stripped.startswith("!["):
            # Image reference line
            match = re.search(r'\!\[(.*?)\]\((.*?)\)', stripped)
            if match:
                alt_text, img_rel_path = match.groups()
                img_full_path = os.path.normpath(os.path.join(os.path.dirname(md_path), img_rel_path))
                if os.path.exists(img_full_path):
                    p_img = doc.add_paragraph()
                    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    doc.add_picture(img_full_path, width=Inches(5.5))
                    p_cap = doc.add_paragraph()
                    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    r_cap = p_cap.add_run(alt_text)
                    r_cap.font.italic = True
                    r_cap.font.size = Pt(9.5)
                    r_cap.font.color.rgb = RGBColor(0x71, 0x80, 0x96)
        else:
            p = doc.add_paragraph()
            clean_text = stripped.replace("$", "").replace("\\rho", "ρ").replace("\\lambda", "λ")
            parts = re.split(r'(\*\*.*?\*\*)', clean_text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = p.add_run(part[2:-2])
                    run.font.bold = True
                else:
                    run = p.add_run(part)
                run.font.size = Pt(11)
                run.font.color.rgb = TEXT_DARK
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15

        i += 1

    if in_table:
        flush_table()

    doc.save(docx_path)
    print(f"Successfully converted {md_path} → {docx_path}")

if __name__ == "__main__":
    md_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs", "FINAL_REPORT.md"))
    docx_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "FINAL_REPORT_Submitted.docx"))
    convert_md_to_docx(md_file, docx_file)
