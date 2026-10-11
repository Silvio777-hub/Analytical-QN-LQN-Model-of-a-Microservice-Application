"""inspect_tables.py — dump every table's cell contents for review."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document

doc = Document('SPEFinal.docx')

TARGET_TABLES = {
    0: "Terminology",
    1: "OJN vs LQN",
    2: "System Parameters",
    3: "Architecture",
    4: "Table 5 — Demand",
    5: "Table 6 — Empirical Breakdown",
    6: "Table 7 — Validation",
    7: "Table 8 — M/M/c Scaling",
    8: "Table 9 — Sensitivity",
    10: "Appendix B Constants",
    11: "Table 8.1 Multi-Tier Live",
    12: "HPA Policy",
}

for idx, label in TARGET_TABLES.items():
    tbl = doc.tables[idx]
    print(f"\n{'='*70}")
    print(f"doc.tables[{idx}] — {label}  ({len(tbl.rows)}r × {len(tbl.columns)}c)")
    print('='*70)
    for r, row in enumerate(tbl.rows):
        cells = [c.text.strip().replace('\n', ' ')[:35] for c in row.cells]
        print(f"  Row {r:2d}: {' | '.join(cells)}")
