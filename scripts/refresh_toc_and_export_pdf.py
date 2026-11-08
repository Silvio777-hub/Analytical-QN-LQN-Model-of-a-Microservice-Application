"""
refresh_toc_and_export_pdf.py
1. Open SPEFinal.docx in Word via COM automation.
2. Refresh all fields (TOC, LOF, LOT) with UpdateEntireTable.
3. Save the DOCX.
4. Export to PDF as SPEFinal_final.pdf.
5. Close Word without displaying.
"""
import sys, io, os, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import win32com.client as win32
from pathlib import Path

BASE = Path(r'c:\Users\7172981\Downloads\Analytical QNLQN Model of a Microservice Application - Oct')
DOCX = str(BASE / 'SPEFinal.docx')
PDF  = str(BASE / 'SPEFinal_final.pdf')

print(f'Opening: {DOCX}')
word = win32.DispatchEx('Word.Application')
word.Visible = False
word.DisplayAlerts = 0  # wdAlertsNone

try:
    doc = word.Documents.Open(DOCX)
    time.sleep(3)

    # Update all fields (triggers TOC/LOF/LOT dialogs suppressed by DisplayAlerts=0)
    doc.Fields.Update()
    time.sleep(1)

    # Also update each TOC/Index explicitly
    for i in range(1, doc.TablesOfContents.Count + 1):
        try:
            doc.TablesOfContents(i).Update()
            print(f'  Updated TOC #{i}')
        except Exception as e:
            print(f'  TOC #{i} update error: {e}')

    for i in range(1, doc.TablesOfFigures.Count + 1):
        try:
            doc.TablesOfFigures(i).Update()
            print(f'  Updated TOF/LOF #{i}')
        except Exception as e:
            print(f'  TOF #{i} update error: {e}')

    doc.Save()
    print(f'Saved DOCX: {DOCX}')

    # Export PDF  (ExportAsFixedFormat, wdExportFormatPDF=17)
    doc.ExportAsFixedFormat(
        OutputFileName=PDF,
        ExportFormat=17,       # wdExportFormatPDF
        OpenAfterExport=False,
        OptimizeFor=0,         # wdExportOptimizeForPrint
        Range=0,               # wdExportAllDocument
        Item=0,                # wdExportDocumentContent
        IncludeDocProps=True,
        KeepIRM=True,
        CreateBookmarks=1,     # wdExportCreateWordBookmarks
        DocStructureTags=True,
        BitmapMissingFonts=True,
        UseISO19005_1=False
    )
    print(f'PDF exported: {PDF}')

    doc.Close(SaveChanges=False)
finally:
    word.Quit()
    print('Word closed.')

# Print final file sizes
for p in [DOCX, PDF]:
    size = os.path.getsize(p)
    print(f'  {Path(p).name}: {size:,} bytes')
