"""Self-check for the Data Comparison page.

Run:  python check_data_comparison.py
Uses synthetic fixtures, so it needs no real export files.
"""

import io

import pandas as pd

import data_comparison as dc

COLUMNS = "Sr #,Consumer Name,F/H Name,Sector,Locality,Rate Type,Connection No.,Status,Actions"

# Row 9 is in an excluded sector, 10 is commercial BY SECTOR, and 11 sits in an
# ordinary sector on a commercial RATE — the three cases the classification has
# to keep apart.
OLD_CSV = COLUMNS + """
1,ALI,AKBAR,Waris Colony,Zone B,DOMESTIC,12020001,Regular Connection,Edit
2,BILAL,AKBAR,Waris Colony,Zone B,DOMESTIC,0012020002,Regular Connection,Edit
3,CARIM,DAWOOD,Ghala Mandi,Zone A,DOMESTIC,12020003,Suspended,Edit
4,SHUT,X,Waris Colony,Zone B,DOMESTIC,12020004,Closed,Edit
5,CASED,Y,Waris Colony,Zone B,DOMESTIC,12020005,Regular Connection,Edit
6,SUSPENDED ONE,S,Waris Colony,Zone B,DOMESTIC,12020007,Regular Connection,Edit
7,PENDING ONE,P,Ghala Mandi,Zone A,DOMESTIC,12020008,Regular Connection,Edit
8,VANISHED,V,Ghala Mandi,Zone A,DOMESTIC,12020009,Regular Connection,Edit
9,ZAIN ONE,Z,ZAIN CITY CHACK NO 13/G,Zone C,DOMESTIC,58010001,Regular Connection,Edit
10,CORNER SHOP,Q,COMMERCIAL,SHOP,6 MONTH COMERCIAL ( SHOPS),84010001,Regular Connection,Edit
11,SHOP INSIDE,R,Waris Colony,Zone B,1 MONTH COMMERCIAL,12020010,Regular Connection,Edit
"""

NEW_CSV = COLUMNS.replace(",Actions", "") + """
1,ALI,AKBAR,Waris Colony,Zone B,DOMESTIC,12020001,Closed
2,BILAL,AKBAR,Waris Colony,Zone B,DOMESTIC,12020002,Regular Connection
3,CARIM,DAWOOD,Ghala Mandi,Zone A,DOMESTIC,12020003,Regular Connection
4,SHUT,X,Waris Colony,Zone B,DOMESTIC,12020004,Closed
5,cased,Y,waris colony,Zone B,DOMESTIC,12020005,Regular Connection
6,SUSPENDED ONE,S,Waris Colony,Zone B,DOMESTIC,12020007,Suspended
7,PENDING ONE,P,Ghala Mandi,Zone A,DOMESTIC,12020008,New Demand
9,ZAIN ONE,Z,ZAIN CITY CHACK NO 13/G,Zone C,DOMESTIC,58010001,Closed
10,CORNER SHOP,Q,COMMERCIAL,SHOP,6 MONTH COMERCIAL ( SHOPS),84010001,Closed
11,SHOP INSIDE,R,Waris Colony,Zone B,1 MONTH COMMERCIAL,12020010,Regular Connection
12,BRAND NEW,Z,Waris Colony,Zone B,DOMESTIC,12020011,Regular Connection
13,NOT YET,W,Waris Colony,Zone B,DOMESTIC,12020012,New Demand
14,BRAND NEW,Z,Waris Colony,Zone B,DOMESTIC,12020011,Regular Connection
"""


def read(text):
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)


def main():
    old, new = read(OLD_CSV), read(NEW_CSV)
    result = dc.build_comparison(old, new, "old.csv", "new.csv")
    summary = result["summary"]

    # --- classification comes from the Handover Register -------------------
    from handover import STATUS_MAP, _status_of, _type_of, is_commercial  # noqa: PLC0415
    assert dc._status_of is _status_of and dc._type_of is _type_of
    assert dc.is_commercial is is_commercial
    assert STATUS_MAP["regular connection"] == "Active", "Active and Regular are one category"

    # --- the excluded sector never reaches any figure ----------------------
    assert summary["old"]["excluded"] == 1 and summary["new"]["excluded"] == 1
    assert all("58010001" not in c["conn"] for c in result["changes"]), (
        "an excluded sector cannot appear in the change list either"
    )

    # --- summary, counted once per connection ------------------------------
    assert summary["old"]["entries"] == 10
    assert summary["new"]["entries"] == 12 and summary["new"]["connections"] == 11, (
        "the repeated row is an entry but not a second connection"
    )
    # Commercial is decided by SECTOR; a commercial RATE in an ordinary sector
    # keeps a record out of the domestic figure without moving it into the
    # commercial one, exactly as the Consumer List counts it.
    assert summary["old"]["domestic_active_regular"] == 6
    assert summary["old"]["commercial_active"] == 1
    assert summary["old"]["total_active"] == 8
    assert summary["old"]["domestic_commercial_rate"] == 1

    # Every connection counted once: the repeated 12020011 row is a second
    # Active ROW but not a second Active connection, and must not inflate this.
    assert summary["new"]["domestic_active_regular"] == 4
    assert summary["new"]["commercial_active"] == 0, "the one commercial connection closed"
    assert summary["new"]["total_active"] == 5
    assert summary["new"]["active_rows"] == 6, "row counting would have said 6"
    assert result["difference"] == -3

    # The three figures must account for the total, with the odd ones named.
    for side in ("old", "new"):
        s = summary[side]
        assert (s["domestic_active_regular"] + s["commercial_active"]
                + s["domestic_commercial_rate"]) == s["total_active"]

    # --- only connections that crossed the Active line ---------------------
    by_conn = {c["conn"]: c for c in result["changes"]}
    assert result["counts"]["all"] == 7, sorted(by_conn)
    # Unchanged Active, however differently it is now spelled.
    assert "12020005" not in by_conn, "CASED -> cased is not a status change"
    # Leading zeros are not a difference: 0012020002 and 12020002 are one
    # connection, Active in both files, so it is not listed.
    assert "12020002" not in by_conn
    assert "12020004" not in by_conn, "Closed in both files never moved"
    assert "12020012" not in by_conn, "a new connection that is not Active changes no count"

    # --- the four named movements ------------------------------------------
    assert by_conn["12020001"]["kind"] == "closed"
    assert (by_conn["12020001"]["old"], by_conn["12020001"]["new"]) == ("Active", "Closed")
    assert by_conn["84010001"]["kind"] == "closed", "a commercial connection closing counts too"
    assert by_conn["12020003"]["kind"] == "resumed"
    assert (by_conn["12020003"]["old"], by_conn["12020003"]["new"]) == ("Suspended", "Active")
    assert by_conn["12020007"]["kind"] == "suspended"
    assert result["counts"]["closed"] == 2 and result["counts"]["suspended"] == 1
    assert result["counts"]["resumed"] == 1 and result["counts"]["activated"] == 0

    # Movements that are not one of the four still change the Active count, so
    # they are reported rather than dropped.
    assert by_conn["12020008"]["kind"] == "other"
    assert by_conn["12020009"]["new"] == dc.MISSING_NEW
    assert by_conn["12020011"]["old"] == dc.MISSING_OLD
    assert result["counts"]["other"] == 3

    # --- the arithmetic has to close ---------------------------------------
    assert result["lost"] == 5 and result["gained"] == 2
    assert (summary["old"]["total_active"] - result["lost"] + result["gained"]
            == summary["new"]["total_active"]), "old - lost + gained must equal new"
    assert result["residual"] == 0, "totals and movements are both per connection"

    # The point of counting connections rather than rows: an export that serves
    # the same page again must not report growth. Three copies of the newer
    # file leave every Active figure exactly where it was.
    tripled = pd.concat([read(NEW_CSV)] * 3, ignore_index=True)
    same = dc.build_comparison(read(OLD_CSV), tripled, "old.csv", "tripled.csv")
    for key in ("domestic_active_regular", "commercial_active", "total_active"):
        assert same["summary"]["new"][key] == summary["new"][key], key
    assert same["summary"]["new"]["active_rows"] == 3 * summary["new"]["active_rows"], (
        "counted by row it would have tripled"
    )

    # --- identity comes from the file that has the connection --------------
    assert by_conn["12020011"]["name"] == "BRAND NEW"
    assert by_conn["12020009"]["name"] == "VANISHED", "taken from the older file"
    assert by_conn["12020009"]["father"] == "V"
    assert by_conn["12020001"]["sector"] == "Waris Colony"
    assert by_conn["84010001"]["locality"] == "SHOP"

    # --- table, columns and filters ----------------------------------------
    headers, rows, total = dc.change_rows(result)
    assert headers == ["Connection No.", "Consumer Name", "Father Name",
                       "Sector", "Locality", "Old Status", "New Status"]
    assert total == 7 and len(rows) == 7

    _, closed_rows, _ = dc.change_rows(result, kind="closed")
    assert {r[0] for r in closed_rows} == {"12020001", "84010001"}
    _, ghala, _ = dc.change_rows(result, sector="Ghala Mandi")
    assert {r[0] for r in ghala} == {"12020003", "12020008", "12020009"}
    _, searched, _ = dc.change_rows(result, search="vanished")
    assert len(searched) == 1 and searched[0][1] == "VANISHED"
    _, composed, _ = dc.change_rows(result, kind="other", sector="Ghala Mandi")
    assert {r[0] for r in composed} == {"12020008", "12020009"}, "filters compose"
    _, capped, capped_total = dc.change_rows(result, limit=2)
    assert len(capped) == 2 and capped_total == 7, "the cap never hides the true count"

    # --- records with no connection number ---------------------------------
    # The live list files a few records under 0, 00 or 0000000000. There is
    # nothing to match those against, so they cannot be counted or compared —
    # but they must be reported rather than quietly vanish from the totals.
    blanks = read(OLD_CSV.rstrip("\n") +
                  "\n12,NO NUMBER,N,Waris Colony,Zone B,DOMESTIC,0000000000,Regular Connection,Edit"
                  "\n13,ALSO NONE,N,Waris Colony,Zone B,DOMESTIC,00,Closed,Edit\n")
    blank_result = dc.build_comparison(blanks, read(NEW_CSV), "old.csv", "new.csv")
    blank_old = blank_result["summary"]["old"]
    assert blank_old["blank"] == 2 and blank_old["blank_active"] == 1
    assert blank_old["entries"] == 12, "they are entries"
    assert blank_old["total_active"] == summary["old"]["total_active"], (
        "but a record with no connection number is no connection"
    )
    assert blank_old["active_rows"] == summary["old"]["active_rows"] + 1, (
        "it is still an Active row in the file, and the row figure says so"
    )
    assert blank_result["counts"]["all"] == result["counts"]["all"], (
        "and cannot appear as a change either"
    )

    # --- file health --------------------------------------------------------
    # An export that repeats a page has the right number of rows and the wrong
    # number of connections. That is a broken export, not deleted records.
    assert result["health"]["old"]["incomplete"] is False
    assert result["health"]["new"]["incomplete"] is False, "13 rows is below the floor"

    repeated = pd.concat([read(NEW_CSV)] * 20, ignore_index=True)
    doubled = dc.build_comparison(read(OLD_CSV), repeated, "old.csv", "repeated.csv")
    assert doubled["health"]["new"]["incomplete"] is True
    assert doubled["health"]["new"]["distinct"] == result["health"]["new"]["distinct"], (
        "repeating rows adds no connections"
    )
    # And the audit itself is unmoved by the repetition.
    assert doubled["summary"]["new"]["total_active"] == summary["new"]["total_active"], (
        "repeating rows adds no Active connection"
    )
    assert doubled["counts"]["all"] == result["counts"]["all"], "and no movement"

    # --- no change at all ---------------------------------------------------
    same = dc.build_comparison(read(OLD_CSV), read(OLD_CSV), "a.csv", "b.csv")
    assert same["counts"]["all"] == 0 and same["difference"] == 0
    assert same["lost"] == 0 and same["gained"] == 0

    # --- a file missing the columns is refused, not silently mis-read -------
    try:
        dc.classify(pd.DataFrame({"Consumer Name": ["A"]}))
    except ValueError as exc:
        assert "Connection No." in str(exc)
    else:
        raise AssertionError("a file with no Connection No. column must be refused")

    print("check_data_comparison: all checks passed")


if __name__ == "__main__":
    main()
