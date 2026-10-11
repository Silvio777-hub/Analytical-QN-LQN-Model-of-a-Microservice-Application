import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document

doc = Document('Software Performance Engineering Course.docx')
print('=== Figure captions in Course.docx ===')
for i, p in enumerate(doc.paragraphs):
    if 'Figure ' in p.text:
        print(f'  P{i:3d}: "{p.text[:80]}"')
