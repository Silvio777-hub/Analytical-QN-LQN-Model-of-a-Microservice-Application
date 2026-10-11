import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document

doc = Document('SPEFinal.docx')
print('=== Image locations in SPEFinal.docx ===')
for i, p in enumerate(doc.paragraphs):
    drawings = p._p.xpath('.//w:drawing')
    if drawings:
        caption = ''
        for j in range(i+1, min(i+5, len(doc.paragraphs))):
            t = doc.paragraphs[j].text.strip()
            if t:
                caption = t
                break
        ptext = p.text.strip()
        print(f'  Para {i:3d}: "{ptext[:60]}" | Caption: "{caption[:80]}"')
