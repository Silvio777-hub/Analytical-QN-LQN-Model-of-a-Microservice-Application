import argparse
import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

# Data for Tables 5, 6, 7
TABLE_5_DATA = [
    ["Frontend (Gateway)", "1.0000", "80.00", "80.00", "80.00 %", "4.000", "1 (BOTTLENECK)"],
    ["ProductCatalogService", "0.3692", "5.00", "1.85", "1.85 %", "0.019", "2"],
    ["RecommendationService", "0.0800", "7.50", "0.60", "0.60 %", "0.006", "3"],
    ["CheckoutService", "0.0400", "14.50", "0.58", "0.58 %", "0.006", "4"],
    ["CurrencyService", "0.1852", "3.00", "0.56", "0.56 %", "0.006", "5"],
    ["CartService", "0.1352", "4.00", "0.54", "0.54 %", "0.005", "6"],
    ["AdService", "0.0500", "5.80", "0.29", "0.29 %", "0.003", "7"],
    ["Redis State Store", "0.1284", "2.00", "0.26", "0.26 %", "0.003", "8"],
    ["ShippingService", "0.0452", "3.80", "0.17", "0.17 %", "0.002", "9"],
    ["PaymentService", "0.0072", "9.50", "0.07", "0.07 %", "0.001", "10"],
    ["EmailService", "0.0052", "11.50", "0.06", "0.06 %", "0.001", "11"],
]

TABLE_6_DATA = [
    ["Frontend (Gateway)", "80.00", "75.00", "145.00", "180.00", "Jaeger + Prometheus"],
    ["ProductCatalogService", "5.00", "4.50", "9.50", "13.00", "Jaeger"],
    ["CurrencyService", "3.00", "2.80", "5.80", "8.00", "Jaeger"],
    ["CartService", "4.00", "3.50", "7.80", "11.00", "Jaeger"],
    ["RecommendationService", "7.50", "6.80", "14.00", "20.00", "Jaeger"],
    ["AdService", "5.80", "5.20", "11.00", "16.00", "Jaeger"],
    ["CheckoutService", "14.50", "13.00", "28.00", "40.00", "Jaeger"],
    ["ShippingService", "3.80", "3.40", "7.40", "10.50", "Jaeger"],
    ["PaymentService", "9.50", "8.60", "18.20", "26.00", "Jaeger"],
    ["EmailService", "11.50", "10.40", "22.00", "31.50", "Jaeger"],
    ["Redis State Store", "2.00", "1.80", "3.80", "5.50", "Jaeger"],
]

TABLE_7_DATA = [
    ["5.0 req/s", "285.0 ms", "—", "122.6 ms", "−57.0 %", "40.00 %"],
]


def add_table(doc, title, headers, rows):
    # Add a heading for the table
    doc.add_paragraph(title, style="Heading 3")
    # Create table with header row
    table = doc.add_table(rows=1, cols=len(headers))
    # No explicit style, using default table style
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
    for row in rows:
        row_cells = table.add_row().cells
        for i, cell in enumerate(row):
            row_cells[i].text = str(cell)
    doc.add_paragraph()  # spacer


def insert_missing_tables(doc_path: Path):
    doc = Document(str(doc_path))
    # Find placeholder for missing tables or use end of document
    placeholder_idx = None
    for i, para in enumerate(doc.paragraphs):
        if "{{MISSING_TABLES}}" in para.text:
            placeholder_idx = i
            para.text = para.text.replace("{{MISSING_TABLES}}", "")
            break
    # Insert tables after placeholder or at end
    def insert_at(idx, func, *args):
        if idx is not None:
            # Insert a new empty paragraph before the placeholder to act as anchor
            anchor = doc.paragraphs[idx]
            # python-docx does not support direct insertion at index, so we append then move later
            func(*args)
        else:
            func(*args)
    # Table 5
    add_table(doc,
        "Table 5: Visit Ratio, Exclusive Service Time, Total Demand, and CPU Load at 10 req/s",
        ["Microservice", "Vᵢ", "Sᵢ (ms)", "Dᵢ (ms)", "CPU Load @ 10 req/s", "Queue Nᵢ", "Rank"],
        TABLE_5_DATA)
    # Table 6
    add_table(doc,
        "Table 6: Empirical Service Times Breakdown (Mean, Median, P95, P99)",
        ["Microservice", "Mean Sᵢ (ms)", "Median (ms)", "P95 (ms)", "P99 (ms)", "Source"],
        TABLE_6_DATA)
    # Table 7
    add_table(doc,
        "Table 7: Model Predictions vs. Observed Empirical Response Times Across 8 Tiers",
        ["Load λ₀", "Empirical R_emp", "Pure M/M/1 Upper Bound", "Calibrated LQN Model", "Error %", "Frontend ρ₀"],
        TABLE_7_DATA)
    # Add note paragraphs where appropriate
    doc.add_paragraph("Note: Only the 5 req/s tier has complete empirical measurements; other tiers are analytical predictions only.")
    doc.save(str(doc_path))
    print(f"Inserted tables 5-7 into {doc_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Insert missing tables 5, 6, and 7 into DOCX reports.")
    parser.add_argument("docs", nargs="+", help="Paths to DOCX files to modify.")
    args = parser.parse_args()
    for doc_path in args.docs:
        insert_missing_tables(Path(doc_path))

if __name__ == "__main__":
    main()
