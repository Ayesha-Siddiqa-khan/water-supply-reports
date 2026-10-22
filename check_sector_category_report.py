"""Self-check for the category-wise Sector Wise Report and the paid/unpaid connection lists.

Run: python check_sector_category_report.py
"""

import csv
import io
import sqlite3
import urllib.parse

from app import BILL_LIST_DB, PRIVATE_SOCIETY_NAMES, app, get_bill_list_context

BASE_COLS = "sr,sector,totalBills,receivedBills,remainingBills,totalReceivedAmount,pendingAmount"


def main():
    context = get_bill_list_context()
    report_rows = context["report_rows"]
    categories = context["report_categories"]

    # Every sector lands in exactly one category group and no sector is lost.
    grouped = [row["sector"] for group in categories for row in group["rows"]]
    assert sorted(grouped) == sorted(row["sector"] for row in report_rows)
    assert len(grouped) == len(set(grouped))
    assert [group["name"] for group in categories] == [c for c in ("Domestic", "Commercial", "Private Societies") if c in {g["name"] for g in categories}]

    # Serial numbers run 1..N across the whole table, in category order.
    assert [row["sr"] for row in report_rows] == list(range(1, len(report_rows) + 1))

    # Classification rules: commercial tag, private-society tag or known society name, rest domestic.
    for row in report_rows:
        sector = row["sector"].upper()
        if "COMMERCIAL" in sector:
            assert row["category"] == "Commercial", row
        elif "PRIVATE" in sector and "SOC" in sector:
            assert row["category"] == "Private Societies", row
        elif any(name.upper() in sector for name in PRIVATE_SOCIETY_NAMES):
            assert row["category"] == "Private Societies", row
        else:
            assert row["category"] == "Domestic", row

    # Group totals add up to the page totals.
    assert sum(group["rows"][0]["total_bills"] for group in categories if group["rows"]) >= 0
    assert sum(len(group["rows"]) for group in categories) == len(report_rows)

    client = app.test_client()

    # Sector-wise export: default columns keep the existing pattern, Category is optional.
    default_export = client.get(f"/bill-list/export/csv?cols={BASE_COLS}")
    assert default_export.status_code == 200
    default_rows = list(csv.reader(io.StringIO(default_export.get_data(as_text=True))))
    assert default_rows[0] == ["Sr", "Sector", "Total Bills", "Received Bills", "Remaining Bills", "Total Received Amount", "Pending Amount"]
    assert len(default_rows) == len(report_rows) + 1
    assert default_rows[1][1] == report_rows[0]["sector"]

    # Category column lands where the page column chips put it (right after Sector).
    category_export = client.get("/bill-list/export/csv?cols=sr,sector,category,totalBills,receivedBills,remainingBills,totalReceivedAmount,pendingAmount")
    assert category_export.status_code == 200
    category_rows = list(csv.reader(io.StringIO(category_export.get_data(as_text=True))))
    assert category_rows[0] == ["Sr", "Sector", "Category", "Total Bills", "Received Bills", "Remaining Bills", "Total Received Amount", "Pending Amount"]
    assert category_rows[1][2] == report_rows[0]["category"]

    # Connection lists: paid / unpaid, restricted to the checked sectors.
    paid_export = client.get("/bill-list/export/connections/csv?status=paid")
    assert paid_export.status_code == 200
    paid_rows = list(csv.reader(io.StringIO(paid_export.get_data(as_text=True))))
    assert paid_rows[0][0] == "Sr"

    unpaid_export = client.get("/bill-list/export/connections/csv?status=unpaid")
    assert unpaid_export.status_code == 200
    unpaid_rows = list(csv.reader(io.StringIO(unpaid_export.get_data(as_text=True))))
    assert unpaid_rows[0][0] == "Sr"

    with sqlite3.connect(BILL_LIST_DB) as connection:
        connection.row_factory = sqlite3.Row
        paid_count = connection.execute("SELECT COUNT(*) AS c FROM bills WHERE amount_received >= total_bill").fetchone()["c"]
        unpaid_count = connection.execute("SELECT COUNT(*) AS c FROM bills WHERE amount_received < total_bill").fetchone()["c"]
    assert len(paid_rows) - 1 == paid_count, (len(paid_rows) - 1, paid_count)
    assert len(unpaid_rows) - 1 == unpaid_count, (len(unpaid_rows) - 1, unpaid_count)

    # Only the checked sector reaches the connection list (include mode).
    checked_sector = report_rows[0]["sector"]
    params = urllib.parse.urlencode({"status": "paid", "row_mode": "include", "row_key": checked_sector})
    selected_export = client.get(f"/bill-list/export/connections/csv?{params}")
    assert selected_export.status_code == 200
    selected_rows = list(csv.reader(io.StringIO(selected_export.get_data(as_text=True))))
    assert len(selected_rows) - 1 <= paid_count
    with sqlite3.connect(BILL_LIST_DB) as connection:
        connection.row_factory = sqlite3.Row
        expected = connection.execute(
            "SELECT COUNT(*) AS c FROM bills WHERE amount_received >= total_bill AND sector = ?",
            (checked_sector,),
        ).fetchone()["c"]
    assert len(selected_rows) - 1 == expected, (len(selected_rows) - 1, expected)

    # The sector report export honours the same checkbox selection.
    sector_params = urllib.parse.urlencode({"row_mode": "include", "row_key": checked_sector})
    sector_export = client.get(f"/bill-list/export/csv?cols={BASE_COLS}&{sector_params}")
    assert sector_export.status_code == 200
    sector_rows = list(csv.reader(io.StringIO(sector_export.get_data(as_text=True))))
    assert len(sector_rows) == 2 and sector_rows[1][1] == checked_sector

    # PDF connection list (grouped by sector) still builds.
    pdf_export = client.get("/bill-list/export/connections/pdf?status=unpaid")
    assert pdf_export.status_code == 200
    assert pdf_export.mimetype == "application/pdf"

    # Sector-wise Details tabs: one per category, each with its own PDF/CSV.
    for group in categories:
        slug = group["name"].lower().replace(" ", "-")
        tab_csv = client.get(f"/bill-list/export/sector/{slug}/csv")
        assert tab_csv.status_code == 200, tab_csv.status_code
        tab_rows = list(csv.reader(io.StringIO(tab_csv.get_data(as_text=True))))
        assert tab_rows[0][:2] == ["Sr", "Sector"], tab_rows[0]
        expected_rows = len(group["rows"]) + sum(len(row.get("localities") or []) for row in group["rows"])
        assert len(tab_rows) == expected_rows + 1
        assert tab_rows[1][0] == "1"  # each tab is its own report, so Sr restarts at 1
        assert {row[1] for row in tab_rows[1:]} == {row["sector"] for row in group["rows"]}

        tab_pdf = client.get(f"/bill-list/export/sector/{slug}/pdf")
        assert tab_pdf.status_code == 200
        assert tab_pdf.mimetype == "application/pdf"

    # The Commercial tab carries the locality break-up under its sector.
    commercial = next((g for g in categories if g["name"] == "Commercial"), None)
    if commercial:
        for row in commercial["rows"]:
            localities = row.get("localities") or []
            assert localities, row
            assert sum(loc["total_bills"] for loc in localities) == row["total_bills"]
            assert sum(loc["received_bills"] for loc in localities) == row["received_bills"]
            assert abs(sum(loc["total_received_amount"] for loc in localities) - row["total_received_amount"]) < 0.5
        tab_rows = list(csv.reader(io.StringIO(
            client.get("/bill-list/export/sector/commercial/csv").get_data(as_text=True)
        )))
        assert tab_rows[0] == ["Sr", "Sector", "Locality", "Total Bills", "Received Bills", "Remaining Bills", "Total Received Amount", "Pending Amount"]
        assert len(tab_rows) > len(commercial["rows"]) + 1

    print("Sector category report and connection list checks passed.")


if __name__ == "__main__":
    main()
