"""Handover Register — independent feature module.

Builds a printable employee handover register by joining a Handover
connections export with an Arrears export on Connection Number.

Design notes
------------
* Self-contained Flask blueprint. Nothing in the existing report modules is
  touched; the only hooks into ``app.py`` are the blueprint registration and
  one sidebar link.
* Shared helpers (PDF table builder, cell wrapping, ``allowed_file`` ...) are
  imported lazily from ``app`` inside functions so this module can be imported
  from ``app.py`` without a circular import.
* Working data lives on disk (``uploads/handover/working.csv``) instead of the
  browser, because a handover file is ~28k rows — far past what localStorage or
  a POSTed JSON payload can carry.
* A finalised register is copied into ``uploads/handover/snapshots/<id>/`` and
  is never rewritten, so later status/arrears changes cannot alter history.
"""

import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
import sys
from datetime import datetime
from xml.sax.saxutils import escape

import pandas as pd
from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from werkzeug.utils import secure_filename

handover_bp = Blueprint("handover", __name__)

# ---------------------------------------------------------------------------
# Storage paths
# ---------------------------------------------------------------------------

def _app():
    """The app module that is already loaded.

    ``python app.py`` (the .bat launcher and the PyInstaller build) makes it
    ``__main__``; a plain ``from app import ...`` would then import all 12k
    lines a second time and build a second Flask application.
    """
    main = sys.modules.get("__main__")
    if hasattr(main, "UPLOAD_FOLDER"):
        return main
    import app

    return app


def _handover_dir() -> str:
    path = os.path.join(_app().UPLOAD_FOLDER, "handover")
    os.makedirs(path, exist_ok=True)
    return path


def _snapshot_dir() -> str:
    path = os.path.join(_handover_dir(), "snapshots")
    os.makedirs(path, exist_ok=True)
    return path


def _working_csv() -> str:
    return os.path.join(_handover_dir(), "working.csv")


def _working_meta() -> str:
    return os.path.join(_handover_dir(), "working_meta.json")


# ---------------------------------------------------------------------------
# Derived-value helpers
# ---------------------------------------------------------------------------

# Added by the join. Original Handover columns are never renamed or dropped.
ADDED_COLUMNS = [
    "Total Arrears",
    "Connection Status",
    "Connection Type",
    "Zone",
    "Arrears Match",
    "Data Flag",
]

STATUS_MAP = {
    "regular connection": "Active",
    "active": "Active",
    "open": "Active",
    "suspended": "Suspended",
    "closed": "Closed",
    "new demand": "New Demand",
    "new": "New Demand",
    "dead": "Dead",
}

# Localities write the zone as "Zone B", "Zone-C", 'Zone "C"' and "C Zone".
_ZONE_RE_A = re.compile(r"\bzone\s*[\"'\-:]*\s*([abc])\b")
_ZONE_RE_B = re.compile(r"\b([abc])\s*zone\b")


def _txt(value) -> str:
    """Collapse whitespace and lower-case — used for every exact-match key."""
    return " ".join(str(value or "").split()).strip().lower()


def _conn_key(value) -> str:
    """Alphanumerics only, lower-cased, leading zeros removed.

    Connection numbers are written as ``12020162`` in the handover export and
    ``0010010002`` in the arrears export, so both sides must be normalised the
    same way before they can be compared. Punctuation and spacing are dropped
    but a trailing letter is NOT: ``00502`` and ``00502-B`` are two different
    connections, and collapsing them loses one of their arrears balances.
    """
    return re.sub(r"[^0-9a-z]", "", str(value or "").lower()).lstrip("0")


def _status_of(raw) -> str:
    return STATUS_MAP.get(_txt(raw), "Other")


def _type_of(rate_type) -> str:
    """Commercial when the rate type says so — including the ``COMERCIAL``
    spelling that dominates the real data. Everything else is Regular."""
    text = _txt(rate_type)
    return "Commercial" if ("commercial" in text or "comercial" in text) else "Regular"


def _zone_of(sector, locality) -> str:
    text = _txt(f"{locality} {sector}")
    match = _ZONE_RE_A.search(text) or _ZONE_RE_B.search(text)
    return match.group(1).upper() if match else "Unassigned"


_AMOUNT_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _to_amount(value) -> float:
    """Parse a money cell tolerantly.

    Pulls the first number out rather than deleting non-digits, so "Rs. 1,500"
    does not become 0.15. Handles trailing-minus ("1500-") and accounting
    parentheses ("(500)"), both of which mean negative.
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value or "").replace(",", "").strip()
    if not text:
        return 0.0
    match = _AMOUNT_RE.search(text)
    if not match:
        return 0.0
    amount = float(match.group())
    # Trailing minus means negative only when it hangs off the digits
    # ("1234.50-"); "1500/-" is just how rupees are written.
    trailing_minus = re.search(r"\d\s*-$", text) is not None
    if amount > 0 and (trailing_minus or (text.startswith("(") and text.endswith(")"))):
        amount = -amount
    return amount


def _pick(columns, *candidates) -> str | None:
    """First column whose normalised name matches one of *candidates*."""
    norm = {re.sub(r"[^a-z0-9]+", " ", str(c).lower()).strip(): c for c in columns}
    for cand in candidates:
        key = re.sub(r"[^a-z0-9]+", " ", cand.lower()).strip()
        if key in norm:
            return norm[key]
    for cand in candidates:
        key = re.sub(r"[^a-z0-9]+", " ", cand.lower()).strip()
        for name, original in norm.items():
            if key and key in name:
                return original
    return None


def _esc(value) -> str:
    """Escape a data value for ReportLab's mini-markup parser.

    Paragraph text is parsed as XML. Real consumer names in this register carry
    stray ``<`` and ``&`` characters from data entry, and an unescaped one
    raises a parse error that takes the whole PDF export down with it. Anything
    reaching a Paragraph — cells, headers, sector names, signature labels — must
    come through here.
    """
    return escape(str(value if value is not None else ""))


def col_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_") or "col"


# ---------------------------------------------------------------------------
# Build the merged dataset
# ---------------------------------------------------------------------------

# Tiered exact-match keys. Connection Number alone is ambiguous in the real
# data (the same number is reused in different sectors), so each further tier
# adds another exact field. A row is only matched at a tier where its key is
# unique on the arrears side — nothing is ever matched by guesswork.
MATCH_TIERS = [
    ("Matched on Connection No.", ["conn"]),
    ("Matched on Connection No. + Sector/Locality", ["conn", "sector", "locality"]),
    ("Matched on Connection No. + Sector/Locality + Name", ["conn", "sector", "locality", "name"]),
    ("Matched on Connection No. + Sector/Locality + Name + Date", ["conn", "sector", "locality", "name", "date"]),
]


def _key_frame(df: pd.DataFrame, conn_col, sector_col, locality_col, name_col, date_col) -> dict:
    def series(col):
        return df[col].map(_txt) if col else pd.Series([""] * len(df), index=df.index)

    return {
        "conn": df[conn_col].map(_conn_key) if conn_col else pd.Series([""] * len(df), index=df.index),
        "sector": series(sector_col),
        "locality": series(locality_col),
        "name": series(name_col),
        "date": series(date_col),
    }


def _compose(parts: dict, fields: list[str]) -> pd.Series:
    out = parts[fields[0]]
    for field in fields[1:]:
        out = out + "|" + parts[field]
    return out


def build_handover_dataset(handover_df: pd.DataFrame, arrears_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Join arrears onto the handover rows and add the derived columns."""
    # Positional access below pairs rows with tier keys; a clean RangeIndex on
    # both frames keeps the label-based arrears lookup honest as well.
    handover_df = handover_df.copy().reset_index(drop=True)
    arrears_df = arrears_df.copy().reset_index(drop=True)

    h_cols, a_cols = list(handover_df.columns), list(arrears_df.columns)
    h_conn = _pick(h_cols, "connection no.", "connection no", "connection number", "connection")
    a_conn = _pick(a_cols, "connection number", "connection no.", "connection no", "connection")
    if not h_conn:
        raise ValueError("Handover file has no Connection Number column.")
    if not a_conn:
        raise ValueError("Arrears file has no Connection Number column.")
    a_arrears = _pick(a_cols, "total arrears", "arrears")
    if not a_arrears:
        raise ValueError("Arrears file has no Total Arrears column.")

    h_parts = _key_frame(
        handover_df, h_conn,
        _pick(h_cols, "sector"), _pick(h_cols, "locality"),
        _pick(h_cols, "consumer name", "name"), _pick(h_cols, "connection date"),
    )
    a_parts = _key_frame(
        arrears_df, a_conn,
        _pick(a_cols, "sector"), _pick(a_cols, "locality"),
        _pick(a_cols, "consumer name", "name"), _pick(a_cols, "connection date"),
    )

    arrears_values = arrears_df[a_arrears].map(_to_amount)
    has_conn = a_parts["conn"] != ""

    # For every tier keep only keys that identify exactly one arrears row.
    # Lookups map to the arrears ROW INDEX, not the amount, so a row can be
    # marked as consumed and never applied to two connections.
    tier_lookups = []
    for label, fields in MATCH_TIERS:
        keys = _compose(a_parts, fields)[has_conn]
        unique = keys[~keys.duplicated(keep=False)]
        tier_lookups.append((label, fields, dict(zip(unique, unique.index))))

    all_conn_keys = set(a_parts["conn"][has_conn])
    h_tier_keys = [_compose(h_parts, fields) for _, fields in MATCH_TIERS]

    dup_in_handover = h_parts["conn"].duplicated(keep=False) & (h_parts["conn"] != "")

    # Pass 1 — tiered exact matching.
    row_source = [None] * len(handover_df)     # arrears row index applied here
    labels = [None] * len(handover_df)
    consumed = set()
    unresolved: dict[str, list[int]] = {}
    for pos in range(len(handover_df)):
        conn = h_parts["conn"].iat[pos]
        if not conn:
            continue
        for tier_index, (tier_label, _fields, lookup) in enumerate(tier_lookups):
            source = lookup.get(h_tier_keys[tier_index].iat[pos])
            if source is not None and source not in consumed:
                row_source[pos], labels[pos] = source, tier_label
                consumed.add(source)
                break
        else:
            unresolved.setdefault(conn, []).append(pos)

    # Pass 2 — a connection number reused N times on both sides, with no field
    # left to separate the copies. Pairing them in file order consumes each
    # arrears row exactly once, so the register still reconciles to the penny;
    # the rows stay labelled so the pairing is visible in the exception report.
    arrears_by_conn: dict[str, list[int]] = {}
    for pos in range(len(arrears_df)):
        key = a_parts["conn"].iat[pos]
        if key:
            arrears_by_conn.setdefault(key, []).append(pos)
    for conn, positions in unresolved.items():
        spare = [i for i in arrears_by_conn.get(conn, []) if i not in consumed]
        if len(spare) != len(positions):
            continue
        for pos, source in zip(positions, spare):
            row_source[pos], labels[pos] = source, "Matched by file order (duplicate connection no.)"
            consumed.add(source)

    amounts, matches, flags = [], [], []
    for pos in range(len(handover_df)):
        conn = h_parts["conn"].iat[pos]
        dup_note = "Duplicate connection no. in handover file" if dup_in_handover.iat[pos] else ""
        if not conn:
            amounts.append(0.0)
            matches.append("No connection number")
            flags.append("No connection number in handover file")
        elif row_source[pos] is None:
            amounts.append(0.0)
            if conn in all_conn_keys:
                matches.append("Ambiguous — duplicate connection no. in arrears file")
                flag = "Arrears not applied — duplicate connection no. could not be resolved"
            else:
                matches.append("Not found in arrears file")
                flag = "Connection no. missing from arrears file"
            flags.append("; ".join(x for x in (flag, dup_note) if x))
        else:
            amounts.append(float(arrears_values.iat[row_source[pos]]))
            matches.append(labels[pos])
            note = "Arrears paired by file order — duplicate connection no." \
                if labels[pos].startswith("Matched by file order") else ""
            flags.append("; ".join(x for x in (note, dup_note) if x))

    sector_col = _pick(h_cols, "sector")
    locality_col = _pick(h_cols, "locality")
    status_col = _pick(h_cols, "status")
    rate_col = _pick(h_cols, "rate type")

    merged = handover_df.copy()
    # Never silently overwrite a source column of the same name — keep the
    # original alongside so "all original columns unchanged" stays true.
    for name in ADDED_COLUMNS:
        if name in merged.columns:
            merged.rename(columns={name: f"{name} (source)"}, inplace=True)

    merged["Total Arrears"] = amounts
    merged["Connection Status"] = (
        handover_df[status_col].map(_status_of) if status_col else "Other"
    )
    merged["Connection Type"] = (
        handover_df[rate_col].map(_type_of) if rate_col else "Regular"
    )
    merged["Zone"] = [
        _zone_of(
            handover_df[sector_col].iat[i] if sector_col else "",
            handover_df[locality_col].iat[i] if locality_col else "",
        )
        for i in range(len(handover_df))
    ]
    merged["Arrears Match"] = matches
    merged["Data Flag"] = flags

    # Summaries, filters and grouping address Sector/Locality by name. Exports
    # spell them differently often enough that _pick exists — so guarantee the
    # canonical names are present rather than 500 when they are not.
    for canonical, found in (("Sector", sector_col), ("Locality", locality_col)):
        if canonical not in merged.columns:
            merged[canonical] = handover_df[found] if found else ""

    merged = canonicalise_groups(merged)
    merged, excluded_rows = drop_excluded_sectors(merged)

    stats = {
        "excluded_rows": excluded_rows,
        "total_rows": int(len(merged)),
        "matched": int(sum(1 for m in matches if m.startswith("Matched"))),
        "matched_exact": int(sum(1 for m in matches if m == MATCH_TIERS[0][0])),
        "ambiguous": int(sum(1 for m in matches if m.startswith("Ambiguous"))),
        "not_found": int(sum(1 for m in matches if m == "Not found in arrears file")),
        "no_connection": int(sum(1 for m in matches if m == "No connection number")),
        "duplicate_in_handover": int(dup_in_handover.sum()),
        "paired_by_order": int(sum(1 for m in matches if m.startswith("Matched by file order"))),
        "arrears_rows": int(len(arrears_df)),
        "arrears_total_file": float(arrears_values.sum()),
        "arrears_total_applied": float(sum(amounts)),
        "arrears_unapplied": float(arrears_values.sum() - sum(amounts)),
        "handover_conn_col": h_conn,
        "arrears_conn_col": a_conn,
    }
    return merged, stats


# ---------------------------------------------------------------------------
# Load / filter / summarise
# ---------------------------------------------------------------------------

def load_dataset(snapshot_id: str | None = None) -> tuple[pd.DataFrame | None, dict]:
    """Return (rows, meta). Snapshots read their own frozen copy."""
    if snapshot_id:
        base = os.path.join(_snapshot_dir(), secure_filename(snapshot_id))
        data_path, meta_path = os.path.join(base, "data.csv"), os.path.join(base, "meta.json")
    else:
        data_path, meta_path = _working_csv(), _working_meta()
    if not os.path.exists(data_path):
        return None, {}
    df = pd.read_csv(data_path, dtype=str, keep_default_na=False)
    df["Total Arrears"] = df["Total Arrears"].map(_to_amount)
    if not snapshot_id:
        # A locked snapshot is left exactly as it was finalised.
        df = canonicalise_groups(df)
        df, _ = drop_excluded_sectors(df)
        df = df.reset_index(drop=True)
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
    return df, meta


FILTER_FIELDS = {
    "sector": "Sector",
    "locality": "Locality",
    "zone": "Zone",
    "status": "Connection Status",
    "type": "Connection Type",
}


def read_filters(args=None) -> dict:
    args = args if args is not None else request.args
    filters = {}
    for param in FILTER_FIELDS:
        values = [v for v in args.getlist(param) if str(v).strip()]
        filters[param] = values
    filters["flagged_only"] = str(args.get("flagged", "")).strip() in ("1", "true", "yes")
    return filters


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df
    for param, column in FILTER_FIELDS.items():
        values = filters.get(param) or []
        if values and column in out.columns:
            out = out[out[column].isin(values)]
    if filters.get("flagged_only"):
        out = out[out["Data Flag"].astype(str).str.strip() != ""]
    # One ordering for every consumer (preview, print, PDF, CSV, Excel) so a
    # register printed today matches the spreadsheet handed over with it.
    sort_cols = [c for c in ("Sector", "Locality") if c in out.columns]
    conn_col = _pick(list(out.columns), "connection no.", "connection no", "connection number")
    if conn_col:
        sort_cols.append(conn_col)
    return out.sort_values(sort_cols, kind="stable") if sort_cols else out


def filter_label(filters: dict) -> str:
    parts = []
    for param, column in FILTER_FIELDS.items():
        values = filters.get(param) or []
        if values:
            shown = ", ".join(values[:4]) + (f" +{len(values) - 4} more" if len(values) > 4 else "")
            parts.append(f"{column}: {shown}")
    if filters.get("flagged_only"):
        parts.append("Flagged rows only")
    return " | ".join(parts) if parts else "All connections (no filter)"


def summarise_block(df: pd.DataFrame, label: str = "", serial="") -> dict:
    """Count one printable block as a single summary line.

    Counts come straight from the status and type values, each record landing
    in exactly one status bucket. Taking build_sector_summary()[0] instead
    would drop rows whenever a block spans more than one sector.
    """
    status = df["Connection Status"]
    ctype = df["Connection Type"]
    commercial = is_commercial(df)
    return {
        "serial": serial,
        "sector": label,
        "total": int(len(df)),
        "active": int((status == "Active").sum()),
        # A "Regular Connection" is Active AND Regular together — never all
        # Active records or all Regular records counted independently.
        "active_regular": int(((status == "Active") & (ctype == "Regular")).sum()),
        "suspended": int((status == "Suspended").sum()),
        "closed": int((status == "Closed").sum()),
        "new_demand": int((status == "New Demand").sum()),
        "other": int((~status.isin(["Active", "Suspended", "Closed", "New Demand"])).sum()),
        # By rate type — these two always partition the block.
        "regular": int((ctype == "Regular").sum()),
        "commercial_type": int((ctype == "Commercial").sum()),
        # By sector — this is what places a record in the commercial section.
        "commercial": int(commercial.sum()),
        "arrears": float(df["Total Arrears"].sum()),
        "flagged": int((df["Data Flag"].astype(str).str.strip() != "").sum()),
    }


def build_sector_summary(df: pd.DataFrame) -> tuple[list[dict], dict]:
    empty = summarise_block(df.iloc[0:0] if len(df) else df, "GRAND TOTAL")
    if df.empty:
        return [], empty
    rows = [
        summarise_block(block, sector, serial)
        for serial, (sector, block) in enumerate(df.groupby("Sector", sort=True), start=1)
    ]
    grand = summarise_block(df, "GRAND TOTAL", "")
    return rows, grand


# The printed register heads each block with its sector name, so the summary
# line under it carries counts only — no sector column, no grand total row.
REGISTER_SUMMARY_COLUMNS = [
    ("total", "Total Entries", 0.17),
    ("active_regular", "Active + Regular", 0.17),
    ("new_demand", "New Demand", 0.15),
    ("closed", "Closed", 0.14),
    ("suspended", "Suspended", 0.15),
    ("arrears", "Total Arrears (Rs.)", 0.22),
]

# Commercial blocks are type-scoped already, so their active count is simply
# the Active records inside the block.
COMMERCIAL_SUMMARY_COLUMNS = [
    ("total", "Total Entries", 0.17),
    ("active", "Active", 0.17),
    ("new_demand", "New Demand", 0.15),
    ("closed", "Closed", 0.14),
    ("suspended", "Suspended", 0.15),
    ("arrears", "Total Arrears (Rs.)", 0.22),
]

# Spreadsheet/CSV summary exports keep the sector column and grand total —
# those are data extracts, not the printed register.
SUMMARY_COLUMNS = [
    ("serial", "SR", 0.05),
    ("sector", "Sector", 0.26),
    ("total", "Total", 0.08),
    ("active", "Active", 0.08),
    ("suspended", "Suspended", 0.09),
    ("closed", "Closed", 0.08),
    ("new_demand", "New Demand", 0.09),
    ("regular", "Regular", 0.08),
    ("commercial", "Commercial", 0.09),
    ("arrears", "Total Arrears (Rs.)", 0.10),
]

# The printed serial, generated per sector. The imported "Sr #" stays available
# as an optional column but is not used for numbering.
SERIAL_COLUMN = "Sr"

# Sector is deliberately NOT a default: every page repeats the sector name in
# its banner, and commercial records are their own blocks, so the column is
# redundant — dropping it is what buys ~40 records a page at 7pt instead of 30.
# It stays available as an optional column.
DEFAULT_DETAIL_COLUMNS = [
    "Consumer Name", "F/H Name", "Mobile", "Address",
    "Connection No.", "Total Arrears",
]

# Free text: wrapped and left-aligned. Everything else stays a plain centred
# string, which is also what keeps a 10k-row register building in seconds.
LEFT_COLUMNS = {"consumer name", "f/h name", "sector", "address"}
WRAP_COLUMNS = LEFT_COLUMNS | {"locality", "data flag", "arrears match"}


def detail_columns(df: pd.DataFrame) -> list[dict]:
    """All available detail columns, with the default register set pre-ticked."""
    defaults = {_txt(c) for c in DEFAULT_DETAIL_COLUMNS}
    return [
        {"key": col_key(c), "label": c, "default": _txt(c) in defaults}
        for c in df.columns
    ]


def selected_columns(df: pd.DataFrame, cols_param: str | None) -> list[str]:
    available = {col_key(c): c for c in df.columns}
    if cols_param:
        chosen = [available[k.strip()] for k in cols_param.split(",") if k.strip() in available]
        if chosen:
            return chosen
    return [c for c in df.columns if _txt(c) in {_txt(d) for d in DEFAULT_DETAIL_COLUMNS}]


# Sectors that do not exist in the real register and must never be counted,
# listed by their normalised name. "ZAIN CITY CHACK NO 13/G" carries its own
# 58010xxx connection block with no overlap against ZAIN CITY (PRIVATE
# SOCITIES) 54010xxx, so its records are dropped outright rather than merged.
EXCLUDED_SECTORS = {"zain city chack no 13/g"}


def drop_excluded_sectors(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove records belonging to sectors that are not real.

    Applied in the frame every consumer reads, so an excluded sector cannot
    reappear in a filter list, a summary, a detail page or an export.
    """
    if "Sector" not in df.columns or not EXCLUDED_SECTORS:
        return df, 0
    keep = ~df["Sector"].map(_txt).isin(EXCLUDED_SECTORS)
    return df[keep], int((~keep).sum())


def _canonical_labels(series) -> dict:
    """Map visually identical labels onto one spelling.

    Sector and locality names arrive with stray spaces and inconsistent case,
    which would otherwise split one sector into two headings and two summary
    lines. Variants that match once trimmed and case-folded are collapsed onto
    the spelling used by the most records (ties break alphabetically), and that
    winner is itself whitespace-collapsed so no heading carries stray spacing.
    """
    variants: dict[str, dict[str, int]] = {}
    for value in series:
        text = str(value)
        variants.setdefault(_txt(text), {})
        variants[_txt(text)][text] = variants[_txt(text)].get(text, 0) + 1
    mapping = {}
    for group in variants.values():
        winner = sorted(group.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        canonical = " ".join(winner.split())
        for spelling in group:
            mapping[spelling] = canonical
    return mapping


def canonicalise_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse duplicate Sector/Locality spellings before anything groups on them.

    Applied once, in the frame every consumer reads, so the filters, the
    on-screen summary, the PDF and the exports can never disagree about how
    many sectors there are. No record is added, dropped or reassigned — only
    the label it is grouped under is normalised.
    """
    for column in ("Sector", "Locality"):
        if column in df.columns:
            mapping = _canonical_labels(df[column])
            df[column] = df[column].map(lambda v: mapping.get(str(v), str(v)))
    return df


def is_commercial(df: pd.DataFrame) -> pd.Series:
    """Records belonging to the commercial register, by SECTOR.

    The source system files commercial connections under a sector literally
    named COMMERCIAL, subdivided by locality into the trade categories — HAMAM,
    SHOP, NURSERY/POULTRY/CATTLE FARM, PETROL PUMPs and so on. That sector is
    what places a record in the commercial section.

    Rate type deliberately does NOT place a record here. Twenty-six connections
    carry a commercial rate while sitting in an ordinary sector (a shop inside
    Baldia Colony, say); grouping those by locality would drop domestic names
    like "Nasirabbad Zone C" and "Zamindara Colony" into the commercial
    section. They stay under their own sector, where they belong, and their
    commercial rate still keeps them out of the Active + Regular count.
    """
    return df["Sector"].map(_txt) == "commercial"


def build_sections(frame: pd.DataFrame, columns: list[str],
                   summary_source: pd.DataFrame | None = None) -> list[dict]:
    """Split the register into printable blocks.

    Ordinary sectors come first, sector by sector, honouring the page filters.
    The commercial register always follows at the very end, broken down
    locality by locality — heading, summary, then that locality's consumers.

    The commercial part is built from the complete import rather than the
    filtered view, so every commercial locality appears even when the page is
    filtered to, say, Active + Regular, which would otherwise exclude every
    commercial record and print nothing at all.

    Each block is a heading, one summary line and its consumer rows, numbered
    from 1 within that block.
    """
    source = frame if summary_source is None else summary_source
    sections = []

    def add(heading, block, counted, summary_columns, group):
        body = detail_rows(block, columns)
        sections.append({
            "sector": heading,
            "group": group,
            "summary": summarise_block(counted, heading),
            "summary_columns": summary_columns,
            "columns": [SERIAL_COLUMN] + list(columns),
            "rows": [[str(i)] + row for i, row in enumerate(body, 1)],
        })

    # Ordinary sectors, sector by sector. The summary line describes the whole
    # sector from the complete import, so a status filter cannot zero out the
    # Closed/Suspended counts it exists to report.
    src_normal = source[~is_commercial(source)]
    for sector, block in frame[~is_commercial(frame)].groupby("Sector", sort=True):
        add(str(sector), block, src_normal[src_normal["Sector"] == sector],
            REGISTER_SUMMARY_COLUMNS, "normal")

    # The commercial register, locality by locality, always last and always
    # complete.
    src_commercial = source[is_commercial(source)]
    for locality, block in src_commercial.groupby("Locality", sort=True):
        add(str(locality), block, block, COMMERCIAL_SUMMARY_COLUMNS, "commercial")

    return sections


# ---------------------------------------------------------------------------
# Signature / approval section
# ---------------------------------------------------------------------------

DEFAULT_SIGNATURE_FIELDS = ["Handed Over By", "Taken Over By", "Verified By"]
SIGNATURE_POSITIONS = ("last", "every", "none")
MAX_SIGNATURE_FIELDS = 6


DEFAULT_WATERMARK_TEXT = "WATER SUPPLY MC CHISHTIAN"


def read_watermark_config(args=None) -> dict:
    """Watermark text and on/off state, read from the request.

    ``wmset`` plays the same role as ``sigset``: it marks a request that
    carried the watermark panel, so an unticked checkbox (which browsers omit
    entirely) reads as "off" rather than falling back to the default.
    """
    args = args if args is not None else request.args
    if args.get("wmset"):
        # Ticking the box with the text cleared means "stamp it" — fall back to
        # the standard legend rather than silently printing nothing.
        text = " ".join(str(args.get("wmtext") or "").split()) or DEFAULT_WATERMARK_TEXT
        enabled = bool(args.get("wm"))
    else:
        # Off unless asked for: a stamp over an official register is a
        # deliberate choice, not something to apply behind the user's back.
        text, enabled = DEFAULT_WATERMARK_TEXT, False
    return {"enabled": enabled, "text": text or DEFAULT_WATERMARK_TEXT}


def read_signature_config(args=None) -> dict:
    """Signature fields and placement, read from the request.

    ``sigset`` marks a form that carried the signature panel, which is what
    separates "the user removed every field" from "this URL never mentioned
    signatures" — the first must print nothing, the second gets the defaults.
    """
    args = args if args is not None else request.args
    position = (args.get("sigpos") or "").strip().lower()
    if position not in SIGNATURE_POSITIONS:
        position = "last"
    if args.get("sigset"):
        fields = [" ".join(str(v).split()) for v in args.getlist("sig")]
        fields = [f for f in fields if f][:MAX_SIGNATURE_FIELDS]
    else:
        fields = list(DEFAULT_SIGNATURE_FIELDS)
    if not fields:
        position = "none"
    return {"fields": fields, "position": position}


def detail_rows(df: pd.DataFrame, columns: list[str]) -> list[list[str]]:
    out = []
    for _, row in df[columns].iterrows():
        cells = []
        for col in columns:
            value = row[col]
            cells.append(f"{value:,.0f}" if col == "Total Arrears" else str(value))
        out.append(cells)
    return out


# ---------------------------------------------------------------------------
# Routes — page
# ---------------------------------------------------------------------------

def _list_snapshots() -> list[dict]:
    items = []
    base = _snapshot_dir()
    for name in sorted(os.listdir(base), reverse=True):
        meta_path = os.path.join(base, name, "meta.json")
        if not os.path.exists(meta_path):
            continue
        try:
            with open(meta_path, "r", encoding="utf-8") as fh:
                items.append(json.load(fh))
        except (OSError, json.JSONDecodeError):
            continue
    return items


def _render_page(snapshot_id: str | None = None):
    df, meta = load_dataset(snapshot_id)
    if df is None:
        if snapshot_id:
            flash("That handover snapshot no longer exists.")
            return redirect(url_for("handover.handover"))
        return render_template(
            "handover.html", active_page="handover", dataset=None,
            snapshots=_list_snapshots(), snapshot=None,
        )

    if snapshot_id:
        filters = meta.get("filters") or {}
        filters.setdefault("flagged_only", False)
        cols_param = meta.get("cols") or ""
        signature = meta.get("signature") or {
            "fields": list(DEFAULT_SIGNATURE_FIELDS), "position": "last",
        }
        watermark = meta.get("watermark") or {
            "enabled": True, "text": DEFAULT_WATERMARK_TEXT,
        }
    else:
        signature = read_signature_config()
        watermark = read_watermark_config()
        if not request.args:
            # Land on the primary handover list (Active + Regular) with the
            # filters spelled out in the URL. Preview, print, PDF, downloads and
            # finalise all read that same query string, so an implicit default
            # here would silently export a different population than is shown.
            return redirect(url_for("handover.handover", status="Active", type="Regular"))
        filters = read_filters()
        cols_param = request.args.get("cols", "")

    filtered = apply_filters(df, filters)
    summary_rows, grand = build_sector_summary(filtered)
    # Same complete-dataset figures the PDF's first page prints, so the screen
    # and the document can never disagree.
    commercial_mask = is_commercial(df)
    domestic_df, commercial_df = df[~commercial_mask], df[commercial_mask]
    overall = summarise_block(domestic_df)
    overall_sectors = domestic_df["Sector"].nunique()
    commercial_overall = summarise_block(commercial_df)
    commercial_localities = commercial_df["Locality"].nunique()
    columns = selected_columns(df, cols_param)
    preview_limit = 300
    flagged = filtered[filtered["Data Flag"].astype(str).str.strip() != ""]

    return render_template(
        "handover.html",
        active_page="handover",
        dataset=meta,
        snapshot=meta if snapshot_id else None,
        snapshot_id=snapshot_id,
        snapshots=_list_snapshots(),
        filters=filters,
        filter_text=filter_label(filters),
        options={
            param: sorted(v for v in df[column].astype(str).unique() if v.strip())
            for param, column in FILTER_FIELDS.items()
        },
        all_columns=detail_columns(df),
        selected_keys=[col_key(c) for c in columns],
        signature=signature,
        watermark=watermark,
        signature_positions=[
            ("last", "Last page only"), ("every", "Every page"), ("none", "Do not show"),
        ],
        max_signature_fields=MAX_SIGNATURE_FIELDS,
        summary_rows=summary_rows,
        grand=grand,
        overall=overall,
        overall_sectors=overall_sectors,
        commercial_overall=commercial_overall,
        commercial_localities=commercial_localities,
        domestic_cards=DOMESTIC_SUMMARY_CARDS,
        commercial_cards=COMMERCIAL_SUMMARY_CARDS,
        columns=columns,
        preview_rows=detail_rows(filtered.head(preview_limit), columns),
        preview_limit=preview_limit,
        row_count=len(filtered),
        total_count=len(df),
        flagged_rows=detail_rows(
            flagged.head(200),
            [c for c in ["Sr #", "Connection No.", "Consumer Name", "Sector", "Locality", "Arrears Match", "Data Flag"] if c in df.columns],
        ),
        flagged_columns=[c for c in ["Sr #", "Connection No.", "Consumer Name", "Sector", "Locality", "Arrears Match", "Data Flag"] if c in df.columns],
        flagged_count=len(flagged),
    )


@handover_bp.route("/handover", methods=["GET", "POST"])
def handover():
    main = _app()
    allowed_file, ajax_error, ajax_ok, is_ajax = (
        main.allowed_file, main.ajax_error, main.ajax_ok, main.is_ajax
    )

    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "clear":
            for path in (_working_csv(), _working_meta()):
                if os.path.exists(path):
                    os.remove(path)
            flash("Handover working data cleared. Finalised snapshots are kept.")
            return redirect(url_for("handover.handover"))

        if action == "finalize":
            return _finalize()

        if action == "upload":
            handover_file = request.files.get("handover_file")
            arrears_file = request.files.get("arrears_file")
            for label, upload in (("Consumer List", handover_file), ("Arrears List", arrears_file)):
                if not upload or not upload.filename:
                    msg = f"Please choose the {label} file."
                    return ajax_error(msg) if is_ajax() else (flash(msg) or redirect(url_for("handover.handover")))
                # ".csv.gz" is the compressed form of an allowed type.
                base = upload.filename[:-3] if upload.filename.lower().endswith(".gz") else upload.filename
                if not allowed_file(base):
                    msg = f"Unsupported file type: {upload.filename}"
                    return ajax_error(msg) if is_ajax() else (flash(msg) or redirect(url_for("handover.handover")))

            try:
                # Decompress up front so the recorded name and checksum describe
                # the real file, not whatever transport encoding carried it.
                h_name, h_bytes = _gunzip(handover_file.filename, handover_file.read())
                a_name, a_bytes = _gunzip(arrears_file.filename, arrears_file.read())
                handover_df = _read_bytes(h_name, h_bytes)
                arrears_df = _read_bytes(a_name, a_bytes)
                merged, stats = build_handover_dataset(handover_df, arrears_df)
            except Exception as exc:  # noqa: BLE001 — surfaced to the user
                msg = f"Could not build the register: {exc}"
                return ajax_error(msg) if is_ajax() else (flash(msg) or redirect(url_for("handover.handover")))

            merged.to_csv(_working_csv(), index=False)
            meta = {
                "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "handover_file": {
                    "name": secure_filename(h_name),
                    "rows": int(len(handover_df)),
                    "sha256": hashlib.sha256(h_bytes).hexdigest()[:16],
                },
                "arrears_file": {
                    "name": secure_filename(a_name),
                    "rows": int(len(arrears_df)),
                    "sha256": hashlib.sha256(a_bytes).hexdigest()[:16],
                },
                "stats": stats,
            }
            with open(_working_meta(), "w", encoding="utf-8") as fh:
                json.dump(meta, fh, ensure_ascii=False, indent=2)

            msg = (
                f"Register built. {stats['total_rows']:,} connections, "
                f"{stats['matched']:,} matched to arrears, "
                f"{stats['ambiguous'] + stats['not_found'] + stats['no_connection']:,} flagged."
            )
            if is_ajax():
                return ajax_ok(message=msg, redirect_url=url_for("handover.handover"))
            flash(msg)
            return redirect(url_for("handover.handover"))

        flash("Unknown handover action.")
        return redirect(url_for("handover.handover"))

    return _render_page()


def _gunzip(filename: str, blob: bytes) -> tuple[str, bytes]:
    """Transparently decompress a gzipped upload.

    The browser compresses both files before posting because the two exports
    together are ~12 MB and a Vercel serverless function rejects any request
    body over 4.5 MB. Detection is by magic bytes, so a hand-made ``.csv.gz``
    works too, and an uncompressed post (the local app) is left alone.
    """
    if blob[:2] == b"\x1f\x8b":
        blob = gzip.decompress(blob)
        if filename.lower().endswith(".gz"):
            filename = filename[:-3]
    return filename, blob


def _read_bytes(filename: str, blob: bytes) -> pd.DataFrame:
    """Read an uploaded CSV/XLSX as text so connection numbers keep leading zeros."""
    filename, blob = _gunzip(filename, blob)
    _, ext = os.path.splitext(filename)
    buf = io.BytesIO(blob)
    if ext.lower() == ".csv":
        return pd.read_csv(buf, dtype=str, keep_default_na=False)
    return pd.read_excel(buf, dtype=str).fillna("")


@handover_bp.route("/handover/status")
def handover_status():
    """Whether THIS instance still holds the working register.

    Serverless instances keep the register in a disposable /tmp, so the browser
    checks here before opening a report in a new tab and re-sends its stored
    copy if the instance that answers has nothing.
    """
    from flask import jsonify

    return jsonify({"ready": os.path.exists(_working_csv())})


@handover_bp.route("/handover/snapshot/<snapshot_id>")
def handover_snapshot(snapshot_id: str):
    return _render_page(snapshot_id)


# ---------------------------------------------------------------------------
# Finalise — locked historical snapshot
# ---------------------------------------------------------------------------

def _finalize():
    df, meta = load_dataset()
    if df is None:
        flash("Upload both files before finalising a handover.")
        return redirect(url_for("handover.handover"))

    filters = read_filters(request.form)
    cols_param = request.form.get("cols", "")
    filtered = apply_filters(df, filters)
    if filtered.empty:
        flash("The current filters select no connections — nothing to finalise.")
        return redirect(url_for("handover.handover"))

    from_officer = (request.form.get("from_officer") or "").strip()
    to_officer = (request.form.get("to_officer") or "").strip()
    if not from_officer or not to_officer:
        flash("Enter both the outgoing and incoming employee names before finalising.")
        return redirect(url_for("handover.handover"))

    now = datetime.now()
    snapshot_id = secure_filename(
        f"{now.strftime('%Y%m%d-%H%M%S')}-{from_officer[:20]}-to-{to_officer[:20]}"
    )
    base = os.path.join(_snapshot_dir(), snapshot_id)
    os.makedirs(base, exist_ok=True)
    filtered.to_csv(os.path.join(base, "data.csv"), index=False)

    summary_rows, grand = build_sector_summary(filtered)
    snapshot_meta = dict(meta)
    snapshot_meta.update({
        "id": snapshot_id,
        "locked": True,
        "finalised_at": now.strftime("%d/%m/%Y %H:%M:%S"),
        "from_officer": from_officer,
        "to_officer": to_officer,
        "note": (request.form.get("note") or "").strip(),
        "filters": {k: v for k, v in filters.items()},
        "filter_text": filter_label(filters),
        "cols": cols_param,
        "signature": read_signature_config(request.form),
        "watermark": read_watermark_config(request.form),
        "row_count": int(len(filtered)),
        "sector_count": len(summary_rows),
        "grand": grand,
    })
    with open(os.path.join(base, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(snapshot_meta, fh, ensure_ascii=False, indent=2)

    flash(f"Handover register finalised and locked ({len(filtered):,} connections).")
    return redirect(url_for("handover.handover_snapshot", snapshot_id=snapshot_id))


# ---------------------------------------------------------------------------
# Print / preview view
# ---------------------------------------------------------------------------

def _report_context(snapshot_id: str | None):
    df, meta = load_dataset(snapshot_id)
    if df is None:
        return None
    if snapshot_id:
        filters = meta.get("filters") or {}
        filters.setdefault("flagged_only", False)
        cols_param = meta.get("cols") or ""
        # A locked record prints the signature layout it was finalised with.
        signature = meta.get("signature") or {
            "fields": list(DEFAULT_SIGNATURE_FIELDS), "position": "last",
        }
        watermark = meta.get("watermark") or {
            "enabled": True, "text": DEFAULT_WATERMARK_TEXT,
        }
    else:
        filters = read_filters()
        cols_param = request.args.get("cols", "")
        signature = read_signature_config()
        watermark = read_watermark_config()
    filtered = apply_filters(df, filters)
    summary_rows, grand = build_sector_summary(filtered)
    # The first-page summary reports the complete imported dataset, not the
    # filtered view — a status filter would otherwise zero out the very
    # Suspended/Closed counts the summary exists to show. Domestic and
    # commercial are summarised separately so neither leaks into the other.
    commercial_mask = is_commercial(df)
    domestic_df, commercial_df = df[~commercial_mask], df[commercial_mask]
    overall = summarise_block(domestic_df)
    overall_sectors = domestic_df["Sector"].nunique()
    commercial_overall = summarise_block(commercial_df)
    commercial_localities = commercial_df["Locality"].nunique()
    columns = selected_columns(df, cols_param)
    return {
        "meta": meta,
        "overall": overall,
        "overall_sectors": overall_sectors,
        "commercial_overall": commercial_overall,
        "commercial_localities": commercial_localities,
        "frame_all": df,
        "filters": filters,
        "filter_text": meta.get("filter_text") if snapshot_id else filter_label(filters),
        "frame": filtered,
        "summary_rows": summary_rows,
        "grand": grand,
        "columns": columns,
        "signature": signature,
        "watermark": watermark,
    }


@handover_bp.route("/handover/print")
def handover_print():
    ctx = _report_context(request.args.get("snap"))
    if ctx is None:
        flash("No handover register available.")
        return redirect(url_for("handover.handover"))
    frame = ctx["frame"]
    return render_template(
        "handover_print.html",
        sections=build_sections(frame, ctx["columns"], ctx["frame_all"]),
        report_date=report_date(ctx["meta"]),
        signature=ctx["signature"],
        watermark=ctx["watermark"],
        row_count=len(frame),
        auto_print=request.args.get("auto") == "1",
    )


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

def report_date(meta: dict) -> str:
    """The one date the register carries.

    A finalised record is dated when it was locked, not when it is reprinted.
    """
    if meta.get("locked") and meta.get("finalised_at"):
        return meta["finalised_at"].split(" ")[0]
    return datetime.now().strftime("%d/%m/%Y")


@handover_bp.route("/handover/export/<fmt_type>")
def export_handover(fmt_type: str):
    _make_pdf_table = _app()._make_pdf_table

    snapshot_id = request.args.get("snap")
    ctx = _report_context(snapshot_id)
    if ctx is None:
        flash("No handover register available. Upload both files first.")
        return redirect(url_for("handover.handover"))

    part = request.args.get("part", "register")
    if part not in ("register", "summary", "detail", "exceptions"):
        part = "register"

    frame, meta = ctx["frame"], ctx["meta"]
    columns = ctx["columns"]
    summary_rows, grand = ctx["summary_rows"], ctx["grand"]
    slug = f"Consumer_List_{datetime.now().strftime('%Y%m%d_%H%M')}"
    if meta.get("locked"):
        slug = f"Consumer_List_{secure_filename(meta.get('id', 'snapshot'))}"

    if part == "exceptions":
        exc_cols = [c for c in ["Sr #", "Connection No.", "Consumer Name", "Sector",
                                "Locality", "Connection Status", "Arrears Match", "Data Flag"]
                    if c in frame.columns]
        flagged = frame[frame["Data Flag"].astype(str).str.strip() != ""]
        headers, body = exc_cols, detail_rows(flagged, exc_cols)
    elif part == "summary":
        headers = [label for _, label, _ in SUMMARY_COLUMNS]
        body = [
            [(f"{r[key]:,.0f}" if key == "arrears" else str(r[key])) for key, _, _ in SUMMARY_COLUMNS]
            for r in summary_rows
        ]
        body.append([
            "" if key == "serial" else
            (f"{grand[key]:,.0f}" if key == "arrears" else str(grand[key]))
            for key, _, _ in SUMMARY_COLUMNS
        ])
    else:
        # Same rows, order and per-sector serial as the printed register, so a
        # downloaded sheet can be ticked off line by line against the PDF.
        sections = build_sections(frame, columns, ctx["frame_all"])
        headers = [SERIAL_COLUMN] + list(columns)
        body = [row for section in sections for row in section["rows"]]

    if fmt_type == "csv":
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(headers)
        writer.writerows(body)
        return Response(
            out.getvalue(), mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={slug}_{part}.csv"},
        )

    if fmt_type == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            _numeric_amounts(pd.DataFrame(body, columns=headers)).to_excel(
                writer, sheet_name=part.title()[:31], index=False
            )
            if part == "register":
                summary_headers = [label for _, label, _ in SUMMARY_COLUMNS]
                summary_body = [
                    [r[key] for key, _, _ in SUMMARY_COLUMNS] for r in summary_rows
                ]
                pd.DataFrame(summary_body, columns=summary_headers).to_excel(
                    writer, sheet_name="Sector Summary", index=False
                )
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={slug}_{part}.xlsx"},
        )

    if fmt_type != "pdf":
        flash("Unsupported export format.")
        return redirect(url_for("handover.handover"))

    # ---- PDF: Consumer List, landscape official register --------------------
    signature = ctx["signature"]
    buf = io.BytesIO()
    page_size = landscape(A4)
    margin = 7 * mm
    # "Every page" draws the signature strip in the page furniture, so the frame
    # has to give up that height on every page or the table would run under it.
    sig_band = _signature_band_height(signature) if signature["position"] == "every" else 0
    doc = SimpleDocTemplate(
        buf, pagesize=page_size, topMargin=margin, bottomMargin=margin + 2 * mm + sig_band,
        leftMargin=margin, rightMargin=margin, title="Consumer List",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("HOTitle", parent=styles["Heading1"], fontSize=19,
                                 leading=22, alignment=1, spaceAfter=1.5 * mm,
                                 textColor=colors.black, fontName="Helvetica-Bold")
    date_style = ParagraphStyle("HODate", parent=styles["Normal"], fontSize=9,
                                alignment=1, spaceAfter=4 * mm, textColor=colors.black)
    sector_style = ParagraphStyle("HOSector", parent=styles["Normal"], fontSize=13,
                                  leading=15, alignment=1, spaceBefore=4 * mm,
                                  spaceAfter=2 * mm, textColor=colors.black,
                                  fontName="Helvetica-Bold")
    commercial_title_style = ParagraphStyle(
        "HOCommercial", parent=styles["Normal"], fontSize=17, leading=20,
        alignment=1, spaceBefore=6 * mm, spaceAfter=3 * mm,
        textColor=colors.black, fontName="Helvetica-Bold")
    note_style = ParagraphStyle("HONote", parent=styles["Normal"], fontSize=8,
                                alignment=1, spaceAfter=1 * mm, textColor=colors.black)

    elements = [
        Paragraph("Consumer List", title_style),
        Paragraph(report_date(meta), date_style),
    ]

    page_w = page_size[0] - 2 * margin

    if part == "exceptions":
        elements.append(Paragraph(f"Exception Report &mdash; {len(body):,} flagged connections", sector_style))
        if not body:
            elements.append(Paragraph("No flagged connections.", note_style))
        else:
            elements.append(_register_table(headers, body, page_w))
    else:
        sections = build_sections(frame, columns, ctx["frame_all"])
        if part in ("register", "summary"):
            # Overall totals for the complete imported dataset, on their own
            # first page; the sector blocks that follow are untouched.
            elements.extend(_summary_page(
                ctx["overall"], ctx["overall_sectors"],
                ctx["commercial_overall"], ctx["commercial_localities"], page_w))
            if sections:
                elements.append(PageBreak())
        if not sections:
            elements.append(Paragraph("No connections for the selected filters.", note_style))
        seen_commercial = False
        for section in sections:
            block = []
            if section.get("group") == "commercial" and not seen_commercial:
                # One banner introduces the whole commercial register, which
                # always sits at the end of the document.
                seen_commercial = True
                block.append(Paragraph("COMMERCIAL", commercial_title_style))
            block.append(Paragraph(_esc(section["sector"]), sector_style))
            if part in ("register", "summary") and section["summary"]:
                summary = section["summary"]
                # Each block carries its own header set: commercial blocks are
                # already type-scoped, so they report Active rather than
                # Active + Regular.
                spec = section["summary_columns"]
                block.append(_make_pdf_table(
                    [[label for _, label, _ in spec], [
                        f"{summary[key]:,.0f}" if key == "arrears" else f"{summary[key]:,}"
                        for key, _, _ in spec
                    ]],
                    col_widths=[page_w * w for _, _, w in spec], header_font_size=8,
                    body_font_size=8, cell_padding=4,
                ))
            # Heading and summary line must not be orphaned from their block.
            elements.append(KeepTogether(block))
            if part in ("register", "detail") and section["rows"]:
                elements.append(Spacer(1, 1.5 * mm))
                elements.append(_register_table(
                    section["columns"], section["rows"], page_w, banner=section["sector"]))
            elements.append(Spacer(1, 2 * mm))

    if signature["position"] == "last":
        elements.append(_signature_flowable(signature, page_w))

    page_furniture = _page_furniture(signature, ctx["watermark"])
    doc.build(elements, onFirstPage=page_furniture, onLaterPages=page_furniture,
              canvasmaker=NumberedCanvas)
    buf.seek(0)
    return Response(
        buf.getvalue(), mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={slug}_{part}.pdf"},
    )


# The summary page carries two separate reports. Commercial figures never
# appear in the domestic one and vice versa; each heading supplies the context,
# so the card labels stay short.
DOMESTIC_SUMMARY_CARDS = [
    ("Total Sectors", "sectors"),
    ("Total Entries", "total"),
    ("Active + Regular Connections", "active_regular"),
    ("Suspended Connections", "suspended"),
    ("Closed Connections", "closed"),
    ("New Demand", "new_demand"),
    ("Total Arrears (Rs.)", "arrears"),
]

COMMERCIAL_SUMMARY_CARDS = [
    ("Total Localities", "sectors"),
    ("Total Entries", "total"),
    ("Active + Regular Connections", "active"),
    ("Suspended Connections", "suspended"),
    ("Closed Connections", "closed"),
    ("New Demand", "new_demand"),
    ("Total Arrears (Rs.)", "arrears"),
]


def _summary_page(domestic: dict, domestic_sectors: int,
                  commercial: dict, commercial_localities: int, page_w: float) -> list:
    """The first page: a domestic report and a commercial report, side by side
    in sequence, with neither set of figures leaking into the other."""
    styles = getSampleStyleSheet()
    heading = ParagraphStyle("HOOverall", parent=styles["Normal"], fontSize=13,
                             leading=15, alignment=1, spaceBefore=4 * mm,
                             spaceAfter=3 * mm, fontName="Helvetica-Bold",
                             textColor=colors.black)
    card = ParagraphStyle("HOCard", parent=styles["Normal"], alignment=1,
                          leading=22, textColor=colors.black)

    def grid_for(summary, spec, count):
        values = dict(summary)
        values["sectors"] = count
        cells = [
            Paragraph(
                f'<font size="8.5">{label.upper()}</font><br/>'
                f'<font size="19"><b>{values.get(key, 0):,.0f}</b></font>', card)
            for label, key in spec
        ]
        rows, spans = [], []
        for start in range(0, len(cells), 3):
            chunk = cells[start:start + 3]
            row = len(rows)
            if len(chunk) < 3:
                # Span only the cells the row is short of, never a sibling card.
                spans.append(("SPAN", (len(chunk) - 1, row), (2, row)))
                chunk = chunk + [""] * (3 - len(chunk))
            rows.append(chunk)
        col_w = page_w / 3
        table = Table(rows, colWidths=[col_w] * 3, rowHeights=[22 * mm] * len(rows))
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.0, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.8, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            # Deliberately unfilled: a solid card background would mask the top
            # half of the watermark and leave it looking sliced off.
        ] + spans))
        return table

    return [
        Paragraph("Domestic Connections", heading),
        grid_for(domestic, DOMESTIC_SUMMARY_CARDS, domestic_sectors),
        Paragraph("Commercial Connections", heading),
        grid_for(commercial, COMMERCIAL_SUMMARY_CARDS, commercial_localities),
    ]


# Body type size for the register. Small enough to fit a landscape sheet
# densely, large enough to stay readable in print.
REGISTER_FONT_SIZE = 7.0


def _register_table(headers, rows, page_w, banner=None, font_size=None):
    """A detail table for the printed register.

    Two corrections on top of the shared table builder, applied without
    touching it because every other report depends on its current behaviour:
      * headers are wrapped, so "Connection Status" cannot spill into the next
        column at register font sizes;
      * the last row is un-bolded — the helper styles it as a grand total, but
        here the final row is just the last consumer on the list.
    """
    font_size = REGISTER_FONT_SIZE if font_size is None else font_size
    main = _app()
    extents = _column_extents(headers, rows)
    widths = _detail_widths(headers, page_w, extents)
    # A plain string is drawn without wrapping or clipping, so it silently
    # overprints its neighbour when it is wider than its cell. Measure the
    # widest value against the width the column actually got, and turn exactly
    # those columns into Paragraphs — no more, which keeps a 10k-row build fast.
    wrap_idx = {
        i for i, h in enumerate(headers)
        if _txt(h) in WRAP_COLUMNS
        or stringWidth(extents[i], "Helvetica", font_size) > widths[i] - 4
    }
    # Names, sector and address read as text and are set left; numbers, dates,
    # statuses and references stay centred.
    left_idx = {i for i, h in enumerate(headers) if _txt(h) in LEFT_COLUMNS} | wrap_idx
    header_row = main.wrap_pdf_header_cells([_esc(h) for h in headers], font_size=font_size + 0.5)
    data = [header_row] + _wrap_rows(rows, wrap_idx, font_size=font_size)
    span_rows = None
    offset = 0
    if banner:
        # A sector's rows can run over several pages. Carrying the sector name
        # in a repeated banner row keeps every continuation page identified
        # without repeating the name on all 9,648 rows.
        styles = getSampleStyleSheet()
        banner_style = ParagraphStyle(
            "HOBanner", parent=styles["Normal"], fontName="Helvetica-Bold",
            fontSize=font_size + 1.5, leading=font_size + 3.5, alignment=0,
        )
        data = [[Paragraph(_esc(banner), banner_style)] + [""] * (len(headers) - 1)] + data
        span_rows = [0]
        offset = 1

    table = main._make_pdf_table(
        data, col_widths=widths, left_cols=left_idx, span_rows=span_rows,
        header_font_size=font_size + 0.5, body_font_size=font_size, cell_padding=2,
    )
    if banner:
        table.repeatRows = 2       # banner + column headers on every page

    # The shared builder sets FONTSIZE but not LEADING, so plain string cells
    # keep reportlab's 12pt default and every row is ~15pt tall no matter how
    # small the type is. Setting leading explicitly is what actually makes the
    # register dense.
    extra = [("LEADING", (0, offset + 1), (-1, -1), font_size + 1.5)]
    if banner:
        # The shared builder paints row 0 as the header; the banner now sits
        # there, so the real column-header row needs the dark fill applied to
        # it — its text is white and would otherwise be invisible.
        extra += [
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#222222")),
            ("LEADING", (0, 1), (-1, 1), font_size + 2),
        ]
    last = len(rows) + offset
    if len(rows) > 1:
        extra += [
            ("FONTNAME", (0, last), (-1, last), "Helvetica"),
            ("BACKGROUND", (0, last), (-1, last),
             colors.HexColor("#f2f2f2") if (last - offset) % 2 == 0 else colors.white),
        ]
    table.setStyle(TableStyle(extra))
    return table


def _numeric_amounts(frame: pd.DataFrame) -> pd.DataFrame:
    """Write money columns to Excel as numbers, not "13,040" text, so the
    arrears column can actually be summed in the spreadsheet."""
    for column in frame.columns:
        if "arrears" in _txt(column):
            frame[column] = frame[column].map(_to_amount)
    return frame


def _wrap_rows(rows, wrap_idx, font_size=7):
    """Wrap only the long-text columns as Paragraphs.

    Matches what ``wrap_pdf_body_cells`` produces for a left-aligned cell, but
    builds the style once instead of per cell — a full register is ~50k wrapped
    cells and the shared helper rebuilds the sample stylesheet on every call.
    """
    if not wrap_idx:
        return rows
    style = ParagraphStyle(
        "HODetailCell", parent=getSampleStyleSheet()["Normal"],
        fontName="Helvetica", fontSize=font_size, leading=font_size + 0.6,
        alignment=0, wordWrap="CJK",
    )
    return [
        [Paragraph(_esc(value).replace("\n", "<br/>"), style) if i in wrap_idx else value
         for i, value in enumerate(row)]
        for row in rows
    ]


def _column_extents(headers, rows) -> list[str]:
    """Longest value per column, used to size the columns and decide wrapping."""
    longest = [""] * len(headers)
    for row in rows:
        for i, value in enumerate(row):
            text = str(value)
            if len(text) > len(longest[i]):
                longest[i] = text
    return longest


def _detail_widths(headers, page_w, extents=None):
    """Share the page across columns according to what they actually hold.

    Sizing off the real content rather than a fixed list of column names is
    what keeps a 20-column selection legible: every column still gets at least
    its longest header word, and no single free-text column can starve the rest.
    """
    weights = []
    for i, header in enumerate(headers):
        # Headers are bold and a size larger than the body, so a header word
        # needs more room per character than a body character — without the
        # allowance, "Total Arrears" breaks mid-word into "Total Arre / ars".
        header_floor = max((len(word) for word in str(header).split()), default=4) * 1.45
        content = len(extents[i]) if extents else 0
        weights.append(max(4.0, header_floor, min(float(content), 26.0)))
    total = sum(weights) or 1
    return [page_w * w / total for w in weights]


# Height reserved for a signature block: room to actually sign and stamp,
# plus the rule and its label.
SIGNATURE_SPACE = 20 * mm
SIGNATURE_LABEL_SPACE = 6 * mm


def _signature_band_height(signature: dict) -> float:
    if signature["position"] == "none" or not signature["fields"]:
        return 0
    return SIGNATURE_SPACE + SIGNATURE_LABEL_SPACE


def _signature_flowable(signature: dict, page_w: float):
    """Signature strip as a flowable, for placement after the last block."""
    fields = signature["fields"]
    if signature["position"] == "none" or not fields:
        return Spacer(0, 0)
    styles = getSampleStyleSheet()
    label_style = ParagraphStyle("HOSigLabel", parent=styles["Normal"], fontSize=8.5,
                                 leading=10, alignment=1, textColor=colors.black,
                                 fontName="Helvetica-Bold")
    col_w = page_w / len(fields)
    table = Table(
        [[""] * len(fields), [Paragraph(_esc(f), label_style) for f in fields]],
        colWidths=[col_w] * len(fields),
        rowHeights=[SIGNATURE_SPACE, SIGNATURE_LABEL_SPACE],
    )
    style = [
        ("VALIGN", (0, 1), (-1, 1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    # A rule under the blank cell of each column — the line people sign on.
    for col in range(len(fields)):
        style.append(("LINEABOVE", (col, 1), (col, 1), 0.8, colors.black))
    table.setStyle(TableStyle(style))
    return KeepTogether([Spacer(1, 4 * mm), table])


def _draw_signature_band(canvas, doc, signature: dict):
    """Signature strip drawn as page furniture, for 'every page'."""
    fields = signature["fields"]
    if not fields:
        return
    page_w, margin = doc.pagesize[0], 7 * mm
    usable = page_w - 2 * margin
    col_w = usable / len(fields)
    baseline = 9 * mm + SIGNATURE_LABEL_SPACE
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(0.8)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(colors.black)
    for index, field in enumerate(fields):
        left = margin + index * col_w
        canvas.line(left + 6, baseline, left + col_w - 6, baseline)
        # drawCentredString cannot wrap, so shrink (then clip) a long custom
        # label rather than let it run into the neighbouring signature column.
        size, text = 8.5, field
        while size > 5.5 and canvas.stringWidth(text, "Helvetica-Bold", size) > col_w - 14:
            size -= 0.5
        if canvas.stringWidth(text, "Helvetica-Bold", size) > col_w - 14:
            # Three dots, not U+2026 — the standard Helvetica encoding
            # ReportLab uses here has no glyph for the ellipsis character.
            while len(text) > 4 and canvas.stringWidth(text + "...", "Helvetica-Bold", size) > col_w - 14:
                text = text[:-1]
            text = text.rstrip() + "..."
        canvas.setFont("Helvetica-Bold", size)
        canvas.drawCentredString(left + col_w / 2, baseline - 4 * mm, text)
    canvas.restoreState()


class NumberedCanvas(canvas.Canvas):
    """Canvas that stamps "Page X of Y" once the total is known.

    ReportLab streams pages out as it lays them out, so at draw time it cannot
    know how many there will be. This holds each finished page in memory and
    writes the footer on all of them at save(), which is what makes the total
    track the real page count automatically.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._held_pages = []

    def showPage(self):
        self._held_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._held_pages)
        for state in self._held_pages:
            self.__dict__.update(state)
            self._draw_page_number(total)
            super().showPage()
        super().save()

    def _draw_page_number(self, total):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#444444"))
        # Centred in the bottom margin: below the frame, and below the
        # repeated signature strip, so it can never overlap either.
        self.drawCentredString(self._pagesize[0] / 2.0, 3.2 * mm, f"Page {self._pageNumber} of {total}")
        self.restoreState()


# ---------------------------------------------------------------------------
# Circular stamp watermark
# ---------------------------------------------------------------------------

EMBLEM_FILENAME = "emblem.jpg"
WATERMARK_COLOR = colors.HexColor("#16324f")
# Rings are thin lines and can carry a little more ink than the solid stars and
# the lettering, which are what would otherwise show through the table text.
WATERMARK_ALPHA = 0.10
WATERMARK_FILL_ALPHA = 0.06


def _emblem_path():
    """The municipal emblem shipped in static/, or None if it is absent."""
    try:
        path = _app().resource_path("static", EMBLEM_FILENAME)
    except Exception:
        return None
    return path if os.path.exists(path) else None


def _draw_ring_text(canvas_obj, cx, cy, radius, text, size, separator="  ★  "):
    """Set text right around the circle, evenly spaced with no gap.

    The legend is repeated as many times as fits at roughly the requested size,
    then the size is trimmed so the repetitions close the ring exactly — which
    is what makes the spacing even all the way round instead of leaving a bald
    patch at the bottom.
    """
    font = "Helvetica-Bold"
    unit = text + separator
    circumference = 2 * math.pi * radius
    unit_width = canvas_obj.stringWidth(unit, font, size)
    if unit_width <= 0:
        return
    repeats = max(1, round(circumference / unit_width))
    full = unit * repeats
    size *= circumference / canvas_obj.stringWidth(full, font, size)
    canvas_obj.setFont(font, size)

    angle = math.pi / 2                       # start at the top
    for char in full:
        step = canvas_obj.stringWidth(char, font, size) / radius
        theta = angle - step / 2
        canvas_obj.saveState()
        canvas_obj.translate(cx + radius * math.cos(theta), cy + radius * math.sin(theta))
        canvas_obj.rotate(math.degrees(theta) - 90)
        canvas_obj.drawCentredString(0, 0, char)
        canvas_obj.restoreState()
        angle -= step


def _draw_star(canvas_obj, cx, cy, outer, points=5):
    path = canvas_obj.beginPath()
    for i in range(points * 2):
        r = outer if i % 2 == 0 else outer * 0.42
        theta = math.pi / 2 + i * math.pi / points
        x, y = cx + r * math.cos(theta), cy + r * math.sin(theta)
        path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
    path.close()
    canvas_obj.drawPath(path, stroke=0, fill=1)


def _draw_watermark(canvas_obj, doc, watermark: dict):
    """A round official stamp, faint, centred, behind the page content."""
    text = (watermark or {}).get("text", "")
    if not (watermark or {}).get("enabled") or not text:
        return
    page_w, page_h = doc.pagesize
    cx, cy = page_w / 2, page_h / 2
    radius = min(page_w, page_h) * 0.25
    inner = radius - 18 * mm          # leaves a wide band for the legend
    arc_radius = radius - 12 * mm     # legend baseline, centred in that band

    canvas_obj.saveState()
    # Alpha must be passed WITH the colour: setFillColor/setStrokeColor reset
    # alpha to the colour object's own (opaque) value, so setting the alpha
    # first and the colour after silently produces a solid black stamp.
    canvas_obj.setStrokeColor(WATERMARK_COLOR, alpha=WATERMARK_ALPHA)
    canvas_obj.setFillColor(WATERMARK_COLOR, alpha=WATERMARK_FILL_ALPHA)

    canvas_obj.setLineWidth(3.0)
    canvas_obj.circle(cx, cy, radius)
    canvas_obj.setLineWidth(1.0)
    canvas_obj.circle(cx, cy, radius - 3 * mm)
    canvas_obj.setLineWidth(1.2)
    canvas_obj.circle(cx, cy, inner)

    # Legend right around the ring, evenly spaced.
    _draw_ring_text(canvas_obj, cx, cy, arc_radius, text.upper(), 12.0)

    # Municipal emblem in the middle, falling back to a star if the asset is
    # missing. Its white background is harmless at watermark opacity — white
    # over white paper stays white — so it needs no alpha channel.
    emblem = _emblem_path()
    if emblem:
        side = inner * 1.5
        canvas_obj.setFillAlpha(WATERMARK_FILL_ALPHA * 2)
        canvas_obj.drawImage(emblem, cx - side / 2, cy - side / 2, width=side, height=side,
                             mask="auto", preserveAspectRatio=True, anchor="c")
    else:
        _draw_star(canvas_obj, cx, cy, 11 * mm)
    canvas_obj.restoreState()


def _page_furniture(signature: dict, watermark: dict):
    """Page-begin callback.

    Runs before the frame lays its flowables down, which is what puts the
    watermark *behind* the tables rather than over them.
    """
    def draw(canvas_obj, doc):
        _draw_watermark(canvas_obj, doc, watermark)
        if signature["position"] == "every":
            _draw_signature_band(canvas_obj, doc, signature)

    return draw
