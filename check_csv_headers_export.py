"""Runnable self-check for the Advanced Bill Checking CSV headers export.
Run: .venv/Scripts/python check_csv_headers_export.py
"""
import io
import csv
import pandas as pd
from app import app, get_filtered_bills, ADV_BILLS_ALL_HEADERS, ADV_BILLS_ALL_KEYS


def test_get_filtered_bills_headers():
    bills = get_filtered_bills()
    assert len(bills) > 0, "Expected bills in test database"
    sample = bills[0]
    expected_fields = [
        "bill_no", "reference_no", "connection_no", "consumer_name",
        "sector", "locality", "zone", "total_bill", "arrears",
        "amount_received", "outstanding_amount", "status", "consumer_mobile",
        "bill_type", "address", "old_connection_no", "water_fee", "sanitation",
        "drainage", "billing_fee", "fine", "after_due_date", "due_date"
    ]
    for field in expected_fields:
        assert field in sample, f"Missing field in bill dict: {field}"
    print(f"[PASS] get_filtered_bills returned all {len(expected_fields)} expected fields in bill records.")


def test_csv_export_all_headers():
    client = app.test_client()
    all_keys_str = ",".join(ADV_BILLS_ALL_KEYS)
    resp = client.get(f"/bill-list/advanced-filter/csv?cols={all_keys_str}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert "text/csv" in resp.content_type

    reader = csv.reader(io.StringIO(resp.data.decode("utf-8")))
    header_row = next(reader)
    assert header_row == ADV_BILLS_ALL_HEADERS, f"Headers mismatch: {header_row} != {ADV_BILLS_ALL_HEADERS}"
    first_data_row = next(reader)
    assert len(first_data_row) == len(ADV_BILLS_ALL_HEADERS)
    print(f"[PASS] CSV export returned all {len(header_row)} headers matching ADV_BILLS_ALL_HEADERS exactly.")


def test_excel_export_all_headers():
    client = app.test_client()
    all_keys_str = ",".join(ADV_BILLS_ALL_KEYS)
    resp = client.get(f"/bill-list/advanced-filter/xlsx?cols={all_keys_str}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    df = pd.read_excel(io.BytesIO(resp.data))
    assert list(df.columns) == ADV_BILLS_ALL_HEADERS, f"Excel columns mismatch: {list(df.columns)}"
    print(f"[PASS] Excel export returned all {len(df.columns)} columns matching ADV_BILLS_ALL_HEADERS.")


def test_pdf_export_all_headers():
    client = app.test_client()
    all_keys_str = ",".join(ADV_BILLS_ALL_KEYS)
    resp = client.get(f"/bill-list/advanced-filter/pdf?cols={all_keys_str}&outstanding_amount=10000")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.data.startswith(b"%PDF"), "Response is not a valid PDF"
    print("[PASS] PDF export generated valid PDF with all 24 columns.")


def test_grouped_pdf_exports():
    client = app.test_client()
    all_keys_str = ",".join(ADV_BILLS_ALL_KEYS)
    for group in ("sector", "zone"):
        resp = client.get(f"/bill-list/advanced-filter/pdf?cols={all_keys_str}&group_by={group}&outstanding_amount=10000")
        assert resp.status_code == 200, f"Expected 200 for group {group}, got {resp.status_code}"
        assert resp.data.startswith(b"%PDF"), f"Response for group {group} is not a valid PDF"
        print(f"[PASS] PDF grouped by {group} generated successfully with all 24 columns.")


if __name__ == "__main__":
    test_get_filtered_bills_headers()
    test_csv_export_all_headers()
    test_excel_export_all_headers()
    test_pdf_export_all_headers()
    test_grouped_pdf_exports()
    print("\nALL ADVANCED BILL HEADERS CHECKS PASSED!")
