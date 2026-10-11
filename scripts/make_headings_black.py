"""
make_headings_black.py - Post-processing script to convert Word document heading colors to black.
"""
import os
from docx import Document
from docx.shared import RGBColor

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docx_path = os.path.join(base_dir, "docs", "FINAL_REPORT.docx")

    if not os.path.exists(docx_path):
        print(f"Error: {docx_path} does not exist. Run Pandoc compile first.")
        return

    print(f"Loading {docx_path}...")
    doc = Document(docx_path)
    
    modified_count = 0
    for p in doc.paragraphs:
        # Check if the paragraph style is a Heading
        if p.style and p.style.name and p.style.name.startswith("Heading"):
            for run in p.runs:
                # Set color to black (RGB 0, 0, 0)
                run.font.color.rgb = RGBColor(0, 0, 0)
                modified_count += 1

    doc.save(docx_path)
    print(f"Successfully converted heading styles to black (modified {modified_count} text runs).")

if __name__ == "__main__":
    main()
