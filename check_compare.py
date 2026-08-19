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
6,SUSPENDED ONE,S,Waris Colony,Waris Zone B,DOMESTIC,12020007,Regular Connection,Edit
7,PENDING ONE,P,Ghala Mandi,Ghala Zone A,DOMESTIC,12020008,Regular Connection,Edit
8,VANISHED,V,Ghala Mandi,Ghala Zone A,DOMESTIC,12020009,Regular Connection,Edit
"""

NEW_CSV = """Sr #,Consumer Name,F/H Name,Sector,Locality,Rate Type,Connection No.,Status
1,ALI,AKBAR,Waris Colony,Waris Zone B,DOMESTIC,12020001,Closed
2,BILAL,AKBAR,Waris Colony,Waris Zone B,DOMESTIC,12020002,Regular Connection
3,CARIM,DAWOOD,Ghala Mandi,Ghala Zone A,DOMESTIC,12020003,Regular Connection
5,cased,Y,waris colony,Waris Zone B,DOMESTIC,12020005,Regular Connection
6,BRAND NEW,Z,Waris Colony,Waris Zone B,DOMESTIC,12020006,Regular Connection
7,DUPE,Q,Waris Colony,Waris Zone B,DOMESTIC,12020006,Regular Connection
8,SUSPENDED ONE,S,Waris Colony,Waris Zone B,DOMESTIC,12020007,Suspended
9,PENDING ONE,P,Ghala Mandi,Ghala Zone A,DOMESTIC,12020008,New Demand
"""


def read(text):
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)


def main():
    old, new = read(OLD_CSV), read(NEW_CSV)
    result = compare.build_comparison(old, new, "old.csv", "new.csv")

    # --- structure ---------------------------------------------------------
    assert result["files"]["old"]["rows"] == 8 and result["files"]["new"]["rows"] == 8
    assert result["columns"]["removed"] == ["Actions"]
    assert result["columns"]["added"] == []
    # "Sr #" is a row counter, not data, so it is never compared.
    assert "Sr #" not in result["columns"]["compared"]

    # --- matching ----------------------------------------------------------
    # 0012020002 and 12020002 are the same connection: leading zeros are not
    # a difference, so BILAL must match rather than look added and removed.
    assert result["matching"]["common"] == 6, result["matching"]
    assert result["matching"]["added"] == ["12020006"]
    # 12020004 was Closed and 12020009 was Active; both vanish from the newer file.
    assert result["matching"]["removed"] == ["12020004", "12020009"]

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
    assert status["counted"] == {"old": 8, "new": 7}
    assert status["old"]["Active"] == 6 and status["new"]["Active"] == 4
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
    assert len(status["records"]) == 4

    # --- active connection difference ---------------------------------------
    # Three figures, then only the connections that moved into or out of Active.
    diff = result["active_diff"]
    assert diff["old_active"] == 6
    assert diff["new_active"] == 4
    assert diff["difference"] == -2

    # The arithmetic has to close: old - lost + gained == new.
    assert diff["old_active"] - len(diff["lost"]) + len(diff["gained"]) == diff["new_active"]

    lost = {r["connection"]: r for r in diff["lost"]}
    gained = {r["connection"]: r for r in diff["gained"]}
    assert set(lost) == {"12020001", "12020007", "12020008", "12020009"}
    # 12020003 was Suspended and is now Active — the reverse case counts too.
    assert set(gained) == {"12020003", "12020006"}

    # Each carries where it went, including "missing" when the newer file has
    # no such connection at all.
    assert lost["12020001"]["new"] == "Closed"
    assert lost["12020007"]["new"] == "Suspended"
    assert lost["12020008"]["new"] == "New Demand"
    assert lost["12020009"]["new"] == compare.MISSING_LABEL
    assert lost["12020001"]["consumer"] == "ALI" and lost["12020001"]["father"] == "AKBAR"

    # A connection absent from the baseline but Active in the newer file counts
    # as gained, with its identity taken from the file that has it.
    assert gained["12020006"]["old"] == compare.NOT_PRESENT_LABEL
    assert gained["12020006"]["consumer"] == "BRAND NEW"

    # Connections that were Active in both files are never listed.
    assert "12020002" not in lost and "12020002" not in gained
    assert "12020005" not in lost and "12020005" not in gained
    # One that was not Active in the baseline can only ever appear as gained.
    assert "12020003" not in lost and gained["12020003"]["old"] == "Suspended"

    # --- audit table and filters -------------------------------------------
    headers, rows = compare.audit_rows(result)
    assert headers == ["Connection No.", "Consumer Name", "Father Name",
                       "Sector", "Old Status", "New Status"]
    assert len(rows) == 6, "four lost plus two gained, and nothing unchanged"

    _, lost_rows = compare.audit_rows(result, view="lost")
    _, gained_rows = compare.audit_rows(result, view="gained")
    assert len(lost_rows) == 4 and len(gained_rows) == 2

    _, ghala = compare.audit_rows(result, sector="Ghala Mandi")
    # 12020003 is in Ghala Mandi too and became Active, so it belongs here.
    assert {r[0] for r in ghala} == {"12020003", "12020008", "12020009"}
    _, searched = compare.audit_rows(result, search="vanished")
    assert len(searched) == 1 and searched[0][1] == "VANISHED"
    _, composed = compare.audit_rows(result, view="gained", sector="Waris Colony")
    assert {r[0] for r in composed} == {"12020006"}, "filters compose"

    # --- file health --------------------------------------------------------
    # A paginated export that repeats a page yields a file of the right length
    # whose connections are mostly duplicates. That must be reported as an
    # incomplete file, not read as thousands of deleted records.
    health = result["health"]
    assert health["old"]["incomplete"] is False
    assert health["new"]["incomplete"] is False, "the fixture files are healthy"

    repeated = read(NEW_CSV)
    repeated = pd.concat([repeated] * 20, ignore_index=True)   # same rows, over and over
    doubled = compare.build_comparison(read(OLD_CSV), repeated, "old.csv", "repeated.csv")
    assert doubled["health"]["new"]["incomplete"] is True
    assert doubled["health"]["new"]["distinct"] == health["new"]["distinct"], (
        "repeating rows adds no connections"
    )
    assert doubled["health"]["new"]["unique_ratio"] < compare.UNIQUE_RATIO_FLOOR
    # And the audit itself is unmoved by the repetition.
    assert doubled["active_diff"]["new_active"] == result["active_diff"]["new_active"]

    # --- key normalisation -------------------------------------------------
    assert compare._key(" 00-1202/0001 ") == "12020001"
    assert compare._key("00502-B") != compare._key("00502"), "a suffix is a different connection"
    assert compare._key("") == "" and compare._key(None) == ""
    assert compare.status_of("regular connection") == "Active"
    assert compare.status_of(" CLOSED ") == "Closed"

    print("check_compare: all checks passed")


if __name__ == "__main__":
    main()
