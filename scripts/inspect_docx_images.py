import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document

doc = Document('SPEFinal.docx')
print('=== Relationships in SPEFinal.docx ===')
for rel_id, rel in doc.part.rels.items():
    if 'image' in rel.reltype:
        print(f'  {rel_id} -> {rel.target_ref}')

print('\n=== Paragraph drawings and their blip r:embed ===')
for i, p in enumerate(doc.paragraphs):
    blips = p._p.xpath('.//a:blip')
    if blips:
        for b in blips:
            embed_id = b.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            rel = doc.part.rels.get(embed_id)
            target = rel.target_ref if rel else 'unknown'
            caption = ''
            for j in range(i+1, min(i+4, len(doc.paragraphs))):
                if doc.paragraphs[j].text.strip():
                    caption = doc.paragraphs[j].text.strip()
                    break
            print(f'  P{i:3d}: rId={embed_id} -> {target} | Caption: "{caption[:70]}"')
