"""File Comparison and Data Integrity Check — independent feature module.

Two read-only audit pages that compare an older Consumer List export against a
newer one, matching records on Connection Number:

* ``/file-comparison``  — structural diff: rows and columns added or removed,
  duplicate connection numbers, and the full record behind every difference.
* ``/data-integrity``   — field-by-field audit centred on connection status
  changes, with old and new values for everything that moved.

Neither page writes to, merges or alters an uploaded file. Values are
normalised (whitespace collapsed) only in order to compare them; the stored
copies keep whatever the source contained, and every figure shown is derived
from those stored copies.
"""

import csv
import gzip
import io
import json
import os
import re
import sys
from datetime import datetime

import pandas as pd
from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

compare_bp = Blueprint("compare", __name__)

# Status values are read the same way the Consumer List reads them, so the two
# features can never disagree about what "Active" means.
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
STATUS_ORDER = ["Active", "Suspended", "Closed", "New Demand", "Dead", "Other"]

# A live connection going dark, or a connection's identity/location moving.
SUSPICIOUS_TRANSITIONS = {
    ("Active", "Closed"), ("Active", "Suspended"), ("Active", "Dead"),
}
IDENTITY_FIELDS = {"consumer name", "f/h name", "sector", "locality", "connection no."}

KEY_COLUMN = "Connection No."

# Bumped whenever the stored result's shape changes. A result written by an
# older build is discarded rather than half-read, which would otherwise fail
# with a template error instead of simply asking for the files again.
RESULT_VERSION = 2


def _app():
    """The already-loaded app module (it is ``__main__`` when run directly)."""
    main = sys.modules.get("__main__")
    if hasattr(main, "UPLOAD_FOLDER"):
        return main
    import app

    return app


def _dir() -> str:
    path = os.path.join(_app().UPLOAD_FOLDER, "compare")
    os.makedirs(path, exist_ok=True)
    return path


def _paths():
    base = _dir()
    return (os.path.join(base, "old.csv"),
            os.path.join(base, "new.csv"),
            os.path.join(base, "result.json"))


def _txt(value) -> str:
    """Collapse whitespace and case — used only to decide whether two values
    are the same, never to rewrite what is stored or displayed."""
    return " ".join(str(value or "").split()).strip().lower()


def _norm(value) -> str:
    """Collapse whitespace but keep case, for display and equality."""
    return " ".join(str(value or "").split()).strip()


def _key(value) -> str:
    """Connection Number reduced to a comparable form.

    Digits and letters only, lower-cased, leading zeros dropped, so 0012020162
    and 12020162 are recognised as the same connection while 502 and 502-B
    stay apart.
    """
    return re.sub(r"[^0-9a-z]", "", str(value or "").lower()).lstrip("0")


def status_of(raw) -> str:
    return STATUS_MAP.get(_txt(raw), "Other")


def read_upload(filename: str, blob: bytes):
    """Read an uploaded CSV/XLSX as text, transparently un-gzipping it.

    The browser compresses before posting because two exports together run to
    ~12 MB and a serverless request body caps at 4.5 MB.
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


def _first_by_key(keys) -> dict:
    """First row position per connection number.

    A file may repeat a connection number; the first occurrence represents it
    for field comparison and every repeat is reported separately as a
    duplicate, so nothing is silently merged away.
    """
    seen = {}
    for position, key in enumerate(keys):
        if key and key not in seen:
            seen[key] = position
    return seen


def _duplicate_keys(keys) -> list:
    counts = {}
    for key in keys:
        if key:
            counts[key] = counts.get(key, 0) + 1
    return [{"key": k, "count": v} for k, v in sorted(counts.items()) if v > 1]


def build_comparison(old_df: pd.DataFrame, new_df: pd.DataFrame,
                     old_name: str, new_name: str) -> dict:
    """Compare two exports on Connection Number. Read-only."""
    for label, df in (("old", old_df), ("new", new_df)):
        if KEY_COLUMN not in df.columns:
            raise ValueError(f"The {label} file has no '{KEY_COLUMN}' column to match on.")

    old_keys = list(old_df[KEY_COLUMN].map(_key))
    new_keys = list(new_df[KEY_COLUMN].map(_key))
    old_at, new_at = _first_by_key(old_keys), _first_by_key(new_keys)
    old_set, new_set = set(old_at), set(new_at)
    added, removed = sorted(new_set - old_set), sorted(old_set - new_set)
    common = sorted(old_set & new_set)

    old_cols, new_cols = list(old_df.columns), list(new_df.columns)
    shared_cols = [c for c in old_cols if c in new_cols and c != "Sr #"]
    status_col = "Status" if "Status" in shared_cols else None

    changes, changed_keys, transitions, status_changes = [], set(), {}, []
    cosmetic_keys = set()
    old_records, new_records = old_df.to_dict("records"), new_df.to_dict("records")

    for key in common:
        a, b = old_records[old_at[key]], new_records[new_at[key]]
        for column in shared_cols:
            before, after = _norm(a.get(column)), _norm(b.get(column))
            if before == after:
                continue
            # A value that differs only in capitalisation is the export
            # re-casing itself, not somebody editing the record; so is a
            # connection number regaining or losing leading zeros. Both are
            # reported, but only substantive edits should raise an eyebrow.
            cosmetic = before.lower() == after.lower()
            if not cosmetic and column == KEY_COLUMN:
                cosmetic = _key(before) == _key(after)
            (cosmetic_keys if cosmetic else changed_keys).add(key)
            changes.append({
                "cosmetic": cosmetic,
                "key": key,
                "connection": _norm(b.get(KEY_COLUMN)),
                "consumer": _norm(b.get("Consumer Name")),
                "sector": _norm(b.get("Sector")),
                "locality": _norm(b.get("Locality")),
                "field": column,
                "old": before,
                "new": after,
                "identity": _txt(column) in IDENTITY_FIELDS,
            })
        if status_col:
            before, after = status_of(a.get(status_col)), status_of(b.get(status_col))
            if before != after:
                pair = f"{before} → {after}"
                transitions[pair] = transitions.get(pair, 0) + 1
                status_changes.append({
                    "key": key,
                    "connection": _norm(b.get(KEY_COLUMN)),
                    "consumer": _norm(b.get("Consumer Name")),
                    "sector": _norm(b.get("Sector")),
                    "locality": _norm(b.get("Locality")),
                    "old": before,
                    "new": after,
                    "suspicious": (before, after) in SUSPICIOUS_TRANSITIONS,
                })

    def status_counts(records, at):
        """Count one status per connection, not per row.

        A file that repeats a connection would otherwise count it several
        times; this file repeats 10,065 of them. The raw row totals are
        reported separately so the duplication stays visible.
        """
        counts = dict.fromkeys(STATUS_ORDER, 0)
        if status_col:
            for position in at.values():
                name = status_of(records[position].get(status_col))
                counts[name] = counts.get(name, 0) + 1
        return counts

    return {
        "version": RESULT_VERSION,
        "built_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "files": {
            "old": {"name": old_name, "rows": int(len(old_df)), "columns": old_cols},
            "new": {"name": new_name, "rows": int(len(new_df)), "columns": new_cols},
        },
        "columns": {
            "added": [c for c in new_cols if c not in old_cols],
            "removed": [c for c in old_cols if c not in new_cols],
            "compared": shared_cols,
        },
        # Not "keys": that name shadows dict.keys in a template.
        "matching": {"added": added, "removed": removed, "common": len(common)},
        "duplicates": {"old": _duplicate_keys(old_keys), "new": _duplicate_keys(new_keys)},
        "blank_keys": {"old": old_keys.count(""), "new": new_keys.count("")},
        "changes": changes,
        "changed_keys": sorted(changed_keys),
        "cosmetic_keys": sorted(cosmetic_keys - changed_keys),
        "status": {
            "old": status_counts(old_records, old_at),
            "new": status_counts(new_records, new_at),
            "counted": {"old": len(old_at), "new": len(new_at)},
            "transitions": transitions,
            "records": status_changes,
        },
    }


# ---------------------------------------------------------------------------
# Persistence — both uploads are kept verbatim so every view re-derives from
# the files themselves rather than from a summary that could drift.
# ---------------------------------------------------------------------------

def save_comparison(old_df, new_df, result) -> None:
    old_path, new_path, result_path = _paths()
    old_df.to_csv(old_path, index=False)
    new_df.to_csv(new_path, index=False)
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False)


def load_comparison():
    """(result, old_df, new_df) or (None, None, None) when nothing is loaded."""
    old_path, new_path, result_path = _paths()
    if not os.path.exists(result_path):
        return None, None, None
    try:
        with open(result_path, "r", encoding="utf-8") as fh:
            result = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None, None, None
    if result.get("version") != RESULT_VERSION or not os.path.exists(old_path):
        return None, None, None
    read = lambda path: pd.read_csv(path, dtype=str, keep_default_na=False)
    return result, read(old_path), read(new_path)


def clear_comparison() -> None:
    for path in _paths():
        if os.path.exists(path):
            os.remove(path)


def rows_for_keys(df: pd.DataFrame, keys, limit=None) -> tuple:
    """Full records behind a set of connection numbers, in file order."""
    wanted = set(keys)
    if not wanted:
        return list(df.columns), [], 0
    marks = df[KEY_COLUMN].map(_key)
    picked = df[marks.isin(wanted)]
    total = len(picked)
    if limit:
        picked = picked.head(limit)
    return list(df.columns), picked.astype(str).values.tolist(), total


# ---------------------------------------------------------------------------
# Upload, shared by both pages
# ---------------------------------------------------------------------------

def _handle_upload(redirect_endpoint):
    main = _app()
    old_file = request.files.get("old_file")
    new_file = request.files.get("new_file")
    for label, upload in (("older", old_file), ("newer", new_file)):
        if not upload or not upload.filename:
            message = f"Please choose the {label} file."
            return main.ajax_error(message) if main.is_ajax() else (
                flash(message) or redirect(url_for(redirect_endpoint)))
        base = upload.filename[:-3] if upload.filename.lower().endswith(".gz") else upload.filename
        if not main.allowed_file(base):
            message = f"Unsupported file type: {upload.filename}"
            return main.ajax_error(message) if main.is_ajax() else (
                flash(message) or redirect(url_for(redirect_endpoint)))
    try:
        old_name, old_df = read_upload(old_file.filename, old_file.read())
        new_name, new_df = read_upload(new_file.filename, new_file.read())
        result = build_comparison(old_df, new_df,
                                  secure_filename(old_name), secure_filename(new_name))
        save_comparison(old_df, new_df, result)
    except Exception as exc:  # noqa: BLE001 — surfaced to the user
        message = f"Could not compare the files: {exc}"
        return main.ajax_error(message) if main.is_ajax() else (
            flash(message) or redirect(url_for(redirect_endpoint)))

    substantive = [c for c in result["changes"] if not c["cosmetic"]]
    message = (
        f"Compared. {result['matching']['common']:,} connections in both files, "
        f"{len(result['matching']['added']):,} added, {len(result['matching']['removed']):,} removed, "
        f"{len(substantive):,} substantive field change(s)."
    )
    if main.is_ajax():
        return main.ajax_ok(message=message, redirect_url=url_for(redirect_endpoint))
    flash(message)
    return redirect(url_for(redirect_endpoint))


# ---------------------------------------------------------------------------
# Page 1 — File Comparison (structural diff)
# ---------------------------------------------------------------------------

PREVIEW_LIMIT = 250


@compare_bp.route("/file-comparison", methods=["GET", "POST"])
def file_comparison():
    if request.method == "POST":
        if request.form.get("action") == "clear":
            clear_comparison()
            flash("Comparison data cleared.")
            return redirect(url_for("compare.file_comparison"))
        return _handle_upload("compare.file_comparison")

    result, old_df, new_df = load_comparison()
    if result is None:
        return render_template("file_comparison.html", active_page="file_comparison", result=None)

    view = request.args.get("view", "added")
    search = _txt(request.args.get("q", ""))

    if view == "removed":
        columns, rows, total = rows_for_keys(old_df, result["matching"]["removed"], PREVIEW_LIMIT)
    elif view == "duplicates":
        side = request.args.get("side", "new")
        source = new_df if side == "new" else old_df
        columns, rows, total = rows_for_keys(
            source, [d["key"] for d in result["duplicates"][side]], PREVIEW_LIMIT)
    else:
        view = "added"
        columns, rows, total = rows_for_keys(new_df, result["matching"]["added"], PREVIEW_LIMIT)

    if search:
        rows = [r for r in rows if any(search in _txt(cell) for cell in r)]

    substantive = [c for c in result["changes"] if not c["cosmetic"]]
    return render_template(
        "file_comparison.html",
        active_page="file_comparison",
        result=result,
        view=view,
        side=request.args.get("side", "new"),
        search=request.args.get("q", ""),
        columns=columns,
        rows=rows,
        shown=len(rows),
        total=total,
        preview_limit=PREVIEW_LIMIT,
        substantive_count=len(substantive),
        cosmetic_count=len(result["changes"]) - len(substantive),
    )


@compare_bp.route("/file-comparison/export/<view>")
def export_file_comparison(view: str):
    result, old_df, new_df = load_comparison()
    if result is None:
        flash("Upload both files first.")
        return redirect(url_for("compare.file_comparison"))
    if view == "removed":
        columns, rows, _ = rows_for_keys(old_df, result["matching"]["removed"])
    elif view == "duplicates":
        side = request.args.get("side", "new")
        source = new_df if side == "new" else old_df
        columns, rows, _ = rows_for_keys(source, [d["key"] for d in result["duplicates"][side]])
    else:
        view = "added"
        columns, rows, _ = rows_for_keys(new_df, result["matching"]["added"])
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(columns)
    writer.writerows(rows)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return Response(out.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition": f"attachment; filename=File_Comparison_{view}_{stamp}.csv"})


# ---------------------------------------------------------------------------
# Page 2 — Data Integrity Check (status audit)
# ---------------------------------------------------------------------------

AUDIT_VIEWS = ("status", "active_closed", "modified", "added", "deleted", "duplicates", "all")


def _audit_rows(result, view, sector, locality, search):
    """Rows for the audit table, already filtered. Returns (headers, rows)."""
    def keep(record):
        if sector and _txt(record.get("sector")) != _txt(sector):
            return False
        if locality and _txt(record.get("locality")) != _txt(locality):
            return False
        if search and not any(search in _txt(record.get(f)) for f in
                              ("connection", "consumer", "sector", "locality", "old", "new", "field")):
            return False
        return True

    status_records = result["status"]["records"]
    if view == "active_closed":
        picked = [r for r in status_records if r["old"] == "Active" and r["new"] == "Closed"]
        headers = ["Connection No.", "Consumer Name", "Sector", "Locality", "Old Status", "New Status"]
        rows = [[r["connection"], r["consumer"], r["sector"], r["locality"], r["old"], r["new"]]
                for r in status_records if keep(r) and r in picked]
        return headers, rows
    if view == "status":
        headers = ["Connection No.", "Consumer Name", "Sector", "Locality", "Old Status", "New Status"]
        rows = [[r["connection"], r["consumer"], r["sector"], r["locality"], r["old"], r["new"]]
                for r in status_records if keep(r)]
        return headers, rows

    headers = ["Connection No.", "Consumer Name", "Sector", "Locality",
               "Field Changed", "Old Value", "New Value", "Kind"]
    changes = result["changes"]
    if view == "modified":
        changes = [c for c in changes if not c["cosmetic"]]
    rows = [[c["connection"], c["consumer"], c["sector"], c["locality"], c["field"],
             c["old"], c["new"], "Case/format only" if c["cosmetic"] else "Substantive"]
            for c in changes if keep(c)]
    return headers, rows


@compare_bp.route("/data-integrity", methods=["GET", "POST"])
def data_integrity():
    if request.method == "POST":
        if request.form.get("action") == "clear":
            clear_comparison()
            flash("Audit data cleared.")
            return redirect(url_for("compare.data_integrity"))
        return _handle_upload("compare.data_integrity")

    result, old_df, new_df = load_comparison()
    if result is None:
        return render_template("data_integrity.html", active_page="data_integrity", result=None)

    view = request.args.get("view", "status")
    if view not in AUDIT_VIEWS:
        view = "status"
    sector = request.args.get("sector", "")
    locality = request.args.get("locality", "")
    search = _txt(request.args.get("q", ""))

    if view in ("added", "deleted", "duplicates"):
        if view == "added":
            columns, rows, total = rows_for_keys(new_df, result["matching"]["added"], PREVIEW_LIMIT)
        elif view == "deleted":
            columns, rows, total = rows_for_keys(old_df, result["matching"]["removed"], PREVIEW_LIMIT)
        else:
            columns, rows, total = rows_for_keys(
                new_df, [d["key"] for d in result["duplicates"]["new"]], PREVIEW_LIMIT)
        headers = columns
    else:
        headers, rows = _audit_rows(result, view, sector, locality, search)
        total = len(rows)
        rows = rows[:PREVIEW_LIMIT]

    status_records = result["status"]["records"]
    substantive = [c for c in result["changes"] if not c["cosmetic"]]
    sectors = sorted({r["sector"] for r in status_records if r["sector"]} |
                     {c["sector"] for c in substantive if c["sector"]})
    localities = sorted({r["locality"] for r in status_records if r["locality"]} |
                        {c["locality"] for c in substantive if c["locality"]})

    old_counts, new_counts = result["status"]["old"], result["status"]["new"]
    status_rows = [
        {"name": name, "old": old_counts.get(name, 0), "new": new_counts.get(name, 0),
         "delta": new_counts.get(name, 0) - old_counts.get(name, 0)}
        for name in STATUS_ORDER if old_counts.get(name) or new_counts.get(name)
    ]

    return render_template(
        "data_integrity.html",
        active_page="data_integrity",
        result=result,
        view=view,
        sector=sector,
        locality=locality,
        search=request.args.get("q", ""),
        sectors=sectors,
        localities=localities,
        status_rows=status_rows,
        transitions=sorted(result["status"]["transitions"].items(), key=lambda kv: -kv[1]),
        active_closed=[r for r in status_records if r["old"] == "Active" and r["new"] == "Closed"],
        headers=headers,
        rows=rows,
        shown=len(rows),
        total=total,
        preview_limit=PREVIEW_LIMIT,
        substantive_count=len(substantive),
        cosmetic_count=len(result["changes"]) - len(substantive),
    )


@compare_bp.route("/data-integrity/export/<fmt>")
def export_data_integrity(fmt: str):
    result, old_df, new_df = load_comparison()
    if result is None:
        flash("Upload both files first.")
        return redirect(url_for("compare.data_integrity"))

    view = request.args.get("view", "status")
    if view not in AUDIT_VIEWS:
        view = "status"
    sector, locality = request.args.get("sector", ""), request.args.get("locality", "")
    search = _txt(request.args.get("q", ""))

    if view in ("added", "deleted", "duplicates"):
        if view == "added":
            headers, rows, _ = rows_for_keys(new_df, result["matching"]["added"])
        elif view == "deleted":
            headers, rows, _ = rows_for_keys(old_df, result["matching"]["removed"])
        else:
            headers, rows, _ = rows_for_keys(
                new_df, [d["key"] for d in result["duplicates"]["new"]])
    else:
        headers, rows = _audit_rows(result, view, sector, locality, search)

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    slug = f"Data_Integrity_{view}_{stamp}"

    if fmt == "csv":
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(headers)
        writer.writerows(rows)
        return Response(out.getvalue(), mimetype="text/csv", headers={
            "Content-Disposition": f"attachment; filename={slug}.csv"})

    if fmt != "pdf":
        flash("Unsupported export format.")
        return redirect(url_for("compare.data_integrity"))

    return _audit_pdf(result, view, headers, rows, slug)


def _audit_pdf(result, view, headers, rows, slug):
    """The audit as a permanent record: what was compared, and what moved."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    main = _app()
    buf = io.BytesIO()
    page_size = landscape(A4)
    margin = 8 * mm
    doc = SimpleDocTemplate(buf, pagesize=page_size, topMargin=margin,
                            bottomMargin=margin + 4 * mm, leftMargin=margin,
                            rightMargin=margin, title="Data Integrity Audit")
    styles = getSampleStyleSheet()
    title = ParagraphStyle("CATitle", parent=styles["Heading1"], fontSize=17, alignment=1,
                           spaceAfter=1.5 * mm, textColor=colors.black,
                           fontName="Helvetica-Bold")
    sub = ParagraphStyle("CASub", parent=styles["Normal"], fontSize=8.5, alignment=1,
                         spaceAfter=1 * mm, textColor=colors.black)
    head = ParagraphStyle("CAHead", parent=styles["Normal"], fontSize=11, spaceBefore=4 * mm,
                          spaceAfter=2 * mm, fontName="Helvetica-Bold", textColor=colors.black)

    files = result["files"]
    substantive = [c for c in result["changes"] if not c["cosmetic"]]
    elements = [
        Paragraph("Data Integrity Audit", title),
        Paragraph(f"Generated {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub),
        Paragraph(
            f"Older: {files['old']['name']} ({files['old']['rows']:,} rows) &nbsp;&bull;&nbsp; "
            f"Newer: {files['new']['name']} ({files['new']['rows']:,} rows) &nbsp;&bull;&nbsp; "
            f"matched on Connection No.", sub),
        Spacer(1, 3 * mm),
        Paragraph("Summary", head),
    ]

    page_w = page_size[0] - 2 * margin
    summary = [
        ["Connections in both files", f"{result['matching']['common']:,}"],
        ["Records added", f"{len(result['matching']['added']):,}"],
        ["Records deleted", f"{len(result['matching']['removed']):,}"],
        ["Records with a substantive change", f"{len(result['changed_keys']):,}"],
        ["Records with case/format changes only", f"{len(result['cosmetic_keys']):,}"],
        ["Substantive field changes", f"{len(substantive):,}"],
        ["Case/format-only field changes", f"{len(result['changes']) - len(substantive):,}"],
        ["Status changes", f"{len(result['status']['records']):,}"],
        ["Duplicate connection numbers (older / newer)",
         f"{len(result['duplicates']['old']):,} / {len(result['duplicates']['new']):,}"],
        ["Columns added / removed",
         f"{', '.join(result['columns']['added']) or '—'} / "
         f"{', '.join(result['columns']['removed']) or '—'}"],
    ]
    elements.append(main._make_pdf_table(
        [["Measure", "Value"]] + summary,
        col_widths=[page_w * 0.62, page_w * 0.38], left_cols={0},
        header_font_size=9, body_font_size=8.5, cell_padding=3))

    elements.append(Paragraph("Connection status, per connection", head))
    old_counts, new_counts = result["status"]["old"], result["status"]["new"]
    status_table = [["Status", "Older file", "Newer file", "Change"]]
    for name in STATUS_ORDER:
        before, after = old_counts.get(name, 0), new_counts.get(name, 0)
        if before or after:
            delta = after - before
            status_table.append([name, f"{before:,}", f"{after:,}",
                                 f"{delta:+,}" if delta else "0"])
    elements.append(main._make_pdf_table(
        status_table, col_widths=[page_w * 0.4] + [page_w * 0.2] * 3, left_cols={0},
        header_font_size=9, body_font_size=8.5, cell_padding=3))

    elements.append(Paragraph(f"{view.replace('_', ' ').title()} — {len(rows):,} record(s)", head))
    if not rows:
        elements.append(Paragraph("Nothing to report for this view.", sub))
    else:
        wrap_idx = {i for i, h in enumerate(headers)
                    if _txt(h) in {"consumer name", "sector", "locality", "old value",
                                   "new value", "address", "f/h name"}}
        body = [[Paragraph(main._esc_html(str(c)) if hasattr(main, "_esc_html") else
                           str(c).replace("&", "&amp;").replace("<", "&lt;"),
                           ParagraphStyle("CACell", parent=styles["Normal"], fontSize=6.5,
                                          leading=7.5, alignment=0))
                 if i in wrap_idx else str(c)
                 for i, c in enumerate(row)] for row in rows[:4000]]
        widths = [page_w / len(headers)] * len(headers)
        table = main._make_pdf_table([headers] + body, col_widths=widths, left_cols=wrap_idx,
                                     header_font_size=7.5, body_font_size=6.5, cell_padding=2)
        table.setStyle(__import__("reportlab.platypus", fromlist=["TableStyle"]).TableStyle(
            [("LEADING", (0, 1), (-1, -1), 7.5)]))
        elements.append(table)
        if len(rows) > 4000:
            elements.append(Paragraph(
                f"Showing the first 4,000 of {len(rows):,} rows; the CSV export carries them all.",
                sub))

    doc.build(elements)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="application/pdf", headers={
        "Content-Disposition": f"inline; filename={slug}.pdf"})
