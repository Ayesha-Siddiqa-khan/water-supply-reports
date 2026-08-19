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
ACTIVE_BUCKETS = [
    ("still_active", "Still Active"),
    ("closed", "Active → Closed"),
    ("suspended", "Active → Suspended"),
    ("new_demand", "Active → New Demand"),
    ("other", "Active → Other Status"),
    ("missing", "Missing from New File"),
]
# The two that mean a running connection stopped running.
ACTIVE_ALERT_BUCKETS = ("closed", "missing")

IDENTITY_FIELDS = {"consumer name", "f/h name", "sector", "locality", "connection no."}

KEY_COLUMN = "Connection No."

# Bumped whenever the stored result's shape changes. A result written by an
# older build is discarded rather than half-read, which would otherwise fail
# with a template error instead of simply asking for the files again.
RESULT_VERSION = 3


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

    # ---- The audit proper: follow every connection that was Active in the
    # older file into the newer one, one connection at a time. Aggregate
    # counts can stay level while individual connections close, so each is
    # resolved on its own and placed in exactly one bucket.
    active_records, active_counts = [], dict.fromkeys(dict(ACTIVE_BUCKETS), 0)
    for key, position in old_at.items():
        before_row = old_records[position]
        if status_of(before_row.get(status_col)) != "Active":
            continue
        if key in new_at:
            after_row = new_records[new_at[key]]
            after = status_of(after_row.get(status_col))
            bucket = {"Active": "still_active", "Closed": "closed",
                      "Suspended": "suspended", "New Demand": "new_demand"}.get(after, "other")
            source = after_row
        else:
            after, bucket, source = "Missing from new file", "missing", before_row
        active_counts[bucket] += 1
        active_records.append({
            "key": key,
            "bucket": bucket,
            # Identity is taken from the older file, which is the baseline the
            # audit is asking about; the status is what the newer file says.
            "connection": _norm(before_row.get(KEY_COLUMN)),
            "consumer": _norm(before_row.get("Consumer Name")),
            "father": _norm(before_row.get("F/H Name")),
            "sector": _norm(before_row.get("Sector")),
            "locality": _norm(before_row.get("Locality")),
            "old": "Active",
            "new": after,
        })
    active_records.sort(key=lambda r: (r["sector"], r["locality"], r["connection"]))

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
        "active_audit": {
            "total": len(active_records),
            "counts": active_counts,
            "records": active_records,
        },
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

AUDIT_HEADERS = ["Connection No.", "Consumer Name", "Father Name",
                 "Sector", "Locality", "Old Status", "New Status"]


def audit_rows(result, view="all", sector="", locality="", search=""):
    """The audit table: every connection that was Active in the older file.

    ``view`` is a bucket key, or "all". Filtering never changes a record's
    bucket — it only decides which are listed — so the summary counts and the
    table can never tell different stories.
    """
    search = _txt(search)
    rows = []
    for record in result["active_audit"]["records"]:
        if view != "all" and record["bucket"] != view:
            continue
        if sector and _txt(record["sector"]) != _txt(sector):
            continue
        if locality and _txt(record["locality"]) != _txt(locality):
            continue
        if search and not any(search in _txt(record[f]) for f in
                              ("connection", "consumer", "father", "sector", "locality")):
            continue
        rows.append([record["connection"], record["consumer"], record["father"],
                     record["sector"], record["locality"], record["old"], record["new"]])
    return AUDIT_HEADERS, rows


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

    buckets = dict(ACTIVE_BUCKETS)
    view = request.args.get("view", "all")
    if view not in buckets and view != "all":
        view = "all"
    sector = request.args.get("sector", "")
    locality = request.args.get("locality", "")
    search = request.args.get("q", "")

    headers, rows = audit_rows(result, view, sector, locality, search)
    records = result["active_audit"]["records"]

    return render_template(
        "data_integrity.html",
        active_page="data_integrity",
        result=result,
        audit=result["active_audit"],
        bucket_labels=ACTIVE_BUCKETS,
        alert_buckets=ACTIVE_ALERT_BUCKETS,
        view=view,
        sector=sector,
        locality=locality,
        search=search,
        sectors=sorted({r["sector"] for r in records if r["sector"]}),
        localities=sorted({r["locality"] for r in records if r["locality"]}),
        headers=headers,
        rows=rows[:PREVIEW_LIMIT],
        shown=min(len(rows), PREVIEW_LIMIT),
        total=len(rows),
        preview_limit=PREVIEW_LIMIT,
    )


@compare_bp.route("/data-integrity/export/<fmt>")
def export_data_integrity(fmt: str):
    result, _, _ = load_comparison()
    if result is None:
        flash("Upload both files first.")
        return redirect(url_for("compare.data_integrity"))

    view = request.args.get("view", "all")
    if view not in dict(ACTIVE_BUCKETS) and view != "all":
        view = "all"
    headers, rows = audit_rows(result, view, request.args.get("sector", ""),
                               request.args.get("locality", ""), request.args.get("q", ""))
    slug = f"Active_Consumer_Audit_{view}_{datetime.now().strftime('%Y%m%d_%H%M')}"

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
    """The audit as a permanent record: which Active connections moved, and where."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, TableStyle

    main = _app()
    buf = io.BytesIO()
    page_size = landscape(A4)
    margin = 8 * mm
    doc = SimpleDocTemplate(buf, pagesize=page_size, topMargin=margin,
                            bottomMargin=margin + 4 * mm, leftMargin=margin,
                            rightMargin=margin, title="Active Consumer Audit")
    styles = getSampleStyleSheet()
    title = ParagraphStyle("CATitle", parent=styles["Heading1"], fontSize=17, alignment=1,
                           spaceAfter=1.5 * mm, textColor=colors.black, fontName="Helvetica-Bold")
    sub = ParagraphStyle("CASub", parent=styles["Normal"], fontSize=8.5, alignment=1,
                         spaceAfter=1 * mm, textColor=colors.black)
    head = ParagraphStyle("CAHead", parent=styles["Normal"], fontSize=11, spaceBefore=4 * mm,
                          spaceAfter=2 * mm, fontName="Helvetica-Bold", textColor=colors.black)

    files, audit = result["files"], result["active_audit"]
    page_w = page_size[0] - 2 * margin
    elements = [
        Paragraph("Active Consumer Audit", title),
        Paragraph(f"Generated {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub),
        Paragraph(
            f"Baseline: {files['old']['name']} ({files['old']['rows']:,} rows) "
            f"&nbsp;&bull;&nbsp; Compared with: {files['new']['name']} "
            f"({files['new']['rows']:,} rows) &nbsp;&bull;&nbsp; matched on Connection No.", sub),
        Paragraph(
            "Every connection recorded as Active in the baseline file is followed into the "
            "newer file individually, so a connection closing cannot hide behind a level total.",
            sub),
        Spacer(1, 3 * mm),
        Paragraph("Summary", head),
    ]

    summary = [["Active consumers in the older file", f"{audit['total']:,}"]]
    for key, label in ACTIVE_BUCKETS:
        summary.append([label, f"{audit['counts'].get(key, 0):,}"])
    elements.append(main._make_pdf_table(
        [["Measure", "Connections"]] + summary,
        col_widths=[page_w * 0.62, page_w * 0.38], left_cols={0},
        header_font_size=9, body_font_size=8.5, cell_padding=3))

    alerts = sum(audit["counts"].get(k, 0) for k in ACTIVE_ALERT_BUCKETS)
    elements.append(Paragraph(
        f"<b>{alerts:,}</b> previously-active connection(s) are now closed or absent from the "
        "newer file." if alerts else
        "<b>No previously-active connection was closed, and none is absent from the newer file.</b>",
        sub))

    label = dict(ACTIVE_BUCKETS).get(view, "All previously-active connections")
    elements.append(Paragraph(f"{label} — {len(rows):,} connection(s)", head))
    if not rows:
        elements.append(Paragraph("No connections in this category.", sub))
    else:
        cell = ParagraphStyle("CACell", parent=styles["Normal"], fontSize=6.5,
                              leading=7.5, alignment=0)
        wrap_idx = {1, 2, 3, 4}
        body = [[Paragraph(str(value).replace("&", "&amp;").replace("<", "&lt;"), cell)
                 if i in wrap_idx else str(value)
                 for i, value in enumerate(row)] for row in rows[:6000]]
        widths = [page_w * w for w in (0.12, 0.18, 0.18, 0.20, 0.18, 0.07, 0.07)]
        table = main._make_pdf_table([headers] + body, col_widths=widths, left_cols=wrap_idx,
                                     header_font_size=7.5, body_font_size=6.5, cell_padding=2)
        table.setStyle(TableStyle([("LEADING", (0, 1), (-1, -1), 7.5)]))
        elements.append(table)
        if len(rows) > 6000:
            elements.append(Paragraph(
                f"Showing the first 6,000 of {len(rows):,}; the CSV export carries them all.", sub))

    doc.build(elements)
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="application/pdf", headers={
        "Content-Disposition": f"inline; filename={slug}.pdf"})
