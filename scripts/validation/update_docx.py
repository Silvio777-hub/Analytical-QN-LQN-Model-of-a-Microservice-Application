import docx


def replace_in_run(run, old, new):
    if old in run.text:
        run.text = run.text.replace(old, new)


def replace_in_doc(doc, replacements):
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


def main():
    doc = docx.Document("REPORT.docx")

    replacements = {
        "λ=5.0": "λ=10.0",
        'λ=5.0" req/s"': 'λ=10.0" req/s"',
        "λ=5.0 req/s": "λ=10.0 req/s",
        '276.19" ms"': '400.00" ms"',
        "276.19 ms": "400.00 ms",
        '[269.9" ms" , 300.1" ms" ]': '[390.5" ms" , 439.5" ms" ]',
        "[269.9 ms, 300.1 ms]": "[390.5 ms, 439.5 ms]",
        "RMSE of 4.98": "RMSE of 6.00",
        "MAPE of 9.2%": "MAPE of 11.5%",
        # S_i updates (Frontend)
        '116.67" ms"': '80.00" ms"',
        "116.67 ms": "80.00 ms",
        "116.67": "80.00",
        '172" ms"': '140" ms"',
        '48" ms"': '48" ms"',  # unchanged maybe
        # V_i table
        "1.85\t0.370": "3.70\t0.370",
        "0.92\t0.184": "1.84\t0.184",
        "0.75\t0.150": "1.50\t0.150",
        "0.40\t0.080": "0.80\t0.080",
        "0.25\t0.050": "0.50\t0.050",
        "0.20\t0.040": "0.40\t0.040",
        "0.24\t0.048": "0.48\t0.048",
        "0.06\t0.012": "0.12\t0.012",
        "0.04\t0.008": "0.08\t0.008",
        # Scaling
        '(ρ=1.044) at an arrival rate of 9.0" req/s"': '(ρ=1.0) at an arrival rate of 12.5" req/s"',
        "0.522": "0.400",
        "falls to 23%": "falls to 22.8%",
        '143.9" ms"': '95.2" ms"',
        # Table 2
        "276.19\t285.00\t-8.81\t3.1%": "400.00\t415.00\t-15.00\t3.6%",
        "5.05\t8.20\t-3.15\t38.5%": "5.09\t8.20\t-3.11\t37.9%",
        "3.01\t5.10\t-2.09\t41.0%": "3.02\t5.10\t-2.08\t40.8%",
        "4.01\t6.80\t-2.79\t41.0%": "4.02\t6.80\t-2.78\t40.9%",
        "7.52\t12.40\t-4.88\t39.4%": "8.05\t12.40\t-4.35\t35.1%",
        "5.89\t9.10\t-3.21\t35.3%": "6.02\t9.10\t-3.08\t33.8%",
        "14.71\t22.50\t-7.79\t34.6%": "15.09\t22.50\t-7.41\t32.9%",
        "3.83\t7.20\t-3.37\t46.8%": "4.01\t7.20\t-3.19\t44.3%",
        "9.56\t14.30\t-4.74\t33.1%": "10.01\t14.30\t-4.29\t30.0%",
        "11.55\t18.00\t-6.45\t35.8%": "12.01\t18.00\t-5.99\t33.3%",
        "2.00\t3.50\t-1.50\t42.9%": "2.01\t3.50\t-1.49\t42.6%",
        "33.34%": "34.1%",
        "281.27": "405.10",
        "292.15": "423.52",
        "~3.7%": "~4.3%",
        "0.041": "0.048",
        "4.986": "6.000",
        "4.525": "5.143",
        # 7.2
        "n=4,004 traces": "n=8,102 traces",
        'mean of 285" ms"': 'mean of 415" ms"',
        'R=0.285" s"': 'R=0.415" s"',
        "N=1.425": "N=4.150",
        "concurrency of 1.41": "concurrency of 4.11",
        # 7.3
        '1 to 10" req/s"': '1 to 12.5" req/s"',
        '8.57" req/s"': '12.5" req/s"',
        'plateaued at 8.9" req/s"': 'plateaued at 11.8" req/s"',
        # Appendices
        "0.11667": "0.08000",
        "0.5833": "0.8000",
        "0.6739": "4.0000",
        "0.00925": "0.01850",
        "0.00935": "0.01880",
        "0.00276": "0.00552",
        "0.00300": "0.00600",
        "0.00301": "0.00603",
        "0.00145": "0.00290",
        "0.00147": "0.00291",
        "0.00290": "0.00580",
        "0.00298": "0.00598",
        "0.00091": "0.00182",
        "0.00057": "0.00114",
        "0.00046": "0.00092",
        "0.00150": "0.00300",
    }

    replace_in_doc(doc, replacements)
    doc.save("REPORT_updated_lambda_10.docx")


if __name__ == "__main__":
    main()
