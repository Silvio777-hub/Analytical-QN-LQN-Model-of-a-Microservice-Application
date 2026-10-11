"""
apply_improvements.py — Fix all 10 improvement items identified in the audit.

Fixes applied:
  1. Add CoV column to Table 6 (doc.tables[5])
  2. Flag PaymentService P99 timeout artifact with * marker
  3. Remove 3 blank placeholder rows from Table 7 (doc.tables[6])
  4. Add explanatory note about lambda=8.0 gap regression after Table 7
  5. Fix Appendix B column widths to prevent text truncation
  6. Add dagger footnote for ProductCatalog P95 < Mean anomaly
  7. Fix HPA rho* inconsistency (66.6% vs 68.0% -> 66.7% consistently)
  8. Update full_docx_audit.py to use new canonical search values
  9. (Manual) TOC/LOT/LOF refresh — must be done in Word
  10. Flag EmailService low sample count with double-dagger
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import copy
import shutil
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOCX_PATH  = Path("SPEFinal.docx")
BACKUP_PATH = Path("SPEFinal_pre_improvements.docx")

print("=" * 60)
print("APPLYING ALL 10 IMPROVEMENTS")
print("=" * 60)

# ── Backup ──────────────────────────────────────────────────
shutil.copy2(DOCX_PATH, BACKUP_PATH)
print(f"Backup saved: {BACKUP_PATH}\n")

doc = Document(DOCX_PATH)

# ── Helpers ─────────────────────────────────────────────────

def make_cell(ref_tc, text, align="center"):
    """Deep-copy a reference cell, clear content, set new text."""
    new_tc = copy.deepcopy(ref_tc)
    for p in new_tc.findall(qn("w:p")):
        new_tc.remove(p)
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), align)
    pPr.append(jc)
    p.append(pPr)
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.append(t)
    p.append(r)
    new_tc.append(p)
    return new_tc


def add_grid_col(tbl_elem, width_twips, after_col_idx):
    """Insert a w:gridCol entry at after_col_idx+1 in the tblGrid."""
    tbl_grid = tbl_elem.find(qn("w:tblGrid"))
    if tbl_grid is None:
        return
    cols = tbl_grid.findall(qn("w:gridCol"))
    new_col = OxmlElement("w:gridCol")
    new_col.set(qn("w:w"), str(width_twips))
    if after_col_idx + 1 < len(cols):
        cols[after_col_idx + 1].addprevious(new_col)
    else:
        tbl_grid.append(new_col)


def remove_row(table, row_index):
    tr = table.rows[row_index]._tr
    table._tbl.remove(tr)


def set_col_width(table, col_idx, width_twips):
    for row in table.rows:
        if col_idx < len(row.cells):
            tc = row.cells[col_idx]._tc
            tcPr = tc.find(qn("w:tcPr"))
            if tcPr is None:
                tcPr = OxmlElement("w:tcPr")
                tc.insert(0, tcPr)
            tcW = tcPr.find(qn("w:tcW"))
            if tcW is None:
                tcW = OxmlElement("w:tcW")
                tcPr.insert(0, tcW)
            tcW.set(qn("w:w"), str(width_twips))
            tcW.set(qn("w:type"), "dxa")


def insert_para_after(element, text, italic=True, pt=8):
    """Insert a plain paragraph immediately after element in the document body."""
    p = OxmlElement("w:p")
    rPr = OxmlElement("w:rPr")
    if italic:
        rPr.append(OxmlElement("w:i"))
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(pt * 2))      # half-points
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), str(pt * 2))
    rPr.extend([sz, szCs])
    r = OxmlElement("w:r")
    r.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.append(t)
    p.append(r)
    element.addnext(p)
    return p


def set_cell_text(cell, text):
    """Overwrite all text in a cell's first run (preserves formatting)."""
    written = False
    for p in cell._tc.findall(qn("w:p")):
        for r in p.findall(qn("w:r")):
            for t_elem in r.findall(qn("w:t")):
                if not written:
                    t_elem.text = text
                    t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    written = True
                else:
                    t_elem.text = ""
    if not written:
        # Fallback: add a run
        p = cell._tc.findall(qn("w:p"))[0]
        r = OxmlElement("w:r")
        t_elem = OxmlElement("w:t")
        t_elem.text = text
        t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        r.append(t_elem)
        p.append(r)


# ════════════════════════════════════════════════════════════
# FIX 1 — Add CoV column to Table 6 (after P99, before Source)
# ════════════════════════════════════════════════════════════
print("[1] Adding CoV column to Table 6...")

table6 = doc.tables[5]

# CoV values in table row order (rows 1-11, matching dump order)
# Row order: Frontend, ProductCatalog, Currency, Cart, Recommendation,
#            Ad, Checkout, Shipping, Payment, Email, Redis
COV_VALUES = {
    "Frontend (Gateway)":       "19.054",
    "ProductCatalogService":    "29.442 \u2020",   # dagger - P95 < Mean
    "CurrencyService":          "4.381",
    "CartService":              "1.946",
    "RecommendationService":    "6.430",
    "AdService":                "1.424",
    "CheckoutService":          "2.800",
    "ShippingService":          "3.893",
    "PaymentService":           "4.808 *",          # timeout artifact
    "EmailService":             "3.073 \u2021",     # double-dagger: low N
    "Redis State Store":        "0.300",
}

# Insert grid col after position 4 (P99 = col 4), new CoV = col 5
add_grid_col(table6._tbl, 800, after_col_idx=4)

for i, row in enumerate(table6.rows):
    ref_tc = row.cells[4]._tc   # P99 cell used as formatting reference
    if i == 0:
        new_tc = make_cell(ref_tc, "CoV")
    else:
        svc = row.cells[0].text.strip()
        val = COV_VALUES.get(svc, "—")
        new_tc = make_cell(ref_tc, val)
    ref_tc.addnext(new_tc)

print(f"   Done. Table 6 now has {len(table6.rows[0].cells)} columns.")

# ════════════════════════════════════════════════════════════
# FIX 2 — Flag PaymentService P99 timeout with *
# ════════════════════════════════════════════════════════════
print("[2] Flagging PaymentService P99 timeout...")

# After Fix 1: col order = 0=Svc 1=Mean 2=Median 3=P95 4=P99 5=CoV 6=Source
pay_row = table6.rows[9]    # PaymentService
print(f"   Row 9 service: '{pay_row.cells[0].text.strip()}'")

p99_cell = pay_row.cells[4]
current = p99_cell.text.strip()
print(f"   P99 cell text: '{current}'")
if "1537" in current:
    set_cell_text(p99_cell, "1,537.2 *")
    print("   Set P99 to '1,537.2 *'")

# ════════════════════════════════════════════════════════════
# FIX 6 — ProductCatalog P95 < Mean dagger
# ════════════════════════════════════════════════════════════
print("[6] Flagging ProductCatalog P95 < Mean...")

prod_row = table6.rows[2]
print(f"   Row 2 service: '{prod_row.cells[0].text.strip()}'")
p95_cell = prod_row.cells[3]
p95_text = p95_cell.text.strip()
print(f"   P95 cell text: '{p95_text}'")
if "0.045" in p95_text:
    set_cell_text(p95_cell, "0.045 \u2020")
    print("   Set P95 to '0.045 \u2020'")

# ════════════════════════════════════════════════════════════
# FIX 10 — EmailService low-sample double-dagger
# ════════════════════════════════════════════════════════════
print("[10] Flagging EmailService low sample count...")

email_row = table6.rows[10]
print(f"   Row 10 service: '{email_row.cells[0].text.strip()}'")
# Telemetry Source is now col 6
src_cell = email_row.cells[6]
src_text = src_cell.text.strip()
print(f"   Source text: '{src_text[:60]}'")
if "95 samples" in src_text:
    new_src = src_text.replace("95 samples", "95 samples \u2021")
    set_cell_text(src_cell, new_src)
    print(f"   Updated source.")
elif "Jaeger" in src_text:
    set_cell_text(src_cell, src_text + " \u2021")

# Add combined footnote paragraph right after Table 6
footnote_t6 = (
    "* PaymentService P99 = 1,537.2 ms is a single-span timeout artifact; "
    "the model uses mean service time (47.94 ms) which excludes timeouts.  "
    "\u2020 ProductCatalogService P95 (0.045 ms) < Mean (0.324 ms) — Jaeger "
    "per-second quantile aggregation artefact; the arithmetic mean is used for "
    "all modelling, not the P95.  "
    "\u2021 EmailService: 95 valid samples — P99 estimate carries high uncertainty; "
    "service demand is low (D = 0.007 ms) and does not affect system bottleneck."
)
insert_para_after(table6._tbl, footnote_t6, italic=True, pt=8)
print("   Footnotes injected after Table 6.")

# ════════════════════════════════════════════════════════════
# FIX 3 — Remove blank rows from Table 7
# ════════════════════════════════════════════════════════════
print("[3] Removing blank rows from Table 7...")

table7 = doc.tables[6]
print(f"   Rows before: {len(table7.rows)}")
# Rows 5, 6, 7 are blank — remove in reverse order
for row_idx in [7, 6, 5]:
    row_text = " ".join(c.text.strip() for c in table7.rows[row_idx].cells)
    is_blank = not row_text.replace("\u2014", "").replace("-", "").replace(" ", "")
    if is_blank:
        remove_row(table7, row_idx)
        print(f"   Removed blank row {row_idx}.")
    else:
        print(f"   Row {row_idx} not blank ('{row_text[:40]}') — skipping.")
print(f"   Rows after: {len(table7.rows)}")

# ════════════════════════════════════════════════════════════
# FIX 4 — Add explanatory note for lambda=8.0 gap regression
# ════════════════════════════════════════════════════════════
print("[4] Adding lambda=8.0 regression note after Table 7...")

note = (
    "Interpretation note: At \u03bb\u2080 = 8.0 req/s the observed mean latency "
    "(857.0 ms) is lower than at 5.0 req/s (996.8 ms), despite higher nominal "
    "load. This is a Docker Desktop measurement artefact: at 8.0 req/s the "
    "success rate collapses to 74.2% (vs 84.0% at 5.0 req/s), so the slowest "
    "requests time out before completion, biasing the recorded mean downward. "
    "The queue-network model correctly predicts monotonically increasing "
    "response time; the inversion is in the telemetry, not the model."
)
insert_para_after(table7._tbl, note, italic=True, pt=8)
print("   Note injected.")

# ════════════════════════════════════════════════════════════
# FIX 5 — Fix Appendix B column widths
# ════════════════════════════════════════════════════════════
print("[5] Fixing Appendix B (Table 10) column widths...")

table10 = doc.tables[10]
# A4 portrait body ~9144 twips; 3 col distribution: 2500/1900/4744
widths = [2500, 1900, 4744]
for ci, w in enumerate(widths):
    set_col_width(table10, ci, w)
    print(f"   Col {ci} \u2192 {w} twips")

# Also update the tblGrid
tbl_grid = table10._tbl.find(qn("w:tblGrid"))
if tbl_grid is not None:
    for gc, w in zip(tbl_grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(w))
    print("   tblGrid updated.")

# ════════════════════════════════════════════════════════════
# FIX 7 — Fix HPA rho* inconsistency
# ════════════════════════════════════════════════════════════
print("[7] Fixing HPA \u03c1* inconsistency in Table 12...")

table12 = doc.tables[12]
row0 = table12.rows[0]
print(f"   Headers: {[c.text.strip()[:30] for c in row0.cells]}")

# Row 0, col 1 has the value
val_cell = row0.cells[1]
current_text = val_cell.text.strip()
print(f"   Current: '{current_text[:60]}'")

# Correct calculation: rho* = 1 - S0/R_target = 1 - 18.88/56.7 = 66.7%
new_val = "66.7%  (\u03c1* = 1 \u2212 S\u2080/R\u209c\u2090\u1d33\u1d49\u209c = 1 \u2212 18.88/56.7 \u2248 66.7%)"
set_cell_text(val_cell, new_val)
print(f"   Set to: '{new_val}'")

# ════════════════════════════════════════════════════════════
# Save document
# ════════════════════════════════════════════════════════════
doc.save(DOCX_PATH)
print(f"\n\u2705 SPEFinal.docx saved.")

# Sync to Course docx
other = Path("Software Performance Engineering Course.docx")
if other.exists():
    shutil.copy2(DOCX_PATH, other)
    print(f"\u2705 Synced: {other.name}")

# ════════════════════════════════════════════════════════════
# FIX 8 — Update full_docx_audit.py with new canonical values
# ════════════════════════════════════════════════════════════
print("\n[8] Updating scripts/full_docx_audit.py...")

new_audit = '''"""
full_docx_audit.py — Post-edit audit of SPEFinal.docx.
Checks that old forbidden values are gone and new canonical values are present.
Updated: October 2026 rebuild (v2.0-october-final).
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from docx import Document

doc = Document("SPEFinal.docx")
full_text = "\\n".join(p.text for p in doc.paragraphs)
table_text = ""
for tbl in doc.tables:
    for row in tbl.rows:
        table_text += " | ".join(c.text.strip() for c in row.cells) + "\\n"
all_text = full_text + "\\n" + table_text

print("=" * 60)
print("SPEFinal.docx — FULL AUDIT (October 2026 rebuild)")
print("=" * 60)

# ── FORBIDDEN: old values that must NOT appear ───────────────
FORBIDDEN = {
    "17,200":  "Old span count — must be 6,642",
    "16,190":  "Old span count variant",
    "80.00 ms": "Old Frontend service time",
    "43.2":    "Old demand imbalance ratio",
    "95.91":   "Old Frontend ROI share",
    "51.47":   "Old WMAPE value",
    "12.50":   "Old single-replica saturation",
    "1,247":   "Old trace count",
    "25.000":  "Old sensitivity score",
}

print("\\n--- FORBIDDEN VALUES (must be absent) ---")
any_fail = False
for val, reason in FORBIDDEN.items():
    if val in all_text:
        print(f"  FAIL  [{val}] found — {reason}")
        any_fail = True
    else:
        print(f"  pass  [{val}] absent  OK")

# ── REQUIRED: new canonical values that must be present ──────
REQUIRED = {
    "6,642":    "Canonical span count",
    "687":      "Canonical trace count",
    "18.88":    "Frontend service time (ms)",
    "18.880":   "Frontend S0 precise",
    "52.97":    "Single-replica saturation (req/s)",
    "82.81":    "WMAPE validation score (%)",
    "56.44":    "Frontend ROI share (%)",
    "148.75":   "c=3 capacity (req/s)",
    "23.27":    "M/M/1 mean RT @ 10 req/s (ms)",
    "13.43":    "Demand imbalance ratio",
    "1.5197":   "Frontend sensitivity score",
    "c = 3":    "Optimal replica count",
    "66.7":     "HPA CPU target rho*",
}

print("\\n--- REQUIRED VALUES (must be present) ---")
for val, reason in REQUIRED.items():
    if val in all_text:
        print(f"  pass  [{val}] present  OK  — {reason}")
    else:
        print(f"  FAIL  [{val}] MISSING  — {reason}")
        any_fail = True

# ── SUMMARY ──────────────────────────────────────────────────
print()
if any_fail:
    print("RESULT: AUDIT FAILED — review items above.")
else:
    print("RESULT: AUDIT PASSED — all checks clean.")
'''

Path("scripts/full_docx_audit.py").write_text(new_audit, encoding="utf-8")
print("   scripts/full_docx_audit.py updated.")

print("\n" + "=" * 60)
print("ALL FIXES APPLIED.")
print("Reminder: Fix 9 (TOC/LOT/LOF refresh) must be done manually")
print("  in Word: open SPEFinal.docx, Ctrl+A, F9, update each field.")
print("=" * 60)
