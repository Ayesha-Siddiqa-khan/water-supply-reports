"""Run: python check_new_connection_detail.py [optional-payment-list.csv]"""

import csv
import io
import json
import os
import re
import sys
import tempfile
from unittest.mock import patch

from openpyxl import load_workbook
from werkzeug.datastructures import FileStorage

import app as module


def upload(headers, rows, name):
    data = io.StringIO()
    writer = csv.writer(data)
    writer.writerow(headers)
    writer.writerows(rows)
    return FileStorage(stream=io.BytesIO(data.getvalue().encode()), filename=name)


def main():
    headers = ["Received Date", "Connection No", "Connection Type", "Sector", "Bill Type", "Connection Fee", "Amount Received", "Bill Amount"]
    rows = [
        ["04/07/2025", "001", "Water Domestic 1/2", "Town", "New Connection", "6000", "7,510", "1200"],
        ["29/06/2026", "002", "Water Domestic 1/2", "Al-Khair Colony (PRIVATE SOCIETY)", "New Connection", "10800", "11500", "400"],
        ["01/07/2026", "003", "Water Commercial 1/4", "COMMERCIAL", "New Connection", "14700", "14000", "500"],
        ["bad date", "004", "Water Domestic 1/2", "Town", "Regular", "-", "1000", "400"],
        ["01/07/2026", "005", "Water Domestic 1/2", "Town", "ReConnection", "6000", "6000", "400"],
        ["bad date", "006", "Water Domestic 1/2", "Town", "New Connection", "6000", "7000", "400"],
        ["01/07/2026", "007", "Unknown", "Town", "New Connection", "6000", "7000", "400"],
        ["01/07/2026", "", "Water Domestic 1/2", "Town", "New Connection", "6000", "7000", "400"],
    ]
    headers.append("Consumer Name")
    rows = [row + [f"Consumer {number}"] for number, row in enumerate(rows, 1)]
    report = module._build_new_connection_detail_report([upload(headers, rows, "22-10-26_Consumer-List.csv")])
    assert report["summary"] == {
        "uploaded_records": 8, "total_new_connections": 3, "total_amount": 33010,
        "domestic": 1, "private": 1, "commercial": 1, "unclassified": 0,
    }
    assert report["skipped_records"] == 2
    assert [r["source_row"] for r in report["rows"]] == [2, 3, 4]
    assert [r["issue"] for r in report["review_rows"]] == [
        "Invalid Received Date", "Missing or unsupported Connection Type", "Missing Connection No",
    ]
    assert report["annual_summary"] == [
        {"financial_year": "2025-2026", "connections": 2, "amount": 19010},
        {"financial_year": "2026-2027", "connections": 1, "amount": 14000},
    ]
    assert all(r["security"] is None and r["connections"] == 1 for r in report["rows"])
    assert report["rows"][0]["original"]["Connection No"] == "001"
    duplicates = module._build_new_connection_detail_report([
        upload(headers, rows[:3], "a.csv"), upload(headers, rows[:3], "b.csv"),
    ])
    assert duplicates["summary"]["total_new_connections"] == 3

    legacy = module._build_new_connection_detail_report([upload(
        ["Received Date", "No of Connection", "Total Receivable", "Security"],
        [["01/07/2025", "101", "5000", "4800"], ["01/07/2025", "102", "10000", "9600"],
         ["01/07/2025", "103", "7000", "6000"], ["01/07/2025", "104", "7000", ""]],
        "24-25.csv",
    )])
    assert [r["classification"] for r in legacy["rows"]] == ["Domestic", "Domestic - Private Society", "Commercial"]
    assert legacy["financial_years"] == ["2024-2025"]
    assert legacy["summary"]["total_amount"] == 22000
    assert legacy["review_rows"][0]["issue"] == "Missing or unsupported Security value"
    assert module._ncd_year_from_source("19-09-26_Consumer-List.csv") is None
    assert module._ncd_year_from_source("22-10-26_Consumer-List.csv") is None

    with tempfile.TemporaryDirectory() as folder, patch.object(module, "NEW_CONNECTION_DETAIL_CACHE", os.path.join(folder, "cache.json")), patch.object(module, "_new_connection_detail_report", None):
        client = module.app.test_client()
        fixture = upload(headers, rows, "22-10-26_Consumer-List.csv")
        response = client.post("/new-connection-detail", data={"new_connection_files": (fixture.stream, fixture.filename)}, follow_redirects=True)
        assert response.status_code == 200
        assert b"33,010" in response.data and b"Needs Review (3)" in response.data
        assert b"2 other payment records excluded" in response.data
        boxes = re.findall(r'<input[^>]*class="ncd-detail-col"[^>]*>', response.get_data(as_text=True))
        assert [re.search(r'value="([^"]+)"', box).group(1) for box in boxes if "checked" in box] == [
            "Sr No.", "Financial Year", "Connection No", "Amount Received",
        ]
        assert any('value="Consumer Name"' in box and "checked" not in box for box in boxes)
        assert any('value="Received Date"' in box and "checked" not in box for box in boxes)
        assert any('value="Sector"' in box and "checked" not in box for box in boxes)
        assert not any("Mobile" in box for box in boxes)
        # Exercise persisted data too, including classification without security.
        module._new_connection_detail_report = None
        assert module._load_new_connection_detail_cache()["summary"] == report["summary"]
        detail = client.get("/new-connection-detail/export/csv")
        exported = list(csv.DictReader(io.StringIO(detail.get_data(as_text=True))))
        assert [r["Connection No"] for r in exported[:3]] == ["001", "002", "003"]
        assert len(exported) == 8  # Three detail rows, footer header, three categories, total.
        assert exported[0]["Connection No"] == "001"
        assert list(exported[0]) == ["Sr No.", "Financial Year", "Connection No", "Amount Received"]
        selected = report["detail_default_columns"] + ["Consumer Name", "Sector", "Received Date"]
        optional = client.post("/new-connection-detail/export/csv", data={"detail_cols": json.dumps(selected)})
        optional_rows = list(csv.DictReader(io.StringIO(optional.get_data(as_text=True))))
        assert optional_rows[0]["Consumer Name"] == "Consumer 1"
        assert optional_rows[0]["Received Date"] == "04/07/2025"
        assert optional_rows[1]["Sector"] == "Al-Khair Colony (PRIVATE SOCIETY)"
        mobile = module._build_new_connection_detail_report([upload(headers + ["Mobile No"], [rows[0] + ["03001234567"]], "mobile.csv")])
        assert mobile["rows"][0]["original"]["Mobile No"] == "03001234567"
        assert "Mobile No" not in mobile["detail_default_columns"]
        annual = client.get("/new-connection-detail/export/annual-csv")
        assert list(csv.reader(io.StringIO(annual.get_data(as_text=True))))[1] == ["1", "2025-2026", "2", "19,010"]
        workbook = load_workbook(io.BytesIO(client.get("/new-connection-detail/export/annual-xlsx").data))
        assert list(workbook.active.values)[1][1:] == ("2025-2026", "2", "19,010")
        pdf = client.get("/new-connection-detail/export/detailed-pdf")
        assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF")

    if len(sys.argv) > 1:
        with open(sys.argv[1], "rb") as source:
            actual = module._build_new_connection_detail_report([FileStorage(stream=source, filename=os.path.basename(source.name))])
        print(json.dumps({"summary": actual["summary"], "annual_summary": actual["annual_summary"], "review_records": len(actual["review_rows"]), "excluded_records": actual["skipped_records"]}, indent=2))
    print("New Connection Detail upload and export checks passed.")


if __name__ == "__main__":
    main()
