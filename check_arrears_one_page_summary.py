"""Regression check for both one-page consumer arrears summary options.

Run: .venv/Scripts/python.exe check_arrears_one_page_summary.py
"""

import os

import pandas as pd
from pypdf import PdfReader

from arrears_analysis import (
    build_arrears_pdf,
    compute_arrears_analysis,
    compute_category_arrears_summary,
    get_one_page_summary_rows,
)


def main():
    df = pd.DataFrame([
        {"Sector": "01", "Locality": "Domestic Area", "Status": "Open", "Rate Type": "4800", "Total Arrears": "100"},
        {"Sector": "01", "Locality": "Domestic Area", "Status": "Suspended", "Rate Type": "4800", "Total Arrears": "20"},
        {"Sector": "01", "Locality": "Domestic Area", "Status": "Closed", "Rate Type": "4800", "Total Arrears": "5"},
        {"Sector": "02", "Locality": "Private Society", "Status": "Open", "Rate Type": "9600", "Total Arrears": "200"},
        {"Sector": "COMMERCIAL", "Locality": "Market", "Status": "Open", "Rate Type": "Commercial", "Total Arrears": "300"},
        {"Sector": "COMMERCIAL", "Locality": "Market", "Status": "Suspended", "Rate Type": "Commercial", "Total Arrears": "60"},
        {"Sector": "COMMERCIAL", "Locality": "Staff Colony", "Status": "Open", "Rate Type": "Commercial", "Total Arrears": "999"},
    ])
    analysis = compute_arrears_analysis(df)
    category_summary = compute_category_arrears_summary(df)
    assert [row["label"] for row in get_one_page_summary_rows(category_summary, "category")] == [
        "Domestic", "Private Societies", "Commercial"
    ]
    assert [row["label"] for row in get_one_page_summary_rows(category_summary, "status")] == [
        "Regular", "Suspended", "Closed"
    ]
    assert category_summary["grand_total"]["total_arrears"] == 685

    os.makedirs("output", exist_ok=True)
    for summary_group, expected_labels in (
        ("category", ["Domestic", "Private Societies", "Commercial"]),
        ("status", ["Regular", "Suspended", "Closed"]),
    ):
        pdf_bytes = build_arrears_pdf(
            df,
            analysis,
            report_mode="one_page",
            category="domestic",
            sum_cols=["reg_count", "reg_arr"],
            summary_group=summary_group,
        )
        output_path = os.path.join("output", f"arrears_summary_{summary_group}_check.pdf")
        with open(output_path, "wb") as pdf_file:
            pdf_file.write(pdf_bytes)
        reader = PdfReader(output_path)
        assert len(reader.pages) == 1
        text = reader.pages[0].extract_text() or ""
        assert "Water Supply Consumer Arrears" in text
        assert "Arrears Summary" not in text
        assert "Connections" in text and "Arrears (PKR)" in text
        for label in expected_labels:
            assert label in text

    print("One-page arrears summary checks passed.")


if __name__ == "__main__":
    main()
