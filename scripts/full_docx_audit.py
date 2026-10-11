"""
full_docx_audit.py — Post-edit audit of SPEFinal.docx.
Checks that old forbidden values are gone and new canonical values are present.
Updated: October 2026 rebuild (v2.0-october-final).
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from docx import Document

doc = Document("SPEFinal.docx")
full_text = "\n".join(p.text for p in doc.paragraphs)
table_text = ""
for tbl in doc.tables:
    for row in tbl.rows:
        table_text += " | ".join(c.text.strip() for c in row.cells) + "\n"
all_text = full_text + "\n" + table_text

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

print("\n--- FORBIDDEN VALUES (must be absent) ---")
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

print("\n--- REQUIRED VALUES (must be present) ---")
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
