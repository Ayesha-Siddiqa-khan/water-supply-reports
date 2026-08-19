"""Self-check for the File Comparison / Data Integrity engine.

Run:  python check_compare.py
Uses synthetic fixtures, so it needs no real export files.
"""

import io

import pandas as pd

import compare

OLD_CSV = """Sr #,Consumer Name,F/H Name,Sector,Locality,Rate Type,Connection No.,Status,Actions
1,ALI,AKBAR,Waris Colony,Waris Zone B,DOMESTIC,12020001,Regular Connection,Edit
2,BILAL,AKBAR,Waris Colony,Waris Zone B,DOMESTIC,0012020002,Regular Connection,Edit
3,CARIM,DAWOOD,Ghala Mandi,Ghala Zone A,DOMESTIC,12020003,Suspended,Edit
4,GONE ONE,X,Waris Colony,Waris Zone B,DOMESTIC,12020004,Closed,Edit
5,CASED,Y,Waris Colony,Waris Zone B,DOMESTIC,12020005,Regular Connection,Edit
"""

NEW_CSV = """Sr #,Consumer Name,F/H Name,Sector,Locality,Rate Type,Connection No.,Status
1,ALI,AKBAR,Waris Colony,Waris Zone B,DOMESTIC,12020001,Closed
2,BILAL,AKBAR,Waris Colony,Waris Zone B,DOMESTIC,12020002,Regular Connection
3,CARIM,DAWOOD,Ghala Mandi,Ghala Zone A,DOMESTIC,12020003,Regular Connection
5,cased,Y,waris colony,Waris Zone B,DOMESTIC,12020005,Regular Connection
6,BRAND NEW,Z,Waris Colony,Waris Zone B,DOMESTIC,12020006,Regular Connection
7,DUPE,Q,Waris Colony,Waris Zone B,DOMESTIC,12020006,Regular Connection
"""


def read(text):
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)


def main():
    old, new = read(OLD_CSV), read(NEW_CSV)
    result = compare.build_comparison(old, new, "old.csv", "new.csv")

    # --- structure ---------------------------------------------------------
    assert result["files"]["old"]["rows"] == 5 and result["files"]["new"]["rows"] == 6
    assert result["columns"]["removed"] == ["Actions"]
    assert result["columns"]["added"] == []
    # "Sr #" is a row counter, not data, so it is never compared.
    assert "Sr #" not in result["columns"]["compared"]

    # --- matching ----------------------------------------------------------
    # 0012020002 and 12020002 are the same connection: leading zeros are not
    # a difference, so BILAL must match rather than look added and removed.
    assert result["matching"]["common"] == 4, result["matching"]
    assert result["matching"]["added"] == ["12020006"]
    assert result["matching"]["removed"] == ["12020004"]

    # --- duplicates --------------------------------------------------------
    assert [d["key"] for d in result["duplicates"]["new"]] == ["12020006"]
    assert result["duplicates"]["new"][0]["count"] == 2
    assert result["duplicates"]["old"] == []

    # --- field changes -----------------------------------------------------
    by_field = {(c["key"], c["field"]): c for c in result["changes"]}

    # A real edit.
    status_change = by_field[("12020001", "Status")]
    assert (status_change["old"], status_change["new"]) == ("Regular Connection", "Closed")
    assert status_change["cosmetic"] is False

    # Case-only differences are reported but flagged, so they cannot drown the
    # real edits: CASED -> cased and Waris Colony -> waris colony.
    assert by_field[("12020005", "Consumer Name")]["cosmetic"] is True
    assert by_field[("12020005", "Sector")]["cosmetic"] is True
    assert "12020005" not in result["changed_keys"], "case-only is not a modification"
    assert "12020005" in result["cosmetic_keys"]

    # A connection number written with leading zeros is the same connection,
    # so the difference is reported but never counted as a substantive edit.
    zeros = by_field[("12020002", "Connection No.")]
    assert zeros["cosmetic"] is True, "0012020002 vs 12020002 is the same connection"
    assert "12020002" not in result["changed_keys"]

    # --- status audit ------------------------------------------------------
    status = result["status"]
    # Counted once per connection, so the duplicated 12020006 counts once.
    assert status["counted"] == {"old": 5, "new": 5}
    assert status["old"]["Active"] == 3 and status["new"]["Active"] == 4
    assert status["old"]["Closed"] == 1 and status["new"]["Closed"] == 1

    transitions = status["transitions"]
    assert transitions["Active → Closed"] == 1
    assert transitions["Suspended → Active"] == 1

    records = {r["key"]: r for r in status["records"]}
    assert records["12020001"]["old"] == "Active" and records["12020001"]["new"] == "Closed"
    assert records["12020001"]["suspicious"] is True, "Active going Closed is worth flagging"
    assert records["12020003"]["suspicious"] is False, "Suspended reopening is not"
    assert records["12020001"]["consumer"] == "ALI"
    assert records["12020001"]["sector"] == "Waris Colony"

    # Totals that move in opposite directions must not hide each other: Active
    # is 3 then 4 even though one connection closed, because another opened.
    assert len(status["records"]) == 2

    # --- key normalisation -------------------------------------------------
    assert compare._key(" 00-1202/0001 ") == "12020001"
    assert compare._key("00502-B") != compare._key("00502"), "a suffix is a different connection"
    assert compare._key("") == "" and compare._key(None) == ""
    assert compare.status_of("regular connection") == "Active"
    assert compare.status_of(" CLOSED ") == "Closed"

    print("check_compare: all checks passed")


if __name__ == "__main__":
    main()
