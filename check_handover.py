"""Self-check for the Handover Register join, filters, and snapshot lock.

Run:  python check_handover.py
Uses a synthetic 8-row fixture, so it needs no real export files.
"""

import io
import json
import os
import shutil

import pandas as pd

import handover

HANDOVER_CSV = """Sr #,Consumer Name,F/H Name,Sector,Locality,Rate Type,Connection No.,Connection Date,Status
1,ALI,AKBAR,Waris Colony,Waris Colony Zone B,6 Month Jan26 To June26,12020001,01/07/2023,Regular Connection
2,BILAL,AKBAR,Waris Colony,Waris Colony Zone B,DOMESTIC (NEW CONNECTION),00012020002,01/07/2023,Closed
3,SHOP ONE,--,Ghala Mandi,Ghala Mandi Zone A,6 MONTH COMERCIAL ( SHOPS ),0010010002,01/07/2023,Suspended
4,DAUD,KARIM,Waris Colony,Waris Colony Zone B,DOMESTIC,12020004,01/07/2023,New Demand
5,SAME NUM A,X,Waris Colony,Waris Colony Zone B,DOMESTIC,777,01/07/2023,Regular Connection
6,SAME NUM B,Y,Ghala Mandi,Ghala Mandi Zone A,DOMESTIC,777,01/07/2023,Regular Connection
7,TWIN,Z,Waris Colony,Waris Colony Zone B,DOMESTIC,888,01/07/2023,Regular Connection
8,NO NUMBER,Q,Waris Colony,Waris Colony Zone B,DOMESTIC,0,01/07/2023,Regular Connection
"""

ARREARS_CSV = """Sr.,Consumer Name,Sector,Locality,Connection Number,Connection Date,Total Arrears,Status
1,ALI,Waris Colony,Waris Colony Zone B,12020001,01/07/2023,1500.00,Open
2,BILAL,Waris Colony,Waris Colony Zone B,12020002,01/07/2023,250.50,Closed
3,SHOP ONE,Ghala Mandi,Ghala Mandi Zone A,0010010002,01/07/2023,13040.00,Suspended
5,SAME NUM A,Waris Colony,Waris Colony Zone B,0777,01/07/2023,100.00,Open
6,SAME NUM B,Ghala Mandi,Ghala Mandi Zone A,777,01/07/2023,200.00,Open
7,TWIN,Waris Colony,Waris Colony Zone B,888,01/07/2023,10.00,Open
8,TWIN,Waris Colony,Waris Colony Zone B,888,01/07/2023,20.00,Open
9,NOBODY,Waris Colony,Waris Colony Zone B,0,01/07/2023,99.00,Open
"""


def read(text):
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)


def main():
    merged, stats = handover.build_handover_dataset(read(HANDOVER_CSV), read(ARREARS_CSV))
    by_name = {row["Consumer Name"]: row for _, row in merged.iterrows()}

    # --- join ------------------------------------------------------------
    assert len(merged) == 8, "the join must never add or drop handover rows"
    assert by_name["ALI"]["Total Arrears"] == 1500.0
    # Leading zeros differ between the two files but must still match.
    assert by_name["BILAL"]["Total Arrears"] == 250.5
    # Connection no. 777 is reused in two sectors: sector/locality separates them.
    assert by_name["SAME NUM A"]["Total Arrears"] == 100.0
    assert by_name["SAME NUM B"]["Total Arrears"] == 200.0
    # 888 is duplicated on the arrears side with nothing to separate it:
    # flag it, never guess or silently pick one.
    assert by_name["TWIN"]["Total Arrears"] == 0.0
    assert by_name["TWIN"]["Arrears Match"].startswith("Ambiguous"), by_name["TWIN"]["Arrears Match"]
    assert by_name["NO NUMBER"]["Arrears Match"] == "No connection number"
    assert by_name["DAUD"]["Arrears Match"] == "Not found in arrears file"
    assert stats["ambiguous"] == 1 and stats["no_connection"] == 1 and stats["not_found"] == 1

    # --- derived columns -------------------------------------------------
    assert by_name["ALI"]["Connection Status"] == "Active"
    assert by_name["BILAL"]["Connection Status"] == "Closed"
    assert by_name["SHOP ONE"]["Connection Status"] == "Suspended"
    assert by_name["DAUD"]["Connection Status"] == "New Demand"
    assert by_name["SHOP ONE"]["Connection Type"] == "Commercial"   # "COMERCIAL" spelling
    assert by_name["ALI"]["Connection Type"] == "Regular"
    assert by_name["ALI"]["Zone"] == "B" and by_name["SHOP ONE"]["Zone"] == "A"

    # --- filters ---------------------------------------------------------
    empty = {k: [] for k in handover.FILTER_FIELDS}
    active_regular = handover.apply_filters(merged, {**empty, "status": ["Active"], "type": ["Regular"]})
    assert set(active_regular["Consumer Name"]) == {"ALI", "SAME NUM A", "SAME NUM B", "TWIN", "NO NUMBER"}
    commercial = handover.apply_filters(merged, {**empty, "type": ["Commercial"]})
    assert list(commercial["Consumer Name"]) == ["SHOP ONE"]
    suspended = handover.apply_filters(merged, {**empty, "status": ["Suspended"]})
    assert list(suspended["Consumer Name"]) == ["SHOP ONE"]

    # --- sector summary --------------------------------------------------
    rows, grand = handover.build_sector_summary(merged)
    assert grand["total"] == 8
    assert grand["active"] + grand["suspended"] + grand["closed"] + grand["new_demand"] + grand["other"] == 8
    assert grand["regular"] + grand["commercial"] == 8
    assert round(grand["arrears"], 2) == round(merged["Total Arrears"].sum(), 2)
    waris = next(r for r in rows if r["sector"] == "Waris Colony")
    assert waris["total"] == 6 and waris["commercial"] == 0

    # --- printed register sections ---------------------------------------
    # The Consumer List prints one block per sector: heading, one summary line,
    # then the rows. The sector is the heading, so it leaves the detail table.
    cols = ["Sr #", "Consumer Name", "Sector", "Locality", "Total Arrears"]
    sections = handover.build_sections(merged, cols)
    assert [s["sector"] for s in sections] == ["Ghala Mandi", "Waris Colony"]
    assert "Sector" not in sections[0]["columns"], "sector repeats the heading"
    assert "Locality" in sections[0]["columns"], "only the sector column is dropped"
    waris_block = next(s for s in sections if s["sector"] == "Waris Colony")
    # The one summary line must agree with the rows printed under it.
    assert waris_block["summary"]["total"] == len(waris_block["rows"]) == 6
    assert waris_block["summary"]["active"] == 4 and waris_block["summary"]["commercial"] == 0
    assert sum(s["summary"]["total"] for s in sections) == 8

    # --- PDF markup safety -------------------------------------------------
    # Reportlab parses Paragraph text as XML. Real consumer names in the
    # register carry stray "<" and "&" from data entry; unescaped, either one
    # raises a parse error that kills the whole PDF export.
    hostile = [["Ali M<Ahmad", "Traders & Sons", "<b>unclosed", "<para>"]]
    wrapped = handover._wrap_rows(hostile, {0, 1, 2, 3}, font_size=6.5)
    assert len(wrapped[0]) == 4, "every hostile cell must survive as a flowable"
    assert handover._esc("a<b>&c") == "a&lt;b&gt;&amp;c"

    # --- signature configuration -----------------------------------------
    from werkzeug.datastructures import MultiDict

    # No mention of signatures in the request -> the three defaults, last page.
    default = handover.read_signature_config(MultiDict())
    assert default["fields"] == handover.DEFAULT_SIGNATURE_FIELDS
    assert default["position"] == "last", "last page only is the default placement"
    # Panel submitted with custom labels, in order.
    custom = handover.read_signature_config(
        MultiDict([("sigset", "1"), ("sigpos", "every"), ("sig", "Outgoing"), ("sig", "Incoming")])
    )
    assert custom["fields"] == ["Outgoing", "Incoming"] and custom["position"] == "every"
    # Panel submitted with every field removed -> print nothing, not the defaults.
    emptied = handover.read_signature_config(MultiDict([("sigset", "1")]))
    assert emptied["fields"] == [] and emptied["position"] == "none"
    # Blank labels dropped, count capped, unknown placement falls back to last.
    noisy = MultiDict([("sigset", "1"), ("sigpos", "sideways")] +
                      [("sig", f"F{i}") for i in range(10)] + [("sig", "   ")])
    capped = handover.read_signature_config(noisy)
    assert len(capped["fields"]) == handover.MAX_SIGNATURE_FIELDS
    assert capped["position"] == "last"

    # --- snapshot lock ---------------------------------------------------
    snap_dir = os.path.join(handover._snapshot_dir(), "selfcheck-tmp")
    shutil.rmtree(snap_dir, ignore_errors=True)
    os.makedirs(snap_dir)
    try:
        merged.to_csv(os.path.join(snap_dir, "data.csv"), index=False)
        with open(os.path.join(snap_dir, "meta.json"), "w", encoding="utf-8") as fh:
            json.dump({"locked": True, "row_count": len(merged)}, fh)
        frozen, meta = handover.load_dataset("selfcheck-tmp")
        assert meta["locked"] is True and len(frozen) == 8
        assert round(frozen["Total Arrears"].sum(), 2) == round(merged["Total Arrears"].sum(), 2)
    finally:
        shutil.rmtree(snap_dir, ignore_errors=True)

    print("check_handover: all checks passed")


if __name__ == "__main__":
    main()
