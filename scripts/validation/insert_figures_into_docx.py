import argparse
import os
from pathlib import Path
from docx import Document
from docx.shared import Inches

def insert_figures(doc_path: Path, figures_dir: Path, caption_prefix: str = "Figure"):
    """Insert all PNG figures from *figures_dir* into the DOCX at *doc_path*.
    If a paragraph contains the placeholder text "{{FIGURES}}", insert after it;
    otherwise, append at the end of the document.
    """
    doc = Document(str(doc_path))
    # Find placeholder paragraph index if exists
    placeholder_idx = None
    for i, para in enumerate(doc.paragraphs):
        if "{{FIGURES}}" in para.text:
            placeholder_idx = i
            # Remove placeholder text so it doesn't appear
            para.text = para.text.replace("{{FIGURES}}", "")
            break
    # Gather sorted figure files
    figure_files = sorted(figures_dir.glob("*.png"))
    for idx, fig_path in enumerate(figure_files, start=1):
        # Insert a new paragraph for image
        if placeholder_idx is not None:
            p = doc.paragraphs[placeholder_idx].insert_paragraph_before()
            # Increment placeholder index so subsequent inserts keep order
            placeholder_idx += 1
        else:
            p = doc.add_paragraph()
        run = p.add_run()
        run.add_picture(str(fig_path), width=Inches(6))
        # Add caption below the image
        caption = f"{caption_prefix} {idx}: {fig_path.stem.replace('_', ' ')}"
        doc.add_paragraph(caption)
    doc.save(str(doc_path))
    print(f"Inserted {len(figure_files)} figures into {doc_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Insert generated figures into one or more DOCX reports.")
    parser.add_argument("docs", nargs="+", help="Paths to DOCX files to modify.")
    parser.add_argument("--figures", default="results/figures", help="Directory containing PNG figures.")
    parser.add_argument("--caption-prefix", default="Figure", help="Prefix for figure captions.")
    args = parser.parse_args()
    figures_dir = Path(args.figures)
    if not figures_dir.is_dir():
        raise FileNotFoundError(f"Figures directory not found: {figures_dir}")
    for doc_path in args.docs:
        insert_figures(Path(doc_path), figures_dir, args.caption_prefix)


if __name__ == "__main__":
    main()
