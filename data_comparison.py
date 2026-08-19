"""Data Comparison — one page, one question.

Replaces the File Comparison, Data Integrity Check and Data Audit pages with a
single page that answers:

    How many connections were Active in the older export, how many are Active
    in the newer one, and exactly which connections were activated or closed?

Nothing else is compared. Spelling, spacing, column order, and every record
whose status did not move are ignored on purpose: an earlier version of this
page reported twelve thousand differences, of which two mattered.

Classification is imported from the Handover Register rather than restated
here — what counts as Active, what counts as Commercial, how a Connection
Number is normalised. A second copy is a second interpretation waiting to
drift, and the Consumer List and this page must never disagree about how many
connections are live.

Neither uploaded file is modified. Values are normalised for comparison only;
what is stored and displayed is what the file said.
"""

import csv
import gzip
import io
import json
import os
import sys
from datetime import datetime

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
from werkzeug.utils import secure_filename

# The Handover Register's own definitions. Imported, never restated.
from handover import (  # noqa: E402
    _conn_key,
    _pick,
    _status_of,
    _txt,
    _type_of,
    canonicalise_groups,
    drop_excluded_sectors,
    is_commercial,
)

data_comparison_bp = Blueprint("data_comparison", __name__)

RESULT_VERSION = 1

# Shown in place of a status when a connection is in one file but not the other.
MISSING_NEW = "Not in the new file"
MISSING_OLD = "Not in the older file"

# The four movements the page exists to report, in the order they are listed.
# Anything else that crosses into or out of Active lands in "other" — it still
# changes the Active count, so it can be reported but never silently dropped.
TRANSITIONS = [
    ("closed", "Active → Closed", ("Active", "Closed")),
    ("activated", "Closed → Active", ("Closed", "Active")),
    ("suspended", "Active → Suspended", ("Active", "Suspended")),
    ("resumed", "Suspended → Active", ("Suspended", "Active")),
]
TRANSITION_OF = {pair: key for key, _, pair in TRANSITIONS}
OTHER = "other"
KIND_ORDER = [key for key, _, _ in TRANSITIONS] + [OTHER]
KIND_LABEL = dict([(key, label) for key, label, _ in TRANSITIONS] +
                  [(OTHER, "Other movement in or out of Active")])

HEADERS = ["Connection No.", "Consumer Name", "Father Name",
           "Sector", "Locality", "Old Status", "New Status"]
FIELDS = ["conn", "name", "father", "sector", "locality", "old", "new"]

# A paginated export that returns the same page twice produces a file of the
# right length whose connections are mostly repeats. Below this share of
# distinct connection numbers the file is reported as incomplete rather than
# read as thousands of deleted records.
UNIQUE_RATIO_FLOOR = 0.95
HEALTH_MIN_ROWS = 100

PREVIEW_LIMIT = 500
PDF_ROW_CAP = 400


# ---------------------------------------------------------------------------
# Storage — the working copies live on disk, not in the session
# ---------------------------------------------------------------------------

def _app():
    """The already-loaded app module (it is ``__main__`` when run directly)."""
    main = sys.modules.get("__main__")
    if hasattr(main, "UPLOAD_FOLDER"):
        return main
    import app

    return app


def _dir() -> str:
    path = os.path.join(_app().UPLOAD_FOLDER, "data_comparison")
    os.makedirs(path, exist_ok=True)
    return path


def _result_path() -> str:
    return os.path.join(_dir(), "result.json")


def save_result(result) -> None:
    with open(_result_path(), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False)


def load_result():
    path = _result_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            result = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    # A result written by an older version is discarded rather than half-read.
    return result if result.get("version") == RESULT_VERSION else None


def clear_result() -> None:
    path = _result_path()
    if os.path.exists(path):
        os.remove(path)


def read_upload(filename: str, blob: bytes):
    """Read an uploaded CSV/XLSX, transparently un-gzipping it.

    The browser compresses before posting because two complete exports run to
    ~12 MB together and a serverless request body caps at 4.5 MB.
    """
    if blob[:2] == b"\x1f\x8b":
        blob = gzip.decompress(blob)
        if filename.lower().endswith(".gz"):
            filename = filename[:-3]
    _, ext = os.path.splitext(filename)
    if ext.lower() == ".csv":
        # utf-8-sig strips the byte-order mark some exports carry, which would
        # otherwise make the first column look renamed.
        return filename, pd.read_csv(io.BytesIO(blob), dtype=str,
                                     keep_default_na=False, encoding="utf-8-sig")
    return filename, pd.read_excel(io.BytesIO(blob), dtype=str).fillna("")


# ---------------------------------------------------------------------------
# Reading a Consumer List export
# ---------------------------------------------------------------------------

def _norm(value) -> str:
    """Collapse whitespace but keep case — for display and equality."""
    return " ".join(str(value or "").split()).strip()


def _column(df: pd.DataFrame, name):
    return df[name].map(_norm) if name else pd.Series([""] * len(df), index=df.index)


def classify(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Reduce an export to the fields this page compares.

    Column names are located with the Handover Register's own ``_pick``, so a
    file that spells a heading differently is still read rather than rejected.
    Excluded sectors are dropped and Sector/Locality spellings collapsed
    exactly as the register does, so the counts on the two pages match.
    """
    cols = list(df.columns)
    conn_col = _pick(cols, "connection no", "connection number")
    if not conn_col:
        raise ValueError('No "Connection No." column found in this file.')
    status_col = _pick(cols, "status")
    if not status_col:
        raise ValueError('No "Status" column found in this file.')
    rate_col = _pick(cols, "rate type")

    frame = pd.DataFrame({
        "conn": _column(df, conn_col),
        "key": df[conn_col].map(_conn_key),
        "name": _column(df, _pick(cols, "consumer name", "name")),
        "father": _column(df, _pick(cols, "f/h name", "father name", "father")),
        "Sector": _column(df, _pick(cols, "sector")),
        "Locality": _column(df, _pick(cols, "locality")),
        "status": df[status_col].map(_status_of),
        "type": df[rate_col].map(_type_of) if rate_col else "Regular",
    })
    frame, excluded = drop_excluded_sectors(frame)
    return canonicalise_groups(frame.reset_index(drop=True)), excluded


def first_positions(frame: pd.DataFrame) -> dict:
    """First row position per connection number.

    A connection repeated in a file is one connection, counted once. Every
    repeat is reported in the file-health figures rather than counted again.
    """
    seen = {}
    for position, key in enumerate(frame["key"]):
        if key and key not in seen:
            seen[key] = position
    return seen


def summarise(frame: pd.DataFrame, positions: dict, rows: int, excluded: int) -> dict:
    """The four figures for one file, counted once per connection number.

    ``Domestic Active + Regular`` and ``Commercial Active`` are the register's
    two headline counts: Commercial is decided by SECTOR, and a commercial rate
    type in an ordinary sector keeps a record out of the domestic figure
    without moving it into the commercial one. Those records are counted here
    too, and reported, so the three figures are never silently short.
    """
    one_each = frame.iloc[sorted(positions.values())] if positions else frame.iloc[0:0]
    status, ctype = one_each["status"], one_each["type"]
    commercial = is_commercial(one_each)
    active = status == "Active"
    domestic_regular = int((active & ~commercial & (ctype == "Regular")).sum())
    commercial_active = int((active & commercial).sum())
    total_active = int(active.sum())
    return {
        "rows": rows,
        "excluded": excluded,
        "entries": int(len(frame)),
        "connections": int(len(one_each)),
        "domestic_active_regular": domestic_regular,
        "commercial_active": commercial_active,
        "total_active": total_active,
        # Active, in an ordinary sector, on a commercial rate: in neither of
        # the two lines above. Stated rather than left as a silent shortfall.
        "domestic_commercial_rate": total_active - domestic_regular - commercial_active,
        "suspended": int((status == "Suspended").sum()),
        "closed": int((status == "Closed").sum()),
        "new_demand": int((status == "New Demand").sum()),
    }


def health(frame: pd.DataFrame, positions: dict) -> dict:
    """Whether a file looks like a complete export.

    An export that repeats a page has the right number of rows and the wrong
    number of connections. Saying so is the difference between "the export is
    broken" and "fifteen thousand connections were deleted".
    """
    rows = int(len(frame))
    distinct = len(positions)
    ratio = (distinct / rows) if rows else 1.0
    return {
        "rows": rows,
        "distinct": distinct,
        "duplicate_rows": rows - distinct,
        "unique_ratio": round(ratio, 4),
        "incomplete": rows >= HEALTH_MIN_ROWS and ratio < UNIQUE_RATIO_FLOOR,
    }


# ---------------------------------------------------------------------------
# The comparison itself
# ---------------------------------------------------------------------------

def _identity(frame: pd.DataFrame, position: int) -> dict:
    row = frame.iloc[position]
    return {
        "conn": row["conn"],
        "name": row["name"],
        "father": row["father"],
        "sector": row["Sector"],
        "locality": row["Locality"],
    }


def build_comparison(old_df: pd.DataFrame, new_df: pd.DataFrame,
                     old_name: str, new_name: str) -> dict:
    """Only the connections whose status moved into or out of Active.

    A connection Active in both files, or inactive in both, is never recorded —
    however differently its name, sector or spacing happen to be written.
    """
    old, old_excluded = classify(old_df)
    new, new_excluded = classify(new_df)
    old_at, new_at = first_positions(old), first_positions(new)

    changes = []
    for key, position in old_at.items():
        before = old["status"].iat[position]
        landing = new_at.get(key)
        after = new["status"].iat[landing] if landing is not None else MISSING_NEW
        if (before == "Active") == (after == "Active"):
            continue  # nothing crossed the Active line
        # Identity comes from the newer file when it has the connection, so the
        # report shows the current name and sector rather than a stale one.
        identity = _identity(new, landing) if landing is not None else _identity(old, position)
        changes.append({**identity, "key": key, "old": before, "new": after,
                        "kind": TRANSITION_OF.get((before, after), OTHER)})

    for key, position in new_at.items():
        if key in old_at:
            continue
        after = new["status"].iat[position]
        if after != "Active":
            continue  # a new connection that is not Active changes no count
        changes.append({**_identity(new, position), "key": key,
                        "old": MISSING_OLD, "new": after, "kind": OTHER})

    changes.sort(key=lambda c: (KIND_ORDER.index(c["kind"]), c["conn"]))

    old_summary = summarise(old, old_at, len(old_df), old_excluded)
    new_summary = summarise(new, new_at, len(new_df), new_excluded)
    lost = sum(1 for c in changes if c["old"] == "Active")
    gained = sum(1 for c in changes if c["new"] == "Active")

    counts = {key: sum(1 for c in changes if c["kind"] == key) for key in KIND_ORDER}
    counts["all"] = len(changes)

    return {
        "version": RESULT_VERSION,
        "built_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "files": {"old": {"name": old_name}, "new": {"name": new_name}},
        "summary": {"old": old_summary, "new": new_summary},
        "health": {"old": health(old, old_at), "new": health(new, new_at)},
        "difference": new_summary["total_active"] - old_summary["total_active"],
        "lost": lost,
        "gained": gained,
        "counts": counts,
        "changes": changes,
        "sectors": sorted({c["sector"] for c in changes if c["sector"]}),
        "localities": sorted({c["locality"] for c in changes if c["locality"]}),
    }


def change_rows(result, kind="all", sector="", locality="", search="", limit=None):
    """The change table, filtered. Filters compose."""
    rows = result["changes"]
    if kind and kind != "all":
        rows = [r for r in rows if r["kind"] == kind]
    if sector:
        rows = [r for r in rows if r["sector"] == sector]
    if locality:
        rows = [r for r in rows if r["locality"] == locality]
    if search:
        needle = _txt(search)
        rows = [r for r in rows
                if any(needle in _txt(r[f]) for f in FIELDS)]
    total = len(rows)
    if limit:
        rows = rows[:limit]
    return HEADERS, [[r[f] for f in FIELDS] for r in rows], total


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def _handle_upload():
    main = _app()
    old_file = request.files.get("old_file")
    new_file = request.files.get("new_file")
    for label, upload in (("older", old_file), ("new", new_file)):
        if not upload or not upload.filename:
            message = f"Please choose the {label} file."
            return main.ajax_error(message) if main.is_ajax() else (
                flash(message) or redirect(url_for("data_comparison.data_comparison")))
        base = upload.filename[:-3] if upload.filename.lower().endswith(".gz") else upload.filename
        if not main.allowed_file(base):
            message = f"Unsupported file type: {upload.filename}"
            return main.ajax_error(message) if main.is_ajax() else (
                flash(message) or redirect(url_for("data_comparison.data_comparison")))
    try:
        old_name, old_df = read_upload(old_file.filename, old_file.read())
        new_name, new_df = read_upload(new_file.filename, new_file.read())
        result = build_comparison(old_df, new_df,
                                  secure_filename(old_name), secure_filename(new_name))
        save_result(result)
    except Exception as exc:  # noqa: BLE001 — surfaced to the user
        message = f"Could not compare the files: {exc}"
        return main.ajax_error(message) if main.is_ajax() else (
            flash(message) or redirect(url_for("data_comparison.data_comparison")))

    message = (
        f"Compared. {result['summary']['old']['total_active']:,} Active before, "
        f"{result['summary']['new']['total_active']:,} after, "
        f"{result['counts']['all']:,} connection(s) changed."
    )
    if main.is_ajax():
        return main.ajax_ok(message=message,
                            redirect_url=url_for("data_comparison.data_comparison"))
    flash(message)
    return redirect(url_for("data_comparison.data_comparison"))


@data_comparison_bp.route("/data-comparison", methods=["GET", "POST"])
def data_comparison():
    if request.method == "POST":
        if request.form.get("action") == "clear":
            clear_result()
            main = _app()
            message = "Comparison cleared."
            if main.is_ajax():
                return main.ajax_ok(message=message,
                                    redirect_url=url_for("data_comparison.data_comparison"))
            flash(message, "success")
            return redirect(url_for("data_comparison.data_comparison"))
        return _handle_upload()

    result = load_result()
    if not result:
        return render_template("data_comparison.html", result=None)

    kind = request.args.get("kind", "all").strip()
    sector = request.args.get("sector", "").strip()
    locality = request.args.get("locality", "").strip()
    search = request.args.get("q", "").strip()
    headers, rows, total = change_rows(result, kind, sector, locality, search, PREVIEW_LIMIT)

    return render_template(
        "data_comparison.html",
        result=result,
        summary=result["summary"],
        kinds=[("all", "All changes")] + [(k, label) for k, label, _ in TRANSITIONS] +
              ([(OTHER, KIND_LABEL[OTHER])] if result["counts"][OTHER] else []),
        kind=kind, sector=sector, locality=locality, search=search,
        headers=headers, rows=rows, total=total, shown=len(rows),
        active_page="data_comparison",
    )


@data_comparison_bp.route("/data-comparison/export/<fmt>")
def export_data_comparison(fmt: str):
    result = load_result()
    if not result:
        flash("Upload both files first.")
        return redirect(url_for("data_comparison.data_comparison"))

    kind = request.args.get("kind", "all").strip()
    headers, rows, _ = change_rows(result, kind,
                                   request.args.get("sector", "").strip(),
                                   request.args.get("locality", "").strip(),
                                   request.args.get("q", "").strip())
    slug = f"Data_Comparison_{datetime.now().strftime('%Y%m%d_%H%M')}"

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        old, new = result["summary"]["old"], result["summary"]["new"]
        writer.writerow(["Figure", "Older File", "New File"])
        for label, key in SUMMARY_LINES:
            writer.writerow([label, old[key], new[key]])
        writer.writerow([])
        writer.writerow(headers)
        writer.writerows(rows)
        return Response(buf.getvalue(), mimetype="text/csv", headers={
            "Content-Disposition": f"attachment; filename={slug}.csv"})

    return _report_pdf(result, kind, headers, rows, slug)


SUMMARY_LINES = [
    ("Total Entries", "entries"),
    ("Domestic Active + Regular Connections", "domestic_active_regular"),
    ("Commercial Active Connections", "commercial_active"),
    ("Total Active Connections", "total_active"),
]


def _report_pdf(result, kind, headers, rows, slug):
    """The summary, then only the connections whose status changed."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, TableStyle

    main = _app()
    buf = io.BytesIO()
    page_size = landscape(A4)
    margin = 10 * mm
    doc = SimpleDocTemplate(buf, pagesize=page_size, topMargin=margin, bottomMargin=margin,
                            leftMargin=margin, rightMargin=margin, title="Data Comparison")
    styles = getSampleStyleSheet()
    title = ParagraphStyle("DCTitle", parent=styles["Heading1"], fontSize=17, alignment=1,
                           spaceAfter=1.5 * mm, textColor=colors.black, fontName="Helvetica-Bold")
    sub = ParagraphStyle("DCSub", parent=styles["Normal"], fontSize=8.5, alignment=1,
                         spaceAfter=1 * mm, textColor=colors.black)
    head = ParagraphStyle("DCHead", parent=styles["Normal"], fontSize=11, spaceBefore=4 * mm,
                          spaceAfter=2 * mm, fontName="Helvetica-Bold", textColor=colors.black)
    verdict = ParagraphStyle("DCVerdict", parent=styles["Normal"], fontSize=12, alignment=1,
                             spaceBefore=6 * mm, fontName="Helvetica-Bold", textColor=colors.black)

    files = result["files"]
    old, new = result["summary"]["old"], result["summary"]["new"]
    page_w = page_size[0] - 2 * margin
    elements = [
        Paragraph("Data Comparison", title),
        Paragraph(f"Generated {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub),
        Paragraph(f"Older: {files['old']['name']} &nbsp;&bull;&nbsp; "
                  f"New: {files['new']['name']} &nbsp;&bull;&nbsp; matched on Connection No.", sub),
        Spacer(1, 2 * mm),
    ]

    incomplete = [side for side in ("old", "new") if result["health"][side]["incomplete"]]
    if incomplete:
        detail = result["health"][incomplete[0]]
        which = "new" if incomplete[0] == "new" else "older"
        elements.append(Paragraph(
            f"<b>Warning: the {which} file looks incomplete.</b> It has {detail['rows']:,} rows "
            f"but only {detail['distinct']:,} distinct connection numbers. Connections reported "
            "as missing are missing from that file, which is not the same as having been removed "
            "from the system. Re-export before treating these figures as real.", sub))
        elements.append(Spacer(1, 2 * mm))

    summary_table = [["Figure", "Older File", "New File", "Change"]]
    for label, key in SUMMARY_LINES:
        delta = new[key] - old[key]
        summary_table.append([label, f"{old[key]:,}", f"{new[key]:,}",
                              f"{delta:+,}" if delta else "0"])
    elements.append(main._make_pdf_table(
        summary_table, col_widths=[page_w * w for w in (0.40, 0.20, 0.20, 0.20)],
        left_cols=[0], header_font_size=9, body_font_size=10, cell_padding=5))

    if not rows:
        elements.append(Paragraph("No change found in Active Connections.", verdict))
        doc.build(elements)
        buf.seek(0)
        return Response(buf.getvalue(), mimetype="application/pdf", headers={
            "Content-Disposition": f"inline; filename={slug}.pdf"})

    elements.append(Paragraph(
        f"{result['lost']:,} connection(s) are no longer Active and {result['gained']:,} became "
        "Active. The two move independently, so a count alone cannot show this and every "
        "connection was matched individually.", sub))
    # Helvetica's WinAnsi encoding has no arrow glyph, so the printed label
    # spells the movement out rather than dropping a black box into the heading.
    label = ("All changes" if kind in ("", "all")
             else KIND_LABEL.get(kind, "Changes").replace("→", "to"))
    elements.append(Paragraph(f"{label} — {len(rows):,} connection(s)", head))

    cell = ParagraphStyle("DCCell", parent=styles["Normal"], fontSize=7, leading=8)
    wrap_idx = {1, 2, 3, 4}
    shown = rows[:PDF_ROW_CAP]
    body = [[Paragraph(str(value).replace("&", "&amp;").replace("<", "&lt;"), cell)
             if i in wrap_idx else str(value)
             for i, value in enumerate(row)] for row in shown]
    widths = [page_w * w for w in (0.12, 0.19, 0.19, 0.16, 0.16, 0.09, 0.09)]
    table = main._make_pdf_table([headers] + body, col_widths=widths, left_cols=wrap_idx,
                                 header_font_size=8, body_font_size=7, cell_padding=2)
    # FONTSIZE alone leaves the rows on reportlab's 12pt default leading, which
    # is what makes a short report run to three times the pages it needs.
    table.setStyle(TableStyle([("LEADING", (0, 1), (-1, -1), 8)]))
    elements.append(table)
    if len(rows) > PDF_ROW_CAP:
        elements.append(Paragraph(
            f"Listing the first {PDF_ROW_CAP:,} of {len(rows):,} changed connections to keep this "
            "report short; the CSV export carries every one.", sub))

    doc.build(elements)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="application/pdf", headers={
        "Content-Disposition": f"inline; filename={slug}.pdf"})
