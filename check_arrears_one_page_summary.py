"""Regression check for both one-page consumer arrears summary options.

Run: .venv/Scripts/python.exe check_arrears_one_page_summary.py
"""

import csv
import io
import os

import pandas as pd
from flask import Flask
from pypdf import PdfReader

import arrears_analysis as arrears_module
from arrears_analysis import (
    build_arrears_pdf,
    compute_arrears_analysis,
    compute_category_arrears_summary,
    get_one_page_summary_rows,
    select_one_page_summary,
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
        {"Sector": "01", "Locality": "Empty Plot", "Status": "Open", "Rate Type": "4800", "Total Arrears": "0"},
        {"Sector": "01", "Locality": "Empty Plot", "Status": "Suspended", "Rate Type": "4800", "Total Arrears": ""},
        {"Sector": "01", "Locality": "Empty Plot", "Status": "Closed", "Rate Type": "4800", "Total Arrears": "-10"},
    ])
    analysis = compute_arrears_analysis(df)
    category_summary = compute_category_arrears_summary(df)
    assert [row["label"] for row in get_one_page_summary_rows(category_summary, "category")] == [
        "Domestic", "Private Societies", "Commercial", "Suspended", "Closed"
    ]
    assert [row["label"] for row in get_one_page_summary_rows(category_summary, "status")] == [
        "Regular", "Suspended", "Closed"
    ]
    assert category_summary["grand_total"]["total_arrears"] == 685
    assert category_summary["grand_total"]["total_count"] == 6
    rows, total = select_one_page_summary(category_summary, "category", ["domestic", "suspended"])
    assert [row["label"] for row in rows] == ["Domestic", "Suspended"]
    assert total["total_count"] == 3 and total["total_arrears"] == 180

    os.makedirs("output", exist_ok=True)
    for summary_group, expected_labels in (
        ("category", ["Domestic", "Private Societies", "Commercial", "Suspended", "Closed"]),
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

    selected_pdf = build_arrears_pdf(
        df, analysis, report_mode="one_page", summary_group="category",
        one_page_rows=["domestic", "suspended"], one_page_cols=["arrears"],
    )
    selected_text = PdfReader(io.BytesIO(selected_pdf)).pages[0].extract_text()
    assert "Domestic" in selected_text and "Suspended" in selected_text
    assert "Private Societies" not in selected_text and "Connections" not in selected_text
    no_metric_pdf = build_arrears_pdf(
        df, analysis, report_mode="one_page", one_page_rows=[], one_page_cols=[],
    )
    assert "GRAND TOTAL" in PdfReader(io.BytesIO(no_metric_pdf)).pages[0].extract_text()

    app = Flask(__name__, template_folder="templates")
    app.register_blueprint(arrears_module.arrears_analysis_bp)
    original_loader = arrears_module.load_working_dataset
    arrears_module.load_working_dataset = lambda: (df, {})
    try:
        with app.test_client() as client:
            query = "?mode=one_page&summary_group=category&summary_rows=domestic,suspended&summary_cols=arrears"
            csv_response = client.get("/arrears-analysis/export/csv" + query)
            csv_rows = list(csv.reader(io.StringIO(csv_response.get_data(as_text=True))))
            assert csv_response.status_code == 200
            assert csv_rows[2] == ["Sr #", "Consumer Category", "Arrears (PKR)"]
            assert csv_rows[-1] == ["", "GRAND TOTAL", "180.0"]
            xlsx_response = client.get("/arrears-analysis/export/xlsx" + query)
            sheet = pd.read_excel(io.BytesIO(xlsx_response.data))
            assert xlsx_response.status_code == 200
            assert list(sheet.columns) == ["Sr #", "Consumer Category", "Arrears (PKR)"]
            assert sheet.iloc[-1]["Arrears (PKR)"] == 180
            print_response = client.get("/arrears-analysis/print" + query)
            print_html = print_response.get_data(as_text=True)
            assert print_response.status_code == 200
            assert "Domestic" in print_html and "Suspended" in print_html
            assert "Private Societies" not in print_html and "<th class=\"center\">Connections</th>" not in print_html

        import app as app_module
        with app_module.app.test_client() as client:
            page = client.get("/arrears-analysis" + query)
            html = page.get_data(as_text=True)
            assert page.status_code == 200
            assert 'value="domestic" checked' in html
            assert 'value="commercial"' in html
            assert 'id="summary-cols-input" value="arrears"' in html
    finally:
        arrears_module.load_working_dataset = original_loader

    print("One-page arrears summary checks passed.")


if __name__ == "__main__":
    main()
