import docx
import sys

sys.stdout.reconfigure(encoding="utf-8")

def update_appendix_a():
    doc = docx.Document('SPEFinal.docx')
    t9 = doc.tables[9]

    def set_cell(row, col, text):
        t9.rows[row].cells[col].paragraphs[0].text = text
        for p in t9.rows[row].cells[col].paragraphs[1:]:
            p.text = ""

    # Row 1 (A.1)
    set_cell(1, 3, "Frontend: S₀ = 18.88 ms empirical CPU demand from 2,386 Jaeger spans (Isolates pure CPU execution)")

    # Row 3 (A.3)
    set_cell(3, 3, "ProductCatalog: 6.369 / 10.0 = 0.6369 visits/req; CartService: 0.0399 visits/req")

    # Row 4 (A.4)
    set_cell(4, 3, "Frontend at 10 req/s: 10 × 0.01888 = 0.1888 (18.88% load)")

    # Row 5 (A.5)
    set_cell(5, 3, "Frontend at 10 req/s: 18.88 / (1 − 0.1888) = 23.27 ms; At 5 req/s: 18.88 / (1 − 0.0944) = 20.85 ms")

    # Row 6 (A.6)
    set_cell(6, 3, "Frontend at 10 req/s: 10 × 0.02327 = 0.233 jobs in system")

    # Row 7 (A.7)
    set_cell(7, 3, "Weighted sum at 10 req/s = 28.1 ms (Frontend contributes 82.8% of uncontended system latency)")

    # Row 8 (A.8)
    set_cell(8, 3, "1 / 0.01888 = 52.97 req/s saturation ceiling (Theoretical uncontended capacity for 1 Frontend pod)")

    # Row 9 (A.9)
    set_cell(9, 3, "Frontend leverage: 1.0 / (1 − 0.1888)² = 1.5197 ms/ms speedup")

    # Row 10 (A.10)
    set_cell(10, 3, "c = 3, a = 0.1888 Erlangs ⟹ C(3, 0.1888) = 0.11% queue probability")

    # Row 11 (A.11)
    set_cell(11, 3, "c = 3 at 10 req/s ⟹ R₀(3) = 18.89 ms (Eliminates gateway queueing buffer)")

    # Row 12 (A.12)
    set_cell(12, 3, "N = 3 pods ⟹ X(3) = 148.75 req/s capacity ceiling (Parameters: σ = 0.0248 contention, κ = 0.0031 coherency)")

    # Row 13 (A.13)
    set_cell(13, 3, "N = 3 pods ⟹ η(3) = 93.6% scaling efficiency (2.81× effective capacity gain at 3 replicas)")

    # Row 14 (A.14)
    set_cell(14, 1, "Multi-Tier Validation (WMAPE)")
    set_cell(14, 2, "WMAPE = Σ|R_pred − R_obs| / Σ R_obs × 100%")
    set_cell(14, 3, "WMAPE = 82.81%, R² = −0.986 across 4 empirical tiers (2, 5, 8, 10 req/s). Demonstrates Docker desktop contention.")

    # Row 15 (A.15)
    set_cell(15, 1, "Empirical Tiers Available")
    set_cell(15, 2, "n = 4")
    set_cell(15, 3, "All 4 tiers (2.0, 5.0, 8.0, 10.0 req/s) measured live in multitier_empirical_measurements.csv.")

    # Row 16 (A.16)
    set_cell(16, 3, "Frontend: 1.0 × 18.88 = 18.88 ms demand; CartService: 0.0399 × 35.23 = 1.406 ms")

    # Row 17 (A.17)
    set_cell(17, 3, "Frontend captures 56.44% of Total ROI; ProductCatalog = 23.76%; Currency = 10.39%. Sum of sensitivity = 2.6925 ms/ms.")

    doc.save('SPEFinal.docx')
    print("Updated Table 9 (Appendix A) in SPEFinal.docx successfully!")

if __name__ == '__main__':
    update_appendix_a()
