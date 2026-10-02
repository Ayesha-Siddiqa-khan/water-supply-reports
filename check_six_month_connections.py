"""Check both six-month report views against a supplied Bills CSV.

Run: .venv/Scripts/python.exe check_six_month_connections.py path/to/Bills.csv
"""

import csv
from contextlib import contextmanager
import io
import os
import shutil
import sqlite3
import sys
import tempfile

import pandas as pd
from pypdf import PdfReader

import app


def main(path: str) -> None:
    source = pd.read_csv(path, dtype=str, keep_default_na=False)
    expected_bills = len(source)
    connections = source["Connection No"].str.strip()
    expected_connections = connections[connections.ne("")].nunique()

    original_db = app.BILL_LIST_DB
    original_get_db = app.get_db

    @contextmanager
    def isolated_db():
        connection = sqlite3.connect(app.BILL_LIST_DB)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    with tempfile.TemporaryDirectory() as temporary:
        app.BILL_LIST_DB = os.path.join(temporary, "six_month_check.sqlite3")
        app.get_db = isolated_db
        try:
            shutil.copy2(original_db, app.BILL_LIST_DB)
            with app.get_db() as connection:
                connection.execute("DELETE FROM bills")
            app.init_bill_list_db()
            app.import_bill_list_dataframe(source)
            query = "?season=jul-dec&year=2026"
            with app.app.test_client() as client:
                general = client.get("/bill-list/export/six-month-pitch/csv" + query + "&view=general")
                assert general.status_code == 200
                general_rows = list(csv.reader(io.StringIO(general.get_data(as_text=True))))
                assert general_rows[0] == ["Sr", "Connections", "Received Bills", "Remaining Bills", "Amount Received", "Pending Amount"]
                assert len(general_rows) == 2 and general_rows[1][0] == "1"
                assert int(general_rows[1][1].replace(",", "")) == expected_connections

                staff = client.get("/bill-list/export/six-month-pitch/csv" + query)
                assert staff.status_code == 200
                staff_rows = list(csv.reader(io.StringIO(staff.get_data(as_text=True))))
                assert staff_rows[0][2] == "Connections" and "Total Bills" not in staff_rows[0]
                assert staff_rows[-1][1] == "Grand Total"
                assert int(staff_rows[-1][2].replace(",", "")) == expected_connections

                all_cols = "&cols=sr,staffName,connections,totalBills,receivedBills,remainingBills,totalAmount,amountReceived,currentBillAmount"
                selected = client.get("/bill-list/export/six-month-pitch/csv" + query + "&view=general" + all_cols)
                selected_rows = list(csv.reader(io.StringIO(selected.get_data(as_text=True))))
                assert selected_rows[0][2] == "Total Bills" and "Total Amount" in selected_rows[0]
                assert int(selected_rows[1][2].replace(",", "")) == expected_bills

                general_excel = client.get("/bill-list/export/six-month-pitch/xlsx" + query + "&view=general")
                assert general_excel.status_code == 200
                assert len(pd.read_excel(io.BytesIO(general_excel.data))) == 1

                category_query = query + "&view=general&category_detail=1"
                category_csv = client.get("/bill-list/export/six-month-pitch/csv" + category_query)
                assert category_csv.status_code == 200
                category_rows = list(csv.reader(io.StringIO(category_csv.get_data(as_text=True))))
                assert category_rows[3] == ["Category-wise Detail"]
                assert [row[0] for row in category_rows[5:9]] == ["Domestic", "Commercial", "Private Societies", "Grand Total"]
                assert category_rows[-1][1:] == general_rows[1][1:]

                category_excel = client.get("/bill-list/export/six-month-pitch/xlsx" + category_query)
                assert category_excel.status_code == 200
                workbook = pd.ExcelFile(io.BytesIO(category_excel.data))
                assert workbook.sheet_names == ["General", "Category-wise Detail"]
                assert len(pd.read_excel(workbook, sheet_name="Category-wise Detail")) == 4

                output_dir = os.path.join("output", "pdf")
                os.makedirs(output_dir, exist_ok=True)
                for view, suffix in (("", "staffwise"), ("&view=general", "general"),
                                     ("&view=general&category_detail=1", "general_category")):
                    response = client.get("/bill-list/export/six-month-pitch/pdf" + query + view)
                    assert response.status_code == 200
                    pdf_path = os.path.join(output_dir, f"six_month_{suffix}_jul_dec_2026.pdf")
                    with open(pdf_path, "wb") as output:
                        output.write(response.data)
                    text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(response.data)).pages)
                    assert "Six Month July to December 2026 Report" in text
                    assert "Connections" in text and f"{expected_connections:,}" in text
                    assert "Total Bills" not in text and "Total Amount" not in text
                    if "general" in view:
                        assert "Generated:" not in text
                        assert len(PdfReader(io.BytesIO(response.data)).pages) == 1
                    if view == "&view=general":
                        assert "Grand Total" not in text
                    if "category_detail" in view:
                        assert "Category-wise Detail" in text
                        assert "Domestic" in text and "Commercial" in text and "Private Societies" in text

                for view in ("&view=general", "&view=general&category_detail=1"):
                    response = client.get("/bill-list/export/six-month-pitch/pdf" + query + view + all_cols)
                    assert response.status_code == 200
                    pages = PdfReader(io.BytesIO(response.data)).pages
                    assert len(pages) == 1
                    text = "\n".join(page.extract_text() or "" for page in pages)
                    assert "Total Bills" in text and "Total Amount" in text
                    if "category_detail" in view:
                        os.makedirs(os.path.join("tmp", "pdfs", "six_month_columns"), exist_ok=True)
                        with open(os.path.join("tmp", "pdfs", "six_month_columns", "selected_all.pdf"), "wb") as output:
                            output.write(response.data)
                    response = client.get("/bill-list/export/six-month-pitch/pdf" + query + view + "&cols=connections,amountReceived")
                    assert response.status_code == 200
                    text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(response.data)).pages)
                    assert "Connections" in text and "Amount Received" in text
                    assert "Total Bills" not in text and "Total Amount" not in text
                    assert "Received Bills" not in text and "Pending Amount" not in text

                page = client.get("/bill-list")
                html = page.get_data(as_text=True)
                assert page.status_code == 200
                assert 'value="2027"' in html and 'value="2028"' in html
                assert "General PDF" in html and "Staff-wise PDF" in html
                assert 'id="season-category-detail"' in html
                assert html.count('data-col-config="sixMonthPitch"') == 3
        finally:
            app.BILL_LIST_DB = original_db
            app.get_db = original_get_db

    print(f"Six-month reports verified: {expected_connections:,} connections, {expected_bills:,} bills.")


if __name__ == "__main__":
    main(sys.argv[1])
