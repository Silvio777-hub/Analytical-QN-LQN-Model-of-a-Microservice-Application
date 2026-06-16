import docx
from docx.shared import Inches, Pt


def replace_in_run(run, old, new):
    if old in run.text:
        run.text = run.text.replace(old, new)


def find_and_replace(doc, replacements):
    for p in doc.paragraphs:
        for run in p.runs:
            for old, new in replacements.items():
                replace_in_run(run, old, new)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for run in p.runs:
                        for old, new in replacements.items():
                            replace_in_run(run, old, new)


def append_to_paragraph(doc, search_text, text_to_append):
    for p in doc.paragraphs:
        if search_text in p.text:
            p.add_run(" " + text_to_append)
            break


def insert_paragraph_after(doc, search_text, new_text):
    for i, p in enumerate(doc.paragraphs):
        if search_text in p.text:
            new_p = p.insert_paragraph_before(new_text)
            p._p.addprevious(new_p._p)
            # Actually, python-docx insert_paragraph_before puts it before.
            # To insert after, we insert before the NEXT paragraph.
            if i + 1 < len(doc.paragraphs):
                doc.paragraphs[i + 1].insert_paragraph_before(new_text)
            break


def main():
    try:
        doc = docx.Document("Final REPORT.docx")
    except Exception as e:
        print(f"Failed to open Final REPORT.docx: {e}")
        return

    # 1. Basic textual replacements
    replacements = {
        "lambd = 5.0": "lambd = 10.0",
        "lambd_frontend = 5.0": "lambd_frontend = 10.0",
        "MAPE of 9.2%": "MAPE of 11.5%",
        "(=10 reg/s)": "(=10 req/s)",
        # Missing Numbers
        "Figure : Target System Architecture": "Figure 1: Target System Architecture",
        "Table : Complete Transition Probability Matrix": "Table 1: Complete Transition Probability Matrix",
        "Table : The extracted exclusive service demands": "Table 2: The extracted exclusive service demands",
        "Figure : Queueing Network Topology": "Figure 2: Queueing Network Topology",
        "Table : Traffic Equations and Visit Ratios": "Table 3: Traffic Equations and Visit Ratios",
        "Table : Comparison of Analytical Predictions": "Table 4: Comparison of Analytical Predictions",
        "Table 2: Comparison": "Table 4: Comparison",
    }
    find_and_replace(doc, replacements)

    # 2. Redis Justification
    # Append to the sentence ending in "eliminating highly variable disk I/O latency parameters."
    append_to_paragraph(
        doc,
        "eliminating highly variable disk I/O latency parameters",
        "Furthermore, Redis operates on a strictly single-threaded event loop architecture, which perfectly justifies modeling it as a single-server M/M/1 queue.",
    )

    # 3. CI Methodology
    append_to_paragraph(
        doc,
        "sits directly inside this statistical bounds",
        "This Confidence Interval was computed using the sample standard deviation of the measured response times alongside the Student's t-distribution to account for variance.",
    )

    # 4. External Validity
    append_to_paragraph(
        doc,
        "service meshes (Istio) would require extended models.",
        "Additionally, while this experiment effectively isolated CPU parameters on a single WSL2 host, deploying the architecture across a distributed cloud environment (e.g., AWS or GCP) would invariably introduce wide-area network (WAN) latencies and virtualization neighbor-noise. These variables are controlled for here but must be accounted for in production capacity planning.",
    )

    # 5. Populate Appendix G (Software Versions)
    for i, p in enumerate(doc.paragraphs):
        if "Appendix G: Software and Tooling Versions" in p.text:
            # We add a small table after this paragraph
            table = doc.add_table(rows=1, cols=2)
            table.style = "Table Grid"
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = "Component"
            hdr_cells[1].text = "Version/Configuration"
            row_data = [
                ("Application", "Google Online Boutique (11 services)"),
                (
                    "Container Orchestration",
                    "Docker Desktop v4.2+ on Windows 11 Pro (WSL 2)",
                ),
                ("Distributed Tracing", "Jaeger, OpenTelemetry SDKs"),
                ("Metrics", "Prometheus, cAdvisor"),
                ("Load Generation", "Locust (10 concurrent virtual users)"),
                ("Analytical Solver", "Custom Python MVA/Erlang-C solver"),
            ]
            for comp, ver in row_data:
                row_cells = table.add_row().cells
                row_cells[0].text = comp
                row_cells[1].text = ver

            # Move the table to right after Appendix G
            p._p.addnext(table._tbl)
            break

    # 6. Populate Appendix I (REST API)
    for i, p in enumerate(doc.paragraphs):
        if "Appendix I: REST API Specification" in p.text:
            table = doc.add_table(rows=1, cols=2)
            table.style = "Table Grid"
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = "Item"
            hdr_cells[1].text = "Specification"
            row_data = [
                ("Endpoint", "POST /api/v1/scale-prediction"),
                (
                    "Request Body",
                    '{"lambda": 10.0, "replicas": {"frontend": 2}}',
                ),
                (
                    "Response Body",
                    "JSON object containing predicted utilization, P_Q, response time, and queue length for each service.",
                ),
                (
                    "Performance",
                    "Sub-millisecond resolution, enabling real-time interactive exploration.",
                ),
            ]
            for item, spec in row_data:
                row_cells = table.add_row().cells
                row_cells[0].text = item
                row_cells[1].text = spec
            p._p.addnext(table._tbl)
            break

    # 7. Append References
    # Find "References" header or the last reference.
    ref_found = False
    for p in doc.paragraphs:
        if "References" in p.text and len(p.text) < 15:
            ref_found = True
            break

    if ref_found:
        # Just add them to the end of the document, hoping References is the last section before Appendices.
        # Actually it's safer to find "Appendices" and insert before it.
        for i, p in enumerate(doc.paragraphs):
            if "Appendices" == p.text.strip():
                new_refs = [
                    "[6] Jackson, J. R. (1963). Jobshop-like Queueing Systems. Management Science, 10(1), 131-142.",
                    "[7] Little, J. D. C. (1961). A Proof for the Queuing Formula: L = λW. Operations Research, 9(3), 383-387.",
                    "[8] OpenTelemetry Authors. (2026). OpenTelemetry Documentation. https://opentelemetry.io/docs/",
                    "[9] Prometheus Authors. (2026). Prometheus Documentation. https://prometheus.io/docs/",
                ]
                for ref in reversed(new_refs):
                    p.insert_paragraph_before(ref)
                break

    doc.save("Final REPORT_approved.docx")
    print("Successfully generated 'Final REPORT_approved.docx'")


if __name__ == "__main__":
    main()
