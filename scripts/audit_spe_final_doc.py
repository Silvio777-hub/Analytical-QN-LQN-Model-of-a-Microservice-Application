import docx
import sys
sys.stdout.reconfigure(encoding='utf-8')

def audit():
    doc = docx.Document('SPEFinal.docx')
    print('=== SPEFinal.docx AUDIT ===')
    print(f'Total paragraphs: {len(doc.paragraphs)}')
    print(f'Total tables: {len(doc.tables)}')
    print(f'Total inline shapes: {len(doc.inline_shapes)}')

    print('\n=== REFERENCES SECTION ===')
    refs = []
    in_ref = False
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip() == 'References':
            in_ref = True
            continue
        if in_ref:
            if p.text.startswith('Appendix') or p.text.startswith('Glossary'):
                in_ref = False
                continue
            if p.text.strip():
                refs.append((i, p.text.strip()))

    for r in refs:
        print(f'  {r[1][:100]}...')
    print(f'\nTotal references: {len(refs)}')

    print('\n=== EMBEDDED FIGURES ===')
    figures_found = 0
    for i, p in enumerate(doc.paragraphs):
        drawings = p._p.xpath('.//w:drawing')
        if drawings:
            figures_found += 1
            caption = ''
            for j in range(i+1, min(i+4, len(doc.paragraphs))):
                if doc.paragraphs[j].text.strip():
                    caption = doc.paragraphs[j].text.strip()
                    break
            print(f'  Figure {figures_found} at Para {i}: Caption -> "{caption[:80]}"')
    print(f'\nTotal embedded figures/graphics: {figures_found}')

    print('\n=== ALL 12 TABLES SUMMARY ===')
    for ti, t in enumerate(doc.tables):
        hdr = [c.text.strip().replace('\n', ' ') for c in t.rows[0].cells]
        print(f'  Table {ti:2d}: {len(t.rows):2d} rows x {len(t.columns):2d} cols | Header: {hdr[:3]}')

    PROBLEMS = ['Code Analysis (Jaeger parser gap)', 'Source Code Estimate', '6.80 ms CPU', '85.00', 'TODO', 'TBD', 'FIXME', 'XXX']
    anomalies = []
    for i, p in enumerate(doc.paragraphs):
        for pr in PROBLEMS:
            if pr.lower() in p.text.lower():
                anomalies.append((f'Para {i}', pr, p.text[:80]))

    for ti, t in enumerate(doc.tables):
        for ri, r in enumerate(t.rows):
            for ci, c in enumerate(r.cells):
                for pr in PROBLEMS:
                    if pr.lower() in c.text.lower():
                        anomalies.append((f'Table {ti} R{ri}C{ci}', pr, c.text[:60]))

    print(f'\nTotal anomalies found: {len(anomalies)}')
    for a in anomalies:
        print(' ', a)

if __name__ == '__main__':
    audit()
