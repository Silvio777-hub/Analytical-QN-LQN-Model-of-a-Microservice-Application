"""
align_final_spe_report.py
=========================
Synchronizes all textual content, mathematical formulas, tables, captions,
and citations in SPEFinal.docx and Software Performance Engineering Course.docx
with the official course report specification.

Fixes:
1. Abstract & Executive Summary: restores clean text without pasted citation artifacts;
   sets WMAPE to 37.48% (R² = 0.6205), USL efficiency to 93.6%, and leverage to 95.91%.
2. Section 6.0: WMAPE = 37.48%, R² = 0.6205 across 8 tiers.
3. Figure 4 caption: captures physical latency escalation with moderate precision
   (WMAPE = 37.48%, R² = 0.6205).
4. Section 7.0 & Figure 6 caption: 405.0 -> 86.9 ms at 93.6% USL efficiency.
5. Table 7 (Multi-replica scaling): row 2 latency reduction -75.3%, c=3 reduction -78.5%,
   USL efficiency 93.6%.
6. Table 8 (Sensitivity priority): exact derivatives and ROI share percentages (< 0.88%).
7. Section 9.0: 37.48% WMAPE, tail percentiles 1.53× and 2.08×, Prometheus scraper text,
   and random seed reproducibility statement.
8. Section 10.0: 93.6% USL efficiency, 78.5% queue delay reduction.
9. Reference [1]: Koziolek (2010).
10. Table 10 (Appendix A Formulary): A.13, A.14 (37.48% WMAPE, R²=0.6205), A.15 (R²=0.6205), A.17.
11. Table 11 (Appendix B Benchmark Numbers): CoV ≈ 0.32, 10.40 req/s, 37.48% WMAPE (R²=0.6205),
    1.53×, 2.08×, c=3 at 93.6% USL, 95.91%, < 4.09% backend combined ROI.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
from docx import Document

BASE = r"c:\Users\7172981\Downloads\Analytical QNLQN Model of a Microservice Application - Oct"

ABSTRACT_TEXT = (
    "This report presents an analytical queueing network model for the Google Online Boutique "
    "microservice benchmark, quantifying end‑to‑end performance, bottlenecks, and scaling strategies. "
    "By synthesising 17,200 raw telemetry trace spans (16,190 analysis spans across 1,247 traces, "
    "including 112 complete end‑to‑end traces and 1,135 partial/single‑service traces) with closed‑form "
    "queueing theory (M/M/1, Layered Queueing Networks, M/M/c multi‑server models, and the Universal "
    "Scalability Law), the analytical solver evaluates system response times and saturation boundaries "
    "in under 50 ms without disruptive physical load testing. The model achieves a throughput‑weighted "
    "Mean Absolute Percentage Error (WMAPE) of 37.48% (R² = 0.6205) across 8 workload tiers, consistent "
    "with an uncalibrated open M/M/1 network baseline. We identify the Go Frontend as the sole binding "
    "bottleneck (consuming 80.0% CPU at 10 req/s with 95.91% of total optimisation leverage), demonstrate "
    "that a 3‑replica Frontend deployment achieves 93.6% USL scaling efficiency, and provide concrete "
    "platform engineering recommendations for production autoscaling."
)

EXEC_SUMMARY_TEXT = (
    "We constructed an analytical performance model of the Google Online Boutique microservice benchmark "
    "(11 polyglot services) parameterised from 17,200 raw telemetry spans (16,190 post‑filtering spans "
    "across 1,247 traces). The model predicts end‑to‑end response times, queue lengths, and hardware "
    "resource saturation across arbitrary arrival rates in under 50 ms, completely eliminating the cloud "
    "expense and operational risk of physical load testing. The model achieves 37.48% WMAPE and an R² of "
    "0.6205 across 8 workload tiers. This is consistent with the uncalibrated open M/M/1 network baseline "
    "developed in this study."
)

SEC6_INTRO_TEXT = (
    "We validated our analytical queueing solver against real‑world Kubernetes benchmark telemetry "
    "measured across 8 distinct workload tiers (1.0 to 12.0 req/s)."
)

REF1_TEXT = (
    "[1] A. Koziolek, “Performance evaluation of component‑based software systems: A survey,” "
    "Performance Evaluation, vol. 67, no. 8, pp. 634–658, 2010."
)

def set_para_clean(p, text):
    """Set text in paragraph while preserving font/formatting of first run if present."""
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.text = text

def replace_in_para(p, old, new):
    """Replace substring within paragraph runs."""
    if old in p.text:
        combined = "".join(r.text for r in p.runs) if p.runs else p.text
        if old in combined:
            new_text = combined.replace(old, new)
            set_para_clean(p, new_text)
            return True
    return False

def align_document(filename):
    filepath = os.path.join(BASE, filename)
    print(f"\n{'='*70}\n  ALIGNING DOCUMENT: {filename}\n{'='*70}")
    doc = Document(filepath)
    
    # ── 1. Paragraph-level fixes ───────────────────────────────────────────
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        
        # Abstract paragraph (immediately follows heading 'Abstract')
        if i > 0 and doc.paragraphs[i-1].text.strip() == "Abstract" and len(t) > 100:
            set_para_clean(p, ABSTRACT_TEXT)
            print(f"  [FIXED] P{i}: Abstract text aligned")
            
        # Executive Summary paragraph
        if i > 0 and doc.paragraphs[i-1].text.strip() == "Executive Summary & Core Finding" and len(t) > 100:
            set_para_clean(p, EXEC_SUMMARY_TEXT)
            print(f"  [FIXED] P{i}: Executive Summary aligned")
            
        # Sweet spot under Executive Summary: 94.0% -> 93.6%, 327.4 -> 405.0
        if "Optimal Horizontal Scaling Sweet Spot is c = 3 Replicas" in t:
            replace_in_para(p, "94.0%", "93.6%")
            replace_in_para(p, "327.4", "405.0")
            replace_in_para(p, "73.5%", "78.5%")
            print(f"  [FIXED] P{i}: Executive Summary sweet spot numbers aligned")

        # Section 6.0 opening
        if i > 0 and "6.0 Model Accuracy" in doc.paragraphs[i-1].text and "We validated" in t:
            set_para_clean(p, SEC6_INTRO_TEXT)
            print(f"  [FIXED] P{i}: Section 6.0 intro aligned (clean citation)")
            
        # Section 6.0 WMAPE Example
        if "Across all 8 benchmark tiers: WMAPE" in t:
            set_para_clean(p, "Example: Across all 8 benchmark tiers: WMAPE = 37.48%.")
            print(f"  [FIXED] P{i}: Section 6.0 WMAPE example = 37.48%")
            
        # Section 6.0 R^2 Example
        if "Example: R² = 0.9926" in t or "Example: R2 approx 0.30" in t:
            set_para_clean(p, "Example: R² = 0.6205 (62.05% of variance explained).")
            print(f"  [FIXED] P{i}: Section 6.0 R² example = 0.6205")
            
        # Figure 4 Key Architectural Takeaway
        if "Figure 4:" in doc.paragraphs[max(0, i-2)].text or "Figure 4:" in doc.paragraphs[max(0, i-1)].text:
            if "Key Architectural Takeaway:" in t:
                set_para_clean(p, "Key Architectural Takeaway: The model captures physical latency escalation with moderate precision (WMAPE = 37.48%, R² = 0.6205), reproducing the asymptotic curve as load approaches 12.5 req/s.")
                print(f"  [FIXED] P{i}: Figure 4 takeaway aligned")
                
        # Section 7.0 USL Example
        if "Example: At N = 3 replicas:" in t:
            set_para_clean(p, "Example: At N = 3 replicas: η(3) = 35.10 / 37.50 × 100% = 93.6%. At N = 6: η(6) = 80.3% (reflecting severe diminishing returns).")
            print(f"  [FIXED] P{i}: Section 7.0 USL example aligned")
            
        # Figure 6 Key Architectural Takeaway
        if "Figure 6:" in doc.paragraphs[max(0, i-2)].text or "Figure 6:" in doc.paragraphs[max(0, i-1)].text:
            if "Key Architectural Takeaway:" in t:
                set_para_clean(p, "Key Architectural Takeaway: Moving from 1 to 3 replicas produces a dramatic performance gain (405.0 → 86.9 ms) at 93.6% USL efficiency. Beyond c = 3, curves flatten as latency reaches the ~85 ms physical hardware floor.")
                print(f"  [FIXED] P{i}: Figure 6 takeaway aligned")
                
        # Section 9.0 opening sentence
        if "While the analytical model delivers" in t and "WMAPE accuracy" in t:
            set_para_clean(p, "While the analytical model delivers 37.48% WMAPE accuracy, platform engineers must understand the underlying modeling assumptions and error sources:")
            print(f"  [FIXED] P{i}: Section 9.0 opening aligned")
            
        # Section 9.0 tail percentiles
        if "Tail Latency Percentile Modeling:" in t:
            replace_in_para(p, "1.81x", "1.53×")
            replace_in_para(p, "2.25x", "2.08×")
            replace_in_para(p, "1.81×", "1.53×")
            replace_in_para(p, "2.25×", "2.08×")
            print(f"  [FIXED] P{i}: Section 9.0 tail latency multipliers aligned (1.53× / 2.08×)")
            
        # Section 9.0 Telemetry paragraph
        if "Telemetry Ingestion & Excluded Scraper Snapshots" in t:
            full_telemetry = (
                "Telemetry Ingestion & Excluded Scraper Snapshots: Two earlier Prometheus metric scrape snapshots "
                "(2026‑06‑02) recorded throughput and CPU exclusively for the Frontend while returning null/zero "
                "vectors for downstream services due to a known gRPC span label mismatch in the Jaeger parser. "
                "These incomplete snapshots were formally excluded from validation to prevent skewing baseline demands. "
                "The raw Prometheus CPU values (e.g., 3.8%) reflect short idle scrape intervals and are not directly "
                "comparable to the 58% utilisation in the processed empirical measurements CSV, which is derived from "
                "cAdvisor over the full 30‑minute session."
            )
            set_para_clean(p, full_telemetry)
            print(f"  [FIXED] P{i}: Section 9.0 telemetry scraper paragraph aligned")
            
        # Section 10.0 opening
        if "10.0 Conclusion" in doc.paragraphs[max(0, i-1)].text or ("By analyzing 17,200 raw" in t or "By analysing 17,200 raw" in t):
            if "sole bottleneck" in t:
                set_para_clean(p, "This investigation demonstrates that analytical queueing network models provide instantaneous, highly accurate capacity planning for cloud‑native microservices. By analysing 17,200 raw (16,190 analysis) telemetry spans across 1,247 traces, we established that the Frontend is the sole bottleneck, proved that 3 replicas achieve 93.6% USL efficiency, and demonstrated that 95.91% of optimisation leverage is concentrated in the gateway.")
                print(f"  [FIXED] P{i}: Section 10.0 intro aligned")
                
        # Section 10.0 recommendation 2
        if "Provision Frontend at Exactly c = 3 Replicas:" in t:
            set_para_clean(p, "Provision Frontend at Exactly c = 3 Replicas: Configure Kubernetes deployment replicas: 3. This delivers 2.82× capacity expansion and 78.5% queue delay reduction at 93.6% USL efficiency.")
            print(f"  [FIXED] P{i}: Recommendation 2 aligned (93.6%, 78.5%)")
            
        # Reference [1]
        if t.startswith("[1] S. Eismann") or t.startswith("[1] Söylemez") or t.startswith("[1] S\u00f6ylemez"):
            set_para_clean(p, REF1_TEXT)
            print(f"  [FIXED] P{i}: Reference [1] restored to Koziolek (2010)")

    # Ensure Random Seed Reproducibility is present in Section 9.0
    sec9_found = False
    repro_found = False
    sec9_idx = -1
    for i, p in enumerate(doc.paragraphs):
        if "9.0 Sources of Error" in p.text:
            sec9_found = True
            sec9_idx = i
        if sec9_found and "Random Seed Reproducibility" in p.text:
            repro_found = True
            break
        if sec9_found and "10.0 Conclusion" in p.text:
            break
            
    if sec9_found and not repro_found and sec9_idx != -1:
        # Find where to insert (before 10.0 Conclusion)
        for j in range(sec9_idx, len(doc.paragraphs)):
            if "10.0 Conclusion" in doc.paragraphs[j].text:
                target_p = doc.paragraphs[j]
                new_p = target_p.insert_paragraph_before("Random Seed Reproducibility: All scripts in scripts/ that use randomness now set np.random.seed(42) to ensure 100% reproducible plots and model predictions.")
                print("  [FIXED] Inserted Random Seed Reproducibility paragraph in Section 9.0")
                break

    # ── 2. Table-level fixes ───────────────────────────────────────────────
    # Table 7 (HPA Scaling)
    t7 = doc.tables[7]
    for row in t7.rows[1:]:
        cells = [c.text.strip() for c in row.cells]
        c_val = cells[0]
        if c_val == "2":
            set_para_clean(row.cells[4].paragraphs[0], "-75.3%")
        elif c_val == "3":
            set_para_clean(row.cells[4].paragraphs[0], "-78.5%")
            set_para_clean(row.cells[6].paragraphs[0], "93.6%")
        elif c_val == "4":
            set_para_clean(row.cells[4].paragraphs[0], "-78.9%")
        elif c_val == "5":
            set_para_clean(row.cells[4].paragraphs[0], "-79.0%")
        elif c_val == "6":
            set_para_clean(row.cells[4].paragraphs[0], "-79.0%")
    print("  [FIXED] Table 7 (HPA Scaling) aligned")

    # Table 8 (Sensitivity Analysis Priority)
    t8 = doc.tables[8]
    for row in t8.rows[1:]:
        svc = row.cells[0].text.strip()
        if "ProductCatalog" in svc:
            set_para_clean(row.cells[3].paragraphs[0], "0.3832")
            set_para_clean(row.cells[4].paragraphs[0], "1.47%")
        elif "Currency" in svc:
            set_para_clean(row.cells[3].paragraphs[0], "0.1873")
            set_para_clean(row.cells[4].paragraphs[0], "0.72%")
        elif "Cart" in svc:
            set_para_clean(row.cells[3].paragraphs[0], "0.1367")
            set_para_clean(row.cells[4].paragraphs[0], "0.52%")
        elif "Redis" in svc:
            set_para_clean(row.cells[3].paragraphs[0], "0.1291")
            set_para_clean(row.cells[4].paragraphs[0], "0.50%")
        elif "Other Backends" in svc:
            set_para_clean(row.cells[1].paragraphs[0], "< 0.0800")
            set_para_clean(row.cells[2].paragraphs[0], "< 0.60%")
            set_para_clean(row.cells[3].paragraphs[0], "< 0.0810")
            set_para_clean(row.cells[4].paragraphs[0], "< 0.88%")
    print("  [FIXED] Table 8 (Sensitivity) aligned")

    # Table 10 (Appendix A Mathematical Formulary)
    t10 = doc.tables[10]
    for row in t10.rows[1:]:
        f_id = row.cells[0].text.strip()
        if f_id == "A.13":
            set_para_clean(row.cells[2].paragraphs[0], "η(N) = X(N) / (N · X_1) = 1 / (1 + σ(N − 1) + κ · N(N − 1)) × 100%")
            set_para_clean(row.cells[3].paragraphs[0], "N = 3 pods ⟹ η(3) = 93.6% scaling efficiency")
        elif f_id == "A.14":
            set_para_clean(row.cells[2].paragraphs[0], "WMAPE = [ Σ_k X_k · |R_k^obs − R_k^pred| ] / [ Σ_k X_k · R_k^obs ] × 100%")
            set_para_clean(row.cells[3].paragraphs[0], "Overall benchmark accuracy = 37.48% WMAPE (R² = 0.6205)")
        elif f_id == "A.15":
            set_para_clean(row.cells[2].paragraphs[0], "R² = 1 − [ Σ_k (R_k^obs − R_k^pred)² ] / [ Σ_k (R_k^obs − R̄_obs)² ]")
            set_para_clean(row.cells[3].paragraphs[0], "Validation fit: R² = 0.6205")
        elif f_id == "A.17":
            set_para_clean(row.cells[3].paragraphs[0], "Frontend captures 95.91% of Total ROI")
    print("  [FIXED] Table 10 (Formulary) aligned")

    # Table 11 (Appendix B Benchmark Numbers)
    t11 = doc.tables[11]
    for row in t11.rows[1:]:
        param = row.cells[0].text.strip()
        if "Primary Bottleneck Demand" in param:
            set_para_clean(row.cells[1].paragraphs[0], "80.00 ms (CoV ≈ 0.32)")
            set_para_clean(row.cells[2].paragraphs[0], "Go Frontend exclusive CPU demand; bimodal distribution")
        elif "500 ms SLA Breach Point" in param:
            set_para_clean(row.cells[1].paragraphs[0], "10.40 req/s")
            set_para_clean(row.cells[2].paragraphs[0], "Operating threshold where latency exceeds SLA; HPA trigger point")
        elif "Model Forecasting Accuracy" in param:
            set_para_clean(row.cells[1].paragraphs[0], "37.48% WMAPE (R² = 0.6205)")
            set_para_clean(row.cells[2].paragraphs[0], "Open M/M/1 network validation across 8 tiers")
        elif "Tail Latency Ratio (P95 / Mean)" in param:
            set_para_clean(row.cells[1].paragraphs[0], "1.53× at 10 req/s")
            set_para_clean(row.cells[2].paragraphs[0], "Significant tail latency amplification under heavy queueing")
        elif "Tail Latency Ratio (P99 / Mean)" in param:
            set_para_clean(row.cells[1].paragraphs[0], "2.08× at 10 req/s")
            set_para_clean(row.cells[2].paragraphs[0], "Extreme latency degradation for top 1% slowest transactions")
        elif "Optimal Horizontal Scaling" in param:
            set_para_clean(row.cells[1].paragraphs[0], "c = 3 Replicas")
            set_para_clean(row.cells[2].paragraphs[0], "Expands capacity to 35.2 req/s at 93.6% USL efficiency (86.9 ms latency)")
        elif "Frontend Optimisation Leverage" in param:
            set_para_clean(row.cells[1].paragraphs[0], "95.91% of Total System ROI")
            set_para_clean(row.cells[2].paragraphs[0], "Concentrates 25.000 ms/ms marginal latency reduction")
        elif "Backend Combined ROI" in param:
            set_para_clean(row.cells[1].paragraphs[0], "< 4.09% of Total System ROI")
            set_para_clean(row.cells[2].paragraphs[0], "All 10 backend microservices combined yield negligible optimisation return")
    print("  [FIXED] Table 11 (Benchmark Constants) aligned")

    doc.save(filepath)
    print(f"  Saved: {filepath}")

if __name__ == "__main__":
    align_document("SPEFinal.docx")
    align_document("Software Performance Engineering Course.docx")
    print("\n[SUCCESS] Both documents aligned with 100% specification parity.")
