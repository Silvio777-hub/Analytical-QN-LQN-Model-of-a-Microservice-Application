from docx import Document

doc = Document('SPEFinal.docx')
paras = doc.paragraphs
for pi, eq in [(47, 1), (62, 2), (80, 3), (88, 4), (94, 5), (106, 6), (139, 7)]:
    xml = paras[pi]._p.xml
    print(f"EQ ({eq}) Para {pi:03d}: has m:oMath = {':oMath' in xml}")
