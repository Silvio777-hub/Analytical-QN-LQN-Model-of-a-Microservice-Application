from docx import Document
import sys

doc = Document('SPE_final.docx')

print("=== ALL TABLE CONTENT ===")
for ti, table in enumerate(doc.tables):
    print(f"\n--- TABLE {ti} ---")
    for ri, row in enumerate(table.rows):
        row_texts = [c.text.strip()[:60] for c in row.cells]
        sep = " || "
        print(f"  Row {ri}: {sep.join(row_texts)}")

print(f"\nTotal tables: {len(doc.tables)}")
print(f"Total paras: {len(doc.paragraphs)}")

print("\n=== ALL PARAS WITH 6.80 or CoV or 0.85 or Code Analysis ===")
for i, p in enumerate(doc.paragraphs):
    t = p.text
    if any(x in t for x in ['6.80', 'CoV', '0.85', 'Code Analysis', 'code analysis',
                              'Source Code', '2.14', 'Jaeger Telemetry Spans']):
        print(f"  Para {i} [{p.style.name}]: {t[:200]}")
