"""
Arrears Analysis Blueprint
==========================
Independent module providing locality-wise Arrears Analysis for water supply consumers.
Calculates Regular (Open) vs Suspended connections and outstanding arrears per locality,
with interactive filtering, column selection, summary & detailed reporting, landscape print,
and professional PDF/Excel/CSV exports.
"""

from __future__ import annotations

import base64
import csv
from datetime import datetime
import gzip
import io
import json
import os
import re
from typing import Any

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
import openpyxl
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from werkzeug.utils import secure_filename

arrears_analysis_bp = Blueprint("arrears_analysis", __name__)


def _app():
    import app
    return app


def _arrears_dir() -> str:
    path = os.path.join(_app().UPLOAD_FOLDER, "arrears_analysis")
    os.makedirs(path, exist_ok=True)
    return path


def _working_csv() -> str:
    return os.path.join(_arrears_dir(), "working.csv")


def _working_meta() -> str:
    return os.path.join(_arrears_dir(), "working_meta.json")


def _handover_working_csv() -> str:
    return os.path.join(_app().UPLOAD_FOLDER, "handover", "working.csv")


def parse_amount(val: Any) -> float:
    """Safely parse currency / arrears numbers from CSV string or number."""
    if val is None or pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "").replace("PKR", "").replace("Rs.", "").replace("Rs", "").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def format_pkr(val: float | int) -> str:
    """Format numeric value with commas (no currency prefix in table cells)."""
    return f"{val:,.0f}"


def classify_status(raw_status: Any) -> str:
    """Classify connection status strictly according to report requirements:
    - Open: counts as Regular Connection (Open, Regular Connection, Active, Regular)
    - Suspended: counts as Suspended Connection
    - Closed, New Demand, etc.: excluded from arrears calculations.
    """
    if raw_status is None or pd.isna(raw_status):
        return "Unknown"
    s = str(raw_status).strip().lower()
    if s in ("open", "regular connection", "regular", "active"):
        return "Open"
    if "suspended" in s:
        return "Suspended"
    if "closed" in s:
        return "Closed"
    if "new demand" in s or s == "new":
        return "New Demand"
    return "Other"


def _detect_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find matching column name case-insensitively from candidates."""
    cols = list(df.columns)
    col_lower = {c.strip().lower(): c for c in cols}
    for cand in candidates:
        cand_l = cand.strip().lower()
        if cand_l in col_lower:
            return col_lower[cand_l]
    return None


def inspect_dataframe_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """Detect key domain columns in the uploaded dataframe."""
    return {
        "locality": _detect_column(df, ["Locality", "locality_name", "Locality Name"]),
        "sector": _detect_column(df, ["Sector", "sector_name", "Sector Name"]),
        "status": _detect_column(df, ["Status", "Connection Status", "Consumer Status"]),
        "arrears": _detect_column(df, ["Total Arrears", "TotalArrears", "Arrears", "arrears", "Net Arrears"]),
        "consumer_name": _detect_column(df, ["Consumer Name", "Name", "consumer_name"]),
        "fh_name": _detect_column(df, ["F/H Name", "Father Name", "Father/Husband Name", "f_h_name"]),
        "mobile": _detect_column(df, ["Mobile", "Mobile Number", "Contact", "Phone"]),
        "address": _detect_column(df, ["Address", "Consumer Address", "Street Address"]),
        "connection_no": _detect_column(df, ["Connection Number", "Connection No.", "Connection No", "Connection"]),
        "reference_no": _detect_column(df, ["Reference No.", "Reference No", "Ref No", "Order No. / Register No", "Order No"]),
    }


def load_working_dataset() -> tuple[pd.DataFrame | None, dict[str, Any]]:
    """Load cached working dataset or fallback to handover dataset if available."""
    csv_path = _working_csv()
    meta_path = _working_meta()
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        try:
            df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
            meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as fh:
                    meta = json.load(fh)
            return df, meta
        except Exception:
            pass

    # Auto-detect existing handover connections CSV if available
    ho_csv = _handover_working_csv()
    if os.path.exists(ho_csv) and os.path.getsize(ho_csv) > 0:
        try:
            df = pd.read_csv(ho_csv, dtype=str, keep_default_na=False)
            meta = {
                "source": "Handover Working Dataset",
                "filename": "handover_connections.csv",
                "loaded_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "auto_detected": True,
            }
            return df, meta
        except Exception:
            pass

    # Auto-detect bundled Bills CSV from repo root (ensures Vercel deployment has data immediately)
    import app
    base_dirs = [
        os.path.dirname(os.path.abspath(__file__)),
        getattr(app, "BASE_DIR", "."),
        os.getcwd(),
    ]
    seen_dirs = set()
    for bdir in base_dirs:
        if not bdir or bdir in seen_dirs:
            continue
        seen_dirs.add(bdir)
        candidate = os.path.join(bdir, "Bills-15-05-2026-08_11_13.csv")
        if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
            try:
                df = pd.read_csv(candidate, dtype=str, keep_default_na=False)
                meta = {
                    "source": "Bundled Bills Dataset",
                    "filename": "Bills-15-05-2026-08_11_13.csv",
                    "loaded_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "auto_detected": True,
                    "rows": len(df),
                }
                return df, meta
            except Exception:
                pass

    return None, {}


def compute_arrears_analysis(
    df: pd.DataFrame,
    selected_localities: list[str] | None = None,
    sectors: list[str] | None = None,
    category: str = "",
    sort_by: str = "arrears_desc",
) -> dict[str, Any]:
    """Perform locality-wise arrears aggregation.
    Strict logic:
      - Only Open (Regular Connection) and Suspended connections are calculated.
      - Closed and New Demand connections are excluded from arrears calculations.
      - Supports strict category filtering (Domestic vs Commercial).
    """
    detected = inspect_dataframe_columns(df)
    loc_col = detected["locality"] or "Locality"
    sec_col = detected["sector"] or "Sector"
    stat_col = detected["status"] or "Status"
    arr_col = detected["arrears"] or "Total Arrears"

    # Normalize data for calculations
    calc_df = df.copy()
    if loc_col not in calc_df.columns:
        calc_df[loc_col] = "Unspecified Locality"
    if sec_col not in calc_df.columns:
        calc_df[sec_col] = "-"
    if stat_col not in calc_df.columns:
        calc_df[stat_col] = "Open"
    if arr_col not in calc_df.columns:
        calc_df[arr_col] = 0.0

    calc_df["_parsed_status"] = calc_df[stat_col].apply(classify_status)
    calc_df["_parsed_arrears"] = calc_df[arr_col].apply(parse_amount)
    calc_df["_norm_locality"] = calc_df[loc_col].astype(str).str.strip()
    calc_df["_norm_sector"] = calc_df[sec_col].astype(str).str.strip()

    # Exclude misassigned residential colony records from Commercial sector
    calc_df = calc_df[~((calc_df["_norm_sector"].str.upper() == "COMMERCIAL") & (calc_df["_norm_locality"].str.upper().str.contains("COLONY")))]

    # Category separation: Domestic vs Commercial
    cat_lower = (category or "").strip().lower()
    if cat_lower == "commercial":
        calc_df = calc_df[calc_df["_norm_sector"].str.upper() == "COMMERCIAL"]
    elif cat_lower == "domestic":
        calc_df = calc_df[calc_df["_norm_sector"].str.upper() != "COMMERCIAL"]
    elif sectors:
        sec_list = [s.strip() for s in sectors if s.strip()]
        if sec_list:
            calc_df = calc_df[calc_df["_norm_sector"].isin(sec_list)]

    # Get sorted list of all unique localities
    all_localities_raw = sorted(
        [loc for loc in calc_df["_norm_locality"].unique() if loc],
        key=lambda x: x.lower()
    )

    # Active localities for report
    if selected_localities is not None:
        sel_set = set(selected_localities)
        active_localities = [loc for loc in all_localities_raw if loc in sel_set]
    else:
        active_localities = all_localities_raw

    # Locality-level summary metrics
    locality_summaries = []
    grand_total = {
        "regular_count": 0,
        "regular_arrears": 0.0,
        "suspended_count": 0,
        "suspended_arrears": 0.0,
        "closed_count": 0,
        "closed_arrears": 0.0,
        "total_count": 0,
        "total_arrears": 0.0,
    }

    # Pre-calculate counts for all localities to display on checkbox list
    locality_quick_counts = {}
    grouped_all = calc_df.groupby("_norm_locality")
    for loc_name, grp in grouped_all:
        regular_sub = grp[grp["_parsed_status"] == "Open"]
        suspended_sub = grp[grp["_parsed_status"] == "Suspended"]
        closed_sub = grp[grp["_parsed_status"] == "Closed"]
        locality_quick_counts[loc_name] = {
            "total_calc_count": len(regular_sub) + len(suspended_sub) + len(closed_sub),
            "total_calc_arrears": (
                regular_sub["_parsed_arrears"].sum()
                + suspended_sub["_parsed_arrears"].sum()
                + closed_sub["_parsed_arrears"].sum()
            ),
            "sector": grp["_norm_sector"].iloc[0] if len(grp) > 0 else "-",
        }

    # Now calculate full details for active localities
    for loc_name in active_localities:
        grp = calc_df[calc_df["_norm_locality"] == loc_name]
        sector_val = grp["_norm_sector"].iloc[0] if len(grp) > 0 else "-"

        reg_grp = grp[grp["_parsed_status"] == "Open"]
        sus_grp = grp[grp["_parsed_status"] == "Suspended"]
        cls_grp = grp[grp["_parsed_status"] == "Closed"]

        reg_count = len(reg_grp)
        reg_arrears = float(reg_grp["_parsed_arrears"].sum())

        sus_count = len(sus_grp)
        sus_arrears = float(sus_grp["_parsed_arrears"].sum())

        cls_count = len(cls_grp)
        cls_arrears = float(cls_grp["_parsed_arrears"].sum())

        comb_count = reg_count + sus_count + cls_count
        comb_arrears = reg_arrears + sus_arrears + cls_arrears

        loc_summary = {
            "locality": loc_name,
            "sector": sector_val,
            "regular_count": reg_count,
            "regular_arrears": reg_arrears,
            "regular_arrears_fmt": format_pkr(reg_arrears),
            "suspended_count": sus_count,
            "suspended_arrears": sus_arrears,
            "suspended_arrears_fmt": format_pkr(sus_arrears),
            "closed_count": cls_count,
            "closed_arrears": cls_arrears,
            "closed_arrears_fmt": format_pkr(cls_arrears),
            "total_count": comb_count,
            "total_arrears": comb_arrears,
            "total_arrears_fmt": format_pkr(comb_arrears),
        }
        locality_summaries.append(loc_summary)

        grand_total["regular_count"] += reg_count
        grand_total["regular_arrears"] += reg_arrears
        grand_total["suspended_count"] += sus_count
        grand_total["suspended_arrears"] += sus_arrears
        grand_total["closed_count"] += cls_count
        grand_total["closed_arrears"] += cls_arrears
        grand_total["total_count"] += comb_count
        grand_total["total_arrears"] += comb_arrears

    grand_total["regular_arrears_fmt"] = format_pkr(grand_total["regular_arrears"])
    grand_total["suspended_arrears_fmt"] = format_pkr(grand_total["suspended_arrears"])
    grand_total["closed_arrears_fmt"] = format_pkr(grand_total["closed_arrears"])
    grand_total["total_arrears_fmt"] = format_pkr(grand_total["total_arrears"])

    if sort_by == "arrears_desc":
        locality_summaries.sort(key=lambda s: s["total_arrears"], reverse=True)
    elif sort_by == "arrears_asc":
        locality_summaries.sort(key=lambda s: s["total_arrears"])
    elif sort_by == "name_asc":
        locality_summaries.sort(key=lambda s: s["locality"].lower())
    elif sort_by == "name_desc":
        locality_summaries.sort(key=lambda s: s["locality"].lower(), reverse=True)
    elif sort_by == "conn_desc":
        locality_summaries.sort(key=lambda s: s["total_count"], reverse=True)
    elif sort_by == "conn_asc":
        locality_summaries.sort(key=lambda s: s["total_count"])
    else:
        locality_summaries.sort(key=lambda s: s["total_arrears"], reverse=True)

    all_sectors_raw = sorted(
        [sec for sec in calc_df["_norm_sector"].unique() if sec and sec != "-"],
        key=lambda x: x.lower()
    )
    sector_locality_map = {}
    for sec_name, grp in calc_df.groupby("_norm_sector"):
        sec_str = str(sec_name).strip()
        if sec_str and sec_str != "-":
            locs = sorted([l for l in grp["_norm_locality"].unique() if l], key=lambda x: x.lower())
            sector_locality_map[sec_str] = locs

    return {
        "all_localities": all_localities_raw,
        "active_localities": active_localities,
        "all_sectors": all_sectors_raw,
        "sector_locality_map": sector_locality_map,
        "locality_quick_counts": locality_quick_counts,
        "locality_summaries": locality_summaries,
        "grand_total": grand_total,
        "detected_columns": detected,
        "total_rows": len(df),
    }


def get_detail_columns(df: pd.DataFrame) -> list[str]:
    """Determine all available displayable columns in the dataframe, ordered logically."""
    exclude_internal = {"_parsed_status", "_parsed_arrears", "_norm_locality", "_norm_sector", "_st"}
    raw_cols = [c for c in df.columns if c not in exclude_internal]
    priority_order = [
        "Sr.", "Connection Number", "Consumer Name", "F/H Name", "Mobile", "CNIC",
        "Locality", "Sector", "Address", "Status", "Rate Type", "Connection Date",
        "Reference No", "Reference No.", "Water Rate", "Sanitation Rate", "Drainage Rate",
        "Water Arrears", "Sanitation Arrears", "Drainage Arrears", "Fine Arrears", "Total Arrears"
    ]
    ordered = []
    col_map = {c.strip().lower(): c for c in raw_cols}
    for p in priority_order:
        pl = p.strip().lower()
        if pl in col_map:
            ordered.append(col_map[pl])
            del col_map[pl]
    for remaining in raw_cols:
        if remaining.strip().lower() in col_map:
            ordered.append(remaining)
    return ordered


DEFAULT_DETAIL_COLS = [
    "Consumer Name",
    "Mobile",
    "Connection Number",
    "Status",
    "Total Arrears",
]


def resolve_detail_columns(df: pd.DataFrame, requested_cols: list[str] | None = None) -> list[str]:
    """Resolve which columns to show in the detailed table."""
    all_cols = get_detail_columns(df)
    if not requested_cols:
        col_lower = {c.strip().lower(): c for c in all_cols}
        resolved = []
        for def_col in DEFAULT_DETAIL_COLS:
            dl = def_col.strip().lower()
            if dl in col_lower:
                resolved.append(col_lower[dl])
            else:
                for actual in all_cols:
                    if dl in actual.lower() and actual not in resolved:
                        resolved.append(actual)
                        break
        return resolved if resolved else all_cols[:8]
    # Filter requested to existing
    return [c for c in requested_cols if c in all_cols]


# ---------------------------------------------------------------------------
# PDF Document Helpers
# ---------------------------------------------------------------------------

class NumberedCanvas(canvas.Canvas):
    """ReportLab canvas that calculates and writes 'Page X of Y' on save."""

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

    def _draw_page_number(self, total: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#444444"))
        page_str = f"Page {self._pageNumber} of {total}"
        self.drawCentredString(self._pagesize[0] / 2.0, 5.0 * mm, page_str)
        self.restoreState()


def is_zero_summary(s: dict[str, Any], include_closed: bool = False) -> bool:
    """Returns True if all visible connection count and arrears fields are zero."""
    vis_count = int(s.get("regular_count", 0)) + int(s.get("suspended_count", 0)) + (int(s.get("closed_count", 0)) if include_closed else 0)
    vis_arrears = float(s.get("regular_arrears", 0.0)) + float(s.get("suspended_arrears", 0.0)) + (float(s.get("closed_arrears", 0.0)) if include_closed else 0.0)
    return (vis_count == 0 and vis_arrears == 0.0)


def build_arrears_pdf(
    df: pd.DataFrame,
    analysis: dict[str, Any],
    report_mode: str = "summary",
    detail_cols: list[str] | None = None,
    selected_sector: str = "",
    category: str = "",
    include_closed: bool = False,
    show_locality: bool = True,
    show_sector: bool = False,
    order: str = "loc_first",
    include_zero: bool = False,
) -> bytes:
    """Generate a clean consolidated landscape A4 PDF report with custom sector/locality columns and order."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=8 * mm,
        rightMargin=8 * mm,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AATitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,  # Center
        spaceAfter=3,
    )
    cell_style = ParagraphStyle(
        "AACell",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#334155"),
    )
    cell_bold_style = ParagraphStyle(
        "AACellBold",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # 1. Heading: Domestic vs Commercial vs Specific Sector
    cat_lower = (category or "").strip().lower()
    if cat_lower == "commercial":
        df = df[df['Sector'].astype(str).str.upper() == 'COMMERCIAL'].copy()
        df = df[~df['Locality'].astype(str).str.upper().str.contains('COLONY', na=False)].copy()
    elif cat_lower == "domestic":
        df = df[df['Sector'].astype(str).str.upper() != 'COMMERCIAL'].copy()

    if len(analysis.get("locality_summaries", [])) == 1:
        single_loc = analysis["locality_summaries"][0]["locality"]
        single_sec = analysis["locality_summaries"][0].get("sector", "")
        if report_mode == "detailed":
            title_text = f"Water Supply Consumer Arrears - {single_loc} ({single_sec}) - Detailed Report"
        else:
            title_text = f"Water Supply Consumer Arrears - {single_loc} ({single_sec})"
    elif report_mode == "detailed":
        if cat_lower == "commercial" or (selected_sector and "commercial" in selected_sector.lower()):
            title_text = "Water Supply Consumer Arrears - Commercial Sector (Detailed Report)"
        elif cat_lower == "domestic":
            if selected_sector and selected_sector not in ("All Sectors", "82 Sectors", "83 Sectors", ""):
                disp_sec = selected_sector.title() if selected_sector.isupper() else selected_sector
                title_text = f"Water Supply Consumer Arrears - Domestic ({disp_sec}) - Detailed Report"
            else:
                title_text = "Water Supply Consumer Arrears - Domestic Detailed Report"
        elif selected_sector and selected_sector not in ("All Sectors", "82 Sectors", "83 Sectors", ""):
            disp_sec = selected_sector.title() if selected_sector.isupper() else selected_sector
            title_text = f"Water Supply Consumer Arrears - {disp_sec} Sector - Detailed Report"
        else:
            title_text = "Water Supply Consumer Arrears - Detailed Report"
    elif cat_lower == "commercial" or (selected_sector and "commercial" in selected_sector.lower()):
        title_text = "Water Supply Consumer Arrears - Commercial Sector"
    elif cat_lower == "domestic":
        if selected_sector and selected_sector not in ("All Sectors", "82 Sectors", "83 Sectors", ""):
            disp_sec = selected_sector.title() if selected_sector.isupper() else selected_sector
            title_text = f"Water Supply Consumer Arrears - Domestic ({disp_sec})"
        else:
            title_text = "Water Supply Consumer Arrears - Domestic Report"
    elif selected_sector:
        disp_sec = selected_sector.title() if selected_sector.isupper() else selected_sector
        title_text = f"Water Supply Consumer Arrears - {disp_sec} Sector"
    else:
        title_text = "Water Supply Consumer Arrears"
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 2 * mm))

    # 2. Main Locality / Sector Arrears Table
    show_loc = show_locality
    show_sec = show_sector
    if not show_loc and not show_sec:
        show_loc = True

    # Build items to display: filter out zero rows if not include_zero
    active_summaries = list(analysis.get("locality_summaries", []))
    if not include_zero:
        active_summaries = [s for s in active_summaries if not is_zero_summary(s, include_closed)]

    if show_sec and not show_loc:
        sec_map = {}
        for item in active_summaries:
            sec = item.get("sector") or "-"
            if sec not in sec_map:
                sec_map[sec] = {
                    "sector": sec,
                    "locality": sec,
                    "regular_count": 0,
                    "regular_arrears": 0.0,
                    "suspended_count": 0,
                    "suspended_arrears": 0.0,
                    "closed_count": 0,
                    "closed_arrears": 0.0,
                }
            sec_map[sec]["regular_count"] += item["regular_count"]
            sec_map[sec]["regular_arrears"] += item["regular_arrears"]
            sec_map[sec]["suspended_count"] += item["suspended_count"]
            sec_map[sec]["suspended_arrears"] += item["suspended_arrears"]
            sec_map[sec]["closed_count"] += item["closed_count"]
            sec_map[sec]["closed_arrears"] += item["closed_arrears"]
        display_items = list(sec_map.values())
        display_items.sort(key=lambda s: s["regular_arrears"] + s["suspended_arrears"], reverse=True)
    else:
        display_items = list(active_summaries)
        if show_sec and show_loc and order == "sec_first":
            display_items.sort(key=lambda s: (s.get("sector", "").lower(), -s["total_arrears"]))

    # Paragraph styles for table elements (Clean B&W for standard printing)
    th_center = ParagraphStyle(
        "THCenter",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=colors.black,
        alignment=TA_CENTER,
    )
    th_left = ParagraphStyle(
        "THLeft",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=colors.black,
        alignment=TA_LEFT,
    )
    td_center = ParagraphStyle(
        "TDCenter",
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_CENTER,
    )
    td_sec = ParagraphStyle(
        "TDSec",
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#334155"),
        alignment=TA_LEFT,
    )
    td_loc = ParagraphStyle(
        "TDLoc",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_LEFT,
    )
    td_gt_title = ParagraphStyle(
        "TDGTTitle",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_LEFT,
    )
    td_gt_center = ParagraphStyle(
        "TDGTCenter",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_CENTER,
    )

    # Determine Header Columns and Widths (Total Width = 281 mm)
    two_name_cols = show_loc and show_sec
    if two_name_cols:
        sec_w = 38 * mm
        loc_w = 50 * mm
        name_th = (
            [Paragraph("Sector", th_left), Paragraph("Locality Name", th_left)]
            if order == "sec_first"
            else [Paragraph("Locality Name", th_left), Paragraph("Sector", th_left)]
        )
        name_widths = [sec_w, loc_w] if order == "sec_first" else [loc_w, sec_w]

        if include_closed:
            header_row = [Paragraph("Sr #", th_center)] + name_th + [
                Paragraph("Regular<br/>Conns", th_center),
                Paragraph("Regular Arrears<br/>(PKR)", th_center),
                Paragraph("Suspended<br/>Conns", th_center),
                Paragraph("Suspended Arrears<br/>(PKR)", th_center),
                Paragraph("Closed<br/>Conns", th_center),
                Paragraph("Closed Arrears<br/>(PKR)", th_center),
                Paragraph("Total<br/>Conns", th_center),
                Paragraph("Total Arrears<br/>(PKR)", th_center),
            ]
            c_sec_w = 30 * mm
            c_loc_w = 48 * mm
            c_name_widths = [c_sec_w, c_loc_w] if order == "sec_first" else [c_loc_w, c_sec_w]
            col_widths = [9 * mm] + c_name_widths + [18 * mm, 32 * mm, 18 * mm, 32 * mm, 17 * mm, 30 * mm, 17 * mm, 30 * mm]
        else:
            header_row = [Paragraph("Sr #", th_center)] + name_th + [
                Paragraph("Regular<br/>Conns", th_center),
                Paragraph("Regular Arrears<br/>(PKR)", th_center),
                Paragraph("Suspended<br/>Conns", th_center),
                Paragraph("Suspended Arrears<br/>(PKR)", th_center),
                Paragraph("Total<br/>Conns", th_center),
                Paragraph("Total Arrears<br/>(PKR)", th_center),
            ]
            col_widths = [10 * mm] + name_widths + [22 * mm, 40 * mm, 22 * mm, 40 * mm, 21 * mm, 38 * mm]
    else:
        single_name_title = "Sector Name" if show_sec else "Locality Name"
        if include_closed:
            header_row = [
                Paragraph("Sr #", th_center),
                Paragraph(single_name_title, th_left),
                Paragraph("Regular<br/>Conns", th_center),
                Paragraph("Regular Arrears<br/>(PKR)", th_center),
                Paragraph("Suspended<br/>Conns", th_center),
                Paragraph("Suspended Arrears<br/>(PKR)", th_center),
                Paragraph("Closed<br/>Conns", th_center),
                Paragraph("Closed Arrears<br/>(PKR)", th_center),
                Paragraph("Total<br/>Conns", th_center),
                Paragraph("Total Arrears<br/>(PKR)", th_center),
            ]
            col_widths = [11 * mm, 60 * mm, 20 * mm, 34 * mm, 20 * mm, 34 * mm, 18 * mm, 31 * mm, 20 * mm, 33 * mm]
        else:
            header_row = [
                Paragraph("Sr #", th_center),
                Paragraph(single_name_title, th_left),
                Paragraph("Regular<br/>Conns", th_center),
                Paragraph("Regular Arrears<br/>(PKR)", th_center),
                Paragraph("Suspended<br/>Conns", th_center),
                Paragraph("Suspended Arrears<br/>(PKR)", th_center),
                Paragraph("Total<br/>Conns", th_center),
                Paragraph("Total Arrears<br/>(PKR)", th_center),
            ]
            col_widths = [12 * mm, 75 * mm, 24 * mm, 43 * mm, 24 * mm, 43 * mm, 22 * mm, 38 * mm]

    table_data = [header_row]

    sum_reg_conns = 0
    sum_reg_arr = 0.0
    sum_sus_conns = 0
    sum_sus_arr = 0.0
    sum_cls_conns = 0
    sum_cls_arr = 0.0
    sum_tot_conns = 0
    sum_tot_arr = 0.0

    for idx, item in enumerate(display_items, 1):
        reg_c = item["regular_count"]
        reg_a = item["regular_arrears"]
        sus_c = item["suspended_count"]
        sus_a = item["suspended_arrears"]
        cls_c = item["closed_count"]
        cls_a = item["closed_arrears"]

        if include_closed:
            tot_c = reg_c + sus_c + cls_c
            tot_a = reg_a + sus_a + cls_a
        else:
            tot_c = reg_c + sus_c
            tot_a = reg_a + sus_a

        sum_reg_conns += reg_c
        sum_reg_arr += reg_a
        sum_sus_conns += sus_c
        sum_sus_arr += sus_a
        sum_cls_conns += cls_c
        sum_cls_arr += cls_a
        sum_tot_conns += tot_c
        sum_tot_arr += tot_a

        raw_loc = str(item.get("locality") or "-").strip()
        raw_sec = str(item.get("sector") or "-").strip()

        # Clean truncation / safe formatting so long names never bleed
        max_loc_len = 34 if two_name_cols else 42
        clean_loc = (raw_loc[:max_loc_len] + "...") if len(raw_loc) > (max_loc_len + 2) else raw_loc

        max_sec_len = 26 if two_name_cols else 42
        clean_sec = (raw_sec[:max_sec_len] + "...") if len(raw_sec) > (max_sec_len + 2) else raw_sec

        if two_name_cols:
            if order == "sec_first":
                name_cells = [Paragraph(clean_sec, td_sec), Paragraph(clean_loc, td_loc)]
            else:
                name_cells = [Paragraph(clean_loc, td_loc), Paragraph(clean_sec, td_sec)]
        else:
            name_text = clean_sec if show_sec else clean_loc
            name_cells = [Paragraph(name_text, td_loc)]

        if include_closed:
            metric_vals = [
                f"{reg_c:,}", f"{reg_a:,.0f}",
                f"{sus_c:,}", f"{sus_a:,.0f}",
                f"{cls_c:,}", f"{cls_a:,.0f}",
                f"{tot_c:,}", f"{tot_a:,.0f}",
            ]
        else:
            metric_vals = [
                f"{reg_c:,}", f"{reg_a:,.0f}",
                f"{sus_c:,}", f"{sus_a:,.0f}",
                f"{tot_c:,}", f"{tot_a:,.0f}",
            ]

        metric_cells = [Paragraph(m, td_center) for m in metric_vals]
        row = [Paragraph(str(idx), td_center)] + name_cells + metric_cells
        table_data.append(row)

    # Grand Total Bottom Row (11pt bold, centered numeric/arrears columns, no PKR prefix)
    if two_name_cols:
        grand_name_cells = [Paragraph("GRAND TOTAL", td_gt_title), Paragraph("-", td_gt_title)]
    else:
        grand_name_cells = [Paragraph("GRAND TOTAL", td_gt_title)]

    if include_closed:
        grand_metrics = [
            f"{sum_reg_conns:,}", f"{sum_reg_arr:,.0f}",
            f"{sum_sus_conns:,}", f"{sum_sus_arr:,.0f}",
            f"{sum_cls_conns:,}", f"{sum_cls_arr:,.0f}",
            f"{sum_tot_conns:,}", f"{sum_tot_arr:,.0f}",
        ]
    else:
        grand_metrics = [
            f"{sum_reg_conns:,}", f"{sum_reg_arr:,.0f}",
            f"{sum_sus_conns:,}", f"{sum_sus_arr:,.0f}",
            f"{sum_tot_conns:,}", f"{sum_tot_arr:,.0f}",
        ]
    grand_metric_cells = [Paragraph(m, td_gt_center) for m in grand_metrics]
    grand_row = [Paragraph("", td_gt_center)] + grand_name_cells + grand_metric_cells
    table_data.append(grand_row)

    main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.black),
        ("LINEABOVE", (0, 0), (-1, 0), 1.2, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING", (0, 1), (-1, -2), 3.5),
        ("BOTTOMPADDING", (0, 1), (-1, -2), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        # Grand Total styling (clean crisp B&W)
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
        ("LINEABOVE", (0, -1), (-1, -1), 1.4, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 1.4, colors.black),
        ("TOPPADDING", (0, -1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 5),
    ]

    # Set left alignment for name columns and center alignment for metric columns
    if two_name_cols:
        t_style.append(("ALIGN", (1, 1), (2, -2), "LEFT"))
        t_style.append(("ALIGN", (3, 1), (-1, -2), "CENTER"))
        t_style.append(("ALIGN", (1, -1), (2, -1), "LEFT"))
        t_style.append(("ALIGN", (3, -1), (-1, -1), "CENTER"))
    else:
        t_style.append(("ALIGN", (1, 1), (1, -2), "LEFT"))
        t_style.append(("ALIGN", (2, 1), (-1, -2), "CENTER"))
        t_style.append(("ALIGN", (1, -1), (1, -1), "LEFT"))
        t_style.append(("ALIGN", (2, -1), (-1, -1), "CENTER"))

    if report_mode in ("summary", "both"):
        main_table.setStyle(TableStyle(t_style))
        story.append(main_table)

    # Detailed rows if requested (mode is detailed or both)
    if report_mode in ("detailed", "both"):
        detected = analysis["detected_columns"]
        loc_col = detected["locality"] or "Locality"
        stat_col = detected["status"] or "Status"
        name_col = detected["consumer_name"] or "Consumer Name"
        mob_col = detected["mobile"] or "Mobile"
        conn_col = detected["connection_no"] or "Connection Number"
        arr_col = detected["arrears"] or "Total Arrears"

        # Styles for Detailed Report (Clean B&W, minimum 10pt font as required)
        th_center_det = ParagraphStyle(
            "THCenterDet",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.black,
        )
        th_left_det = ParagraphStyle(
            "THLeftDet",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            textColor=colors.black,
        )
        td_center_det = ParagraphStyle(
            "TDCenterDet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
        )
        td_left_det = ParagraphStyle(
            "TDLeftDet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#0f172a"),
        )
        td_arr_det = ParagraphStyle(
            "TDArrDet",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
        )
        td_tot_label = ParagraphStyle(
            "TDTotLabelDet",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#0f172a"),
        )
        td_tot_val = ParagraphStyle(
            "TDTotValDet",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
        )
        loc_header_style = ParagraphStyle(
            "AALocHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=12,
            spaceAfter=4,
            keepWithNext=False,
        )

        # Standard requested columns (excluding Locality and Sector which are in section header)
        active_detail_cols = ["Consumer Name", "Mobile", "Connection Number", "Status", "Total Arrears"]
        if detail_cols:
            clean_req = [c for c in detail_cols if c.lower() not in ("sr.", "sr", "#", "locality", "sector")]
            if clean_req:
                active_detail_cols = clean_req

        total_avail = 281 * mm
        sr_width = 16 * mm
        remain_w = total_avail - sr_width

        is_standard_5 = (active_detail_cols == ["Consumer Name", "Mobile", "Connection Number", "Status", "Total Arrears"])
        if is_standard_5:
            col_widths = [sr_width, 85 * mm, 42 * mm, 46 * mm, 36 * mm, 56 * mm]
        else:
            each_w = remain_w / max(1, len(active_detail_cols))
            col_widths = [sr_width] + [each_w] * len(active_detail_cols)

        # Header row
        header_cells = [Paragraph("<b>Sr #</b>", th_center_det)]
        for col_name in active_detail_cols:
            if "name" in col_name.lower():
                header_cells.append(Paragraph(f"<b>{col_name}</b>", th_left_det))
            elif "arrear" in col_name.lower():
                header_cells.append(Paragraph(f"<b>{col_name} (PKR)</b>", th_center_det))
            else:
                header_cells.append(Paragraph(f"<b>{col_name}</b>", th_center_det))

        for item in active_summaries:
            loc_name = item["locality"]
            grp = df[df[loc_col].astype(str).str.strip() == loc_name].copy()
            grp["_st"] = grp[stat_col].apply(classify_status)
            valid_statuses = ["Open", "Suspended"] if not include_closed else ["Open", "Suspended", "Closed"]
            grp_valid = grp[grp["_st"].isin(valid_statuses)]

            if not grp_valid.empty:
                story.append(Spacer(1, 4 * mm))
                header_html = f"<b>{loc_name}</b> &nbsp;&nbsp;<font color='#475569' size='9'>(Sector: {item.get('sector', '')})</font>"
                story.append(Paragraph(header_html, loc_header_style))

                tbl_rows = [header_cells]
                loc_tot_arr = 0.0

                for idx, (_, r) in enumerate(grp_valid.iterrows(), 1):
                    row_cells = [Paragraph(str(idx), td_center_det)]
                    for c in active_detail_cols:
                        val = str(r.get(c, "")).strip()
                        if "arrear" in c.lower():
                            amt = parse_amount(val)
                            loc_tot_arr += amt
                            row_cells.append(Paragraph(f"{amt:,.0f}", td_arr_det))
                        elif "name" in c.lower():
                            row_cells.append(Paragraph(val, td_left_det))
                        else:
                            row_cells.append(Paragraph(val, td_center_det))
                    tbl_rows.append(row_cells)

                # Total row at bottom of locality table
                tot_label = f"Total Consumers in {loc_name}: {len(grp_valid)}"
                empty_cells = [Paragraph("", td_center_det) for _ in range(len(active_detail_cols) - 1)]
                total_row_cells = [Paragraph(f"<b>{tot_label}</b>", td_tot_label)] + empty_cells + [Paragraph(f"<b>{loc_tot_arr:,.0f}</b>", td_tot_val)]
                tbl_rows.append(total_row_cells)

                det_table = Table(tbl_rows, colWidths=col_widths, repeatRows=1)
                det_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                        ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.black),
                        ("LINEABOVE", (0, 0), (-1, 0), 1.2, colors.black),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
                        ("SPAN", (0, -1), (-2, -1)),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
                        ("LINEABOVE", (0, -1), (-1, -1), 1.2, colors.black),
                        ("LINEBELOW", (0, -1), (-1, -1), 1.2, colors.black),
                        ("TOPPADDING", (0, -1), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, -1), (-1, -1), 5),
                    ])
                )
                story.append(det_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------

@arrears_analysis_bp.route("/arrears-analysis", methods=["GET", "POST"])
def arrears_analysis():
    main = _app()
    allowed_file = main.allowed_file
    ajax_error = getattr(main, "ajax_error", lambda err, code=400: ({"ok": False, "error": err}, code))
    ajax_ok = getattr(main, "ajax_ok", lambda message="", redirect_url=None: ({"ok": True, "message": message, "redirect": redirect_url}))

    if request.method == "POST":
        # -------------------------------------------------------------------
        # JSON upload: handles client-side compressed / base64 payloads to
        # bypass Vercel's 4.5MB serverless body limit for large datasets.
        # -------------------------------------------------------------------
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            act = payload.get("action", "")
            if act in ("upload_compressed", "upload_excel", "upload_data"):
                fn = secure_filename(payload.get("filename", "upload.csv"))
                if not allowed_file(fn):
                    return ajax_error(f"Unsupported file format: {fn}")

                b64_data = payload.get("data_base64") or payload.get("data_gz_base64", "")
                if not b64_data:
                    return ajax_error("No file data received.")

                try:
                    raw_bytes = base64.b64decode(b64_data)
                    if payload.get("is_gzip") or act == "upload_compressed":
                        try:
                            raw_bytes = gzip.decompress(raw_bytes)
                        except Exception:
                            pass  # Fallback if bytes were already uncompressed

                    bio = io.BytesIO(raw_bytes)
                    if fn.lower().endswith((".xlsx", ".xls")):
                        df = pd.read_excel(bio, dtype=str, keep_default_na=False)
                    else:
                        df = pd.read_csv(bio, dtype=str, keep_default_na=False)

                    df.to_csv(_working_csv(), index=False)
                    meta = {
                        "source": "Uploaded File",
                        "filename": fn,
                        "loaded_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "rows": len(df),
                    }
                    with open(_working_meta(), "w", encoding="utf-8") as fh:
                        json.dump(meta, fh, indent=2)

                    msg = f"Successfully uploaded {fn} ({len(df):,} records)."
                    return ajax_ok(message=msg, redirect_url=url_for("arrears_analysis.arrears_analysis"))
                except Exception as exc:
                    return ajax_error(f"Error parsing file: {exc}")

        action = request.form.get("action", "")

        if action == "clear":
            for p in (_working_csv(), _working_meta()):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            flash("Arrears analysis dataset cleared.", "info")
            return redirect(url_for("arrears_analysis.arrears_analysis"))

        if action == "use_handover":
            ho_csv = _handover_working_csv()
            if os.path.exists(ho_csv) and os.path.getsize(ho_csv) > 0:
                df = pd.read_csv(ho_csv, dtype=str, keep_default_na=False)
                df.to_csv(_working_csv(), index=False)
                meta = {
                    "source": "Handover Connections",
                    "filename": "handover_working.csv",
                    "loaded_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "rows": len(df),
                }
                with open(_working_meta(), "w", encoding="utf-8") as fh:
                    json.dump(meta, fh, indent=2)
                flash(f"Loaded existing Handover connections dataset ({len(df):,} rows).", "success")
            else:
                flash("No existing Handover dataset found to load.", "error")
            return redirect(url_for("arrears_analysis.arrears_analysis"))

        if action == "upload":
            file = request.files.get("csv_file")
            if not file or not file.filename:
                flash("Please choose a CSV or XLSX file.", "error")
                return redirect(url_for("arrears_analysis.arrears_analysis"))

            fn = secure_filename(file.filename)
            if not allowed_file(fn):
                flash(f"Unsupported file format: {file.filename}", "error")
                return redirect(url_for("arrears_analysis.arrears_analysis"))

            try:
                if fn.lower().endswith((".xlsx", ".xls")):
                    df = pd.read_excel(file, dtype=str, keep_default_na=False)
                else:
                    df = pd.read_csv(file, dtype=str, keep_default_na=False)

                df.to_csv(_working_csv(), index=False)
                meta = {
                    "source": "Uploaded File",
                    "filename": fn,
                    "loaded_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "rows": len(df),
                }
                with open(_working_meta(), "w", encoding="utf-8") as fh:
                    json.dump(meta, fh, indent=2)

                flash(f"Successfully uploaded {fn} ({len(df):,} records).", "success")
            except Exception as exc:
                flash(f"Error parsing file: {exc}", "error")

            return redirect(url_for("arrears_analysis.arrears_analysis"))

    # GET Request: Load dataset and perform analysis
    df, meta = load_working_dataset()
    if df is None or df.empty:
        handover_available = os.path.exists(_handover_working_csv()) and os.path.getsize(_handover_working_csv()) > 0
        return render_template(
            "arrears_analysis.html",
            has_data=False,
            meta=meta or {},
            handover_available=handover_available,
            analysis={
                "grand_total": {
                    "regular_count": 0,
                    "regular_arrears_fmt": "0",
                    "suspended_count": 0,
                    "suspended_arrears_fmt": "0",
                    "closed_count": 0,
                    "closed_arrears_fmt": "0",
                    "total_count": 0,
                    "total_arrears_fmt": "0",
                },
                "locality_summaries": [],
                "all_localities": [],
                "all_sectors": [],
                "active_localities": [],
            },
            all_sectors=[],
            sector_locality_map={},
            selected_sector="",
            selected_localities=[],
            explicit_selection=False,
            report_mode="summary",
            sort_by="arrears_desc",
            all_available_cols=[],
            selected_cols=[],
            detail_records={},
            category=request.args.get("category", "domestic").strip().lower(),
            active_page="arrears_analysis",
        )

    # Sector and Locality selection from query args
    category = request.args.get("category", "domestic").strip().lower()
    if category not in ("domestic", "commercial", "all"):
        category = "domestic"

    sort_by = request.args.get("sort", "arrears_desc").strip()
    full_analysis = compute_arrears_analysis(
        df,
        None,
        category=(category if category in ("domestic", "commercial") else ""),
        sort_by=sort_by,
    )
    all_raw_localities = full_analysis["all_localities"]
    all_sectors = full_analysis["all_sectors"]
    sector_locality_map = full_analysis["sector_locality_map"]

    selected_sector = request.args.get("sector", "").strip()
    if category == "commercial" and not selected_sector:
        selected_sector = "COMMERCIAL"

    req_localities = request.args.getlist("locality")
    explicit_selection = bool(req_localities)
    if explicit_selection:
        selected_localities = req_localities
    elif selected_sector and selected_sector in sector_locality_map:
        # Default to all localities in the chosen sector
        selected_localities = sector_locality_map[selected_sector]
    else:
        # By default: only localities with total_arrears > 0 are selected
        selected_localities = [
            s["locality"] for s in full_analysis["locality_summaries"] if s["total_arrears"] > 0
        ]

    # Report mode: 'summary', 'detailed', or 'both'
    report_mode = request.args.get("mode", "summary").strip().lower()
    if report_mode not in ("summary", "detailed", "both"):
        report_mode = "summary"

    # Column selection
    all_available_cols = get_detail_columns(df)
    req_cols = request.args.getlist("col")
    if not req_cols:
        raw_cols_str = request.args.get("cols", "")
        if raw_cols_str:
            req_cols = [c.strip() for c in raw_cols_str.split(",") if c.strip()]
    selected_cols = resolve_detail_columns(df, req_cols if req_cols else None)

    # Calculate grand total for active selected localities
    sel_set = set(selected_localities)
    selected_grand_total = {
        "regular_count": sum(s["regular_count"] for s in full_analysis["locality_summaries"] if s["locality"] in sel_set),
        "regular_arrears": sum(s["regular_arrears"] for s in full_analysis["locality_summaries"] if s["locality"] in sel_set),
        "suspended_count": sum(s["suspended_count"] for s in full_analysis["locality_summaries"] if s["locality"] in sel_set),
        "suspended_arrears": sum(s["suspended_arrears"] for s in full_analysis["locality_summaries"] if s["locality"] in sel_set),
        "closed_count": sum(s["closed_count"] for s in full_analysis["locality_summaries"] if s["locality"] in sel_set),
        "closed_arrears": sum(s["closed_arrears"] for s in full_analysis["locality_summaries"] if s["locality"] in sel_set),
        "total_count": sum(s["total_count"] for s in full_analysis["locality_summaries"] if s["locality"] in sel_set),
        "total_arrears": sum(s["total_arrears"] for s in full_analysis["locality_summaries"] if s["locality"] in sel_set),
    }
    selected_grand_total["regular_arrears_fmt"] = format_pkr(selected_grand_total["regular_arrears"])
    selected_grand_total["suspended_arrears_fmt"] = format_pkr(selected_grand_total["suspended_arrears"])
    selected_grand_total["closed_arrears_fmt"] = format_pkr(selected_grand_total["closed_arrears"])
    selected_grand_total["total_arrears_fmt"] = format_pkr(selected_grand_total["total_arrears"])

    full_analysis["grand_total"] = selected_grand_total
    full_analysis["active_localities"] = selected_localities

    inc_closed_param = request.args.get("inc_closed", "0").strip().lower()
    include_closed = inc_closed_param in ("1", "true", "yes")

    # Detailed consumer records per locality if detail or both mode
    detail_records = {}
    is_detail_limited = False
    detail_limit_count = 0
    if report_mode in ("detailed", "both"):
        detected = full_analysis["detected_columns"]
        loc_col = detected["locality"] or "Locality"
        stat_col = detected["status"] or "Status"

        df_work = df.copy()
        df_work["_st"] = df_work[stat_col].apply(classify_status)
        valid_statuses = ["Open", "Suspended"] if not include_closed else ["Open", "Suspended", "Closed"]
        df_work_valid = df_work[df_work["_st"].isin(valid_statuses)]

        # Target localities for consumer records to keep payload safely within serverless limits (< 4.5 MB)
        if explicit_selection:
            target_detail_localities = [l for l in selected_localities if l in all_raw_localities]
        elif category == "commercial":
            # All 19 commercial localities have only 250 records total - safe to render all
            target_detail_localities = [s["locality"] for s in full_analysis["locality_summaries"]]
        elif selected_sector and selected_sector in sector_locality_map:
            target_detail_localities = sector_locality_map[selected_sector]
        else:
            # Safe default for large domestic dataset: top 3 localities by arrears
            active_summaries = [s for s in full_analysis["locality_summaries"] if s["total_arrears"] > 0]
            target_detail_localities = [s["locality"] for s in active_summaries[:3]]
            is_detail_limited = (len(active_summaries) > 3)
            detail_limit_count = len(active_summaries)

        for loc_name in target_detail_localities:
            if category == "commercial":
                grp = df_work_valid[
                    (df_work_valid[loc_col].astype(str).str.strip() == loc_name)
                    & (df_work_valid["Sector"].astype(str).str.strip().str.upper() == "COMMERCIAL")
                ]
            else:
                grp = df_work_valid[df_work_valid[loc_col].astype(str).str.strip() == loc_name]

            records = []
            for _, r in grp.iterrows():
                row_dict = {}
                for c in all_available_cols:
                    val = str(r.get(c, "")).strip()
                    if "arrear" in c.lower():
                        val = f"{parse_amount(val):,.0f}"
                    row_dict[c] = val
                records.append(row_dict)
            detail_records[loc_name] = records

    handover_available = os.path.exists(_handover_working_csv()) and os.path.getsize(_handover_working_csv()) > 0

    return render_template(
        "arrears_analysis.html",
        has_data=True,
        meta=meta,
        handover_available=handover_available,
        analysis=full_analysis,
        all_sectors=all_sectors,
        sector_locality_map=sector_locality_map,
        selected_sector=selected_sector,
        selected_localities=selected_localities,
        explicit_selection=explicit_selection,
        report_mode=report_mode,
        sort_by=sort_by,
        all_available_cols=all_available_cols,
        selected_cols=selected_cols,
        detail_records=detail_records,
        category=category,
        is_detail_limited=is_detail_limited,
        detail_limit_count=detail_limit_count,
        active_page="arrears_analysis",
    )


@arrears_analysis_bp.route("/arrears-analysis/print")
def arrears_analysis_print():
    """Printable sheet styled for A4 landscape."""
    df, meta = load_working_dataset()
    if df is None or df.empty:
        flash("No dataset loaded to print.", "error")
        return redirect(url_for("arrears_analysis.arrears_analysis"))

    sort_by = request.args.get("sort", "arrears_desc").strip()

    category = request.args.get("category", "").strip().lower()
    req_sectors = request.args.getlist("sector")
    if not req_sectors:
        raw_sec = request.args.get("sector", "").strip()
        if raw_sec:
            req_sectors = [s.strip() for s in raw_sec.split(",") if s.strip()]

    if not category:
        if req_sectors and all("commercial" in s.lower() for s in req_sectors):
            category = "commercial"
        elif req_sectors:
            category = ""
        else:
            category = "domestic"

    full_res = compute_arrears_analysis(df, None, category=category, sort_by=sort_by)
    all_raw_localities = full_res["all_localities"]
    sector_locality_map = full_res.get("sector_locality_map", {})

    req_localities = request.args.getlist("locality")
    if not req_localities:
        raw_loc = request.args.get("locality", "").strip()
        if raw_loc:
            req_localities = [l.strip() for l in raw_loc.split(",") if l.strip()]

    inc_closed_param = request.args.get("inc_closed", "0").strip()
    include_closed = inc_closed_param in ("1", "true", "yes")

    inc_zero_param = request.args.get("inc_zero", "0").strip()
    include_zero = inc_zero_param in ("1", "true", "yes")

    if req_localities:
        selected_localities = req_localities
    elif req_sectors:
        selected_localities = []
        for sec in req_sectors:
            selected_localities.extend(sector_locality_map.get(sec, []))
        seen = set()
        selected_localities = [x for x in selected_localities if not (x in seen or seen.add(x))]
        if not include_zero:
            selected_localities = [
                loc for loc in selected_localities
                if any(s["locality"] == loc and not is_zero_summary(s, include_closed) for s in full_res["locality_summaries"])
            ]
    else:
        if category == "commercial":
            if not include_zero:
                selected_localities = [
                    s["locality"] for s in full_res["locality_summaries"]
                    if not is_zero_summary(s, include_closed)
                ]
            else:
                selected_localities = [s["locality"] for s in full_res["locality_summaries"]]
        else:
            if not include_zero:
                selected_localities = [
                    s["locality"] for s in full_res["locality_summaries"]
                    if not is_zero_summary(s, include_closed) and s["total_arrears"] > 0
                ]
            else:
                selected_localities = [s["locality"] for s in full_res["locality_summaries"]]

    selected_sector_label = ", ".join(req_sectors) if len(req_sectors) <= 2 else f"{len(req_sectors)} Sectors"

    report_mode = request.args.get("mode", "summary").strip().lower()
    if report_mode not in ("summary", "detailed", "both"):
        report_mode = "summary"

    raw_cols_str = request.args.get("cols", "")
    req_cols = [c.strip() for c in raw_cols_str.split(",") if c.strip()] if raw_cols_str else request.args.getlist("col")
    selected_cols = resolve_detail_columns(df, req_cols if req_cols else None)

    show_loc = request.args.get("show_loc", "1").strip() not in ("0", "false", "no")
    show_sec = request.args.get("show_sec", "1").strip() not in ("0", "false", "no")
    if not show_loc and not show_sec:
        show_loc = True
    col_order = request.args.get("order", "loc_first").strip().lower()
    if col_order not in ("loc_first", "sec_first"):
        col_order = "loc_first"

    analysis = compute_arrears_analysis(df, selected_localities, sectors=req_sectors if req_sectors else None, category=category, sort_by=sort_by)
    if not include_zero:
        analysis["locality_summaries"] = [
            s for s in analysis["locality_summaries"]
            if not is_zero_summary(s, include_closed)
        ]
        analysis["active_localities"] = [s["locality"] for s in analysis["locality_summaries"]]

    detail_records = {}
    if report_mode in ("detailed", "both"):
        detected = analysis["detected_columns"]
        loc_col = detected["locality"] or "Locality"
        stat_col = detected["status"] or "Status"

        df_work = df.copy()
        if category == "commercial":
            df_work = df_work[df_work["Sector"].astype(str).str.upper() == "COMMERCIAL"].copy()
            df_work = df_work[~df_work[loc_col].astype(str).str.upper().str.contains("COLONY", na=False)].copy()
        elif category == "domestic":
            df_work = df_work[df_work["Sector"].astype(str).str.upper() != "COMMERCIAL"].copy()

        df_work["_st"] = df_work[stat_col].apply(classify_status)
        valid_statuses = ["Open", "Suspended"] if not include_closed else ["Open", "Suspended", "Closed"]
        df_work_valid = df_work[df_work["_st"].isin(valid_statuses)]

        for loc_name in analysis["active_localities"]:
            grp = df_work_valid[df_work_valid[loc_col].astype(str).str.strip() == loc_name]
            records = []
            for _, r in grp.iterrows():
                row_dict = {}
                for c in selected_cols:
                    val = str(r.get(c, "")).strip()
                    if "arrear" in c.lower():
                        val = f"{parse_amount(val):,.0f}"
                    row_dict[c] = val
                records.append(row_dict)
            detail_records[loc_name] = records

    return render_template(
        "arrears_analysis_print.html",
        meta=meta,
        analysis=analysis,
        selected_sector=selected_sector_label,
        category=category,
        report_mode=report_mode,
        selected_cols=selected_cols,
        detail_records=detail_records,
        include_closed=include_closed,
        include_zero=include_zero,
        show_locality=show_loc,
        show_sector=show_sec,
        order=col_order,
        printed_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )


@arrears_analysis_bp.route("/arrears-analysis/export/<fmt_type>")
def export_arrears_analysis(fmt_type: str):
    """Export the report as PDF, Excel (XLSX), or CSV."""
    df, _ = load_working_dataset()
    if df is None or df.empty:
        flash("No dataset loaded to export.", "error")
        return redirect(url_for("arrears_analysis.arrears_analysis"))

    sort_by = request.args.get("sort", "arrears_desc").strip()

    category = request.args.get("category", "").strip().lower()
    req_sectors = request.args.getlist("sector")
    if not req_sectors:
        raw_sec = request.args.get("sector", "").strip()
        if raw_sec:
            req_sectors = [s.strip() for s in raw_sec.split(",") if s.strip()]

    if not category:
        if req_sectors and all("commercial" in s.lower() for s in req_sectors):
            category = "commercial"
        elif req_sectors:
            category = ""
        else:
            category = "domestic"

    full_res = compute_arrears_analysis(df, None, category=category, sort_by=sort_by)
    all_raw_localities = full_res["all_localities"]
    sector_locality_map = full_res.get("sector_locality_map", {})

    req_localities = request.args.getlist("locality")
    if not req_localities:
        raw_loc = request.args.get("locality", "").strip()
        if raw_loc:
            req_localities = [l.strip() for l in raw_loc.split(",") if l.strip()]

    if req_localities:
        selected_localities = req_localities
    elif req_sectors:
        selected_localities = []
        for sec in req_sectors:
            selected_localities.extend(sector_locality_map.get(sec, []))
        seen = set()
        selected_localities = [x for x in selected_localities if not (x in seen or seen.add(x))]
    else:
        if category == "commercial":
            selected_localities = [s["locality"] for s in full_res["locality_summaries"]]
        else:
            selected_localities = [
                s["locality"] for s in full_res["locality_summaries"] if s["total_arrears"] > 0
            ]

    selected_sector_label = ", ".join(req_sectors) if len(req_sectors) <= 2 else f"{len(req_sectors)} Sectors"

    report_mode = request.args.get("mode", "summary").strip().lower()
    if report_mode not in ("summary", "detailed", "both"):
        report_mode = "summary"

    raw_cols_str = request.args.get("cols", "")
    req_cols = [c.strip() for c in raw_cols_str.split(",") if c.strip()] if raw_cols_str else request.args.getlist("col")
    selected_cols = resolve_detail_columns(df, req_cols if req_cols else None)

    inc_closed_param = request.args.get("inc_closed", "0").strip()
    include_closed = inc_closed_param in ("1", "true", "yes")

    inc_zero_param = request.args.get("inc_zero", "0").strip()
    include_zero = inc_zero_param in ("1", "true", "yes")

    if req_localities:
        selected_localities = req_localities
    elif req_sectors:
        selected_localities = []
        for sec in req_sectors:
            selected_localities.extend(sector_locality_map.get(sec, []))
        seen = set()
        selected_localities = [x for x in selected_localities if not (x in seen or seen.add(x))]
        if not include_zero:
            selected_localities = [
                loc for loc in selected_localities
                if any(s["locality"] == loc and not is_zero_summary(s, include_closed) for s in full_res["locality_summaries"])
            ]
    else:
        if category == "commercial":
            if not include_zero:
                selected_localities = [
                    s["locality"] for s in full_res["locality_summaries"]
                    if not is_zero_summary(s, include_closed)
                ]
            else:
                selected_localities = [s["locality"] for s in full_res["locality_summaries"]]
        else:
            if not include_zero:
                selected_localities = [
                    s["locality"] for s in full_res["locality_summaries"]
                    if not is_zero_summary(s, include_closed) and s["total_arrears"] > 0
                ]
            else:
                selected_localities = [s["locality"] for s in full_res["locality_summaries"]]

    selected_sector_label = ", ".join(req_sectors) if len(req_sectors) <= 2 else f"{len(req_sectors)} Sectors"

    report_mode = request.args.get("mode", "summary").strip().lower()
    if report_mode not in ("summary", "detailed", "both"):
        report_mode = "summary"

    raw_cols_str = request.args.get("cols", "")
    req_cols = [c.strip() for c in raw_cols_str.split(",") if c.strip()] if raw_cols_str else request.args.getlist("col")
    selected_cols = resolve_detail_columns(df, req_cols if req_cols else None)

    show_loc = request.args.get("show_loc", "1").strip() not in ("0", "false", "no")
    show_sec = request.args.get("show_sec", "1").strip() not in ("0", "false", "no")
    if not show_loc and not show_sec:
        show_loc = True
    col_order = request.args.get("order", "loc_first").strip().lower()
    if col_order not in ("loc_first", "sec_first"):
        col_order = "loc_first"

    analysis = compute_arrears_analysis(
        df,
        selected_localities,
        sectors=req_sectors if req_sectors else None,
        category=category,
        sort_by=sort_by,
    )
    if not include_zero:
        analysis["locality_summaries"] = [
            s for s in analysis["locality_summaries"]
            if not is_zero_summary(s, include_closed)
        ]
        analysis["active_localities"] = [s["locality"] for s in analysis["locality_summaries"]]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    if category == "commercial":
        slug = f"Commercial_Sector_Arrears_{report_mode}_{timestamp}"
    elif category == "domestic":
        slug = f"Domestic_Arrears_{report_mode}_{timestamp}"
    elif selected_sector_label:
        sec_slug = "".join(c if c.isalnum() else "_" for c in selected_sector_label)[:20]
        slug = f"Arrears_{sec_slug}_{report_mode}_{timestamp}"
    else:
        slug = f"Arrears_Analysis_{report_mode}_{timestamp}"

    # 1. PDF Export
    if fmt_type == "pdf":
        pdf_bytes = build_arrears_pdf(
            df,
            analysis,
            report_mode,
            selected_cols,
            selected_sector=selected_sector_label,
            category=category,
            include_closed=include_closed,
            show_locality=show_loc,
            show_sector=show_sec,
            order=col_order,
            include_zero=include_zero,
        )
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={slug}.pdf"},
        )

    # 2. CSV Export
    if fmt_type == "csv":
        out = io.StringIO()
        writer = csv.writer(out)

        # Write Summary Table
        writer.writerow(["WATER SUPPLY CONSUMER ARREARS - SUMMARY REPORT", f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}"])
        writer.writerow([])

        # Determine name columns
        if show_loc and show_sec:
            name_cols = ["Sector", "Locality"] if col_order == "sec_first" else ["Locality", "Sector"]
        elif show_sec:
            name_cols = ["Sector"]
        else:
            name_cols = ["Locality"]

        if include_closed:
            headers = name_cols + [
                "Regular Connections", "Regular Arrears (PKR)",
                "Suspended Connections", "Suspended Arrears (PKR)", "Closed Connections",
                "Closed Arrears (PKR)", "Total Connections", "Total Arrears (PKR)",
            ]
        else:
            headers = name_cols + [
                "Regular Connections", "Regular Arrears (PKR)",
                "Suspended Connections", "Suspended Arrears (PKR)", "Total Connections", "Total Arrears (PKR)",
            ]
        writer.writerow(headers)

        sum_reg_c = sum(s["regular_count"] for s in analysis["locality_summaries"])
        sum_reg_a = sum(s["regular_arrears"] for s in analysis["locality_summaries"])
        sum_sus_c = sum(s["suspended_count"] for s in analysis["locality_summaries"])
        sum_sus_a = sum(s["suspended_arrears"] for s in analysis["locality_summaries"])
        sum_cls_c = sum(s["closed_count"] for s in analysis["locality_summaries"])
        sum_cls_a = sum(s["closed_arrears"] for s in analysis["locality_summaries"])

        for s in analysis["locality_summaries"]:
            tot_c = s["regular_count"] + s["suspended_count"] + (s["closed_count"] if include_closed else 0)
            tot_a = s["regular_arrears"] + s["suspended_arrears"] + (s["closed_arrears"] if include_closed else 0)
            
            if show_loc and show_sec:
                row_names = [s["sector"], s["locality"]] if col_order == "sec_first" else [s["locality"], s["sector"]]
            elif show_sec:
                row_names = [s["sector"]]
            else:
                row_names = [s["locality"]]

            if include_closed:
                writer.writerow(row_names + [
                    s["regular_count"], s["regular_arrears"],
                    s["suspended_count"], s["suspended_arrears"], s["closed_count"],
                    s["closed_arrears"], tot_c, tot_a,
                ])
            else:
                writer.writerow(row_names + [
                    s["regular_count"], s["regular_arrears"],
                    s["suspended_count"], s["suspended_arrears"], tot_c, tot_a,
                ])

        tot_sum_c = sum_reg_c + sum_sus_c + (sum_cls_c if include_closed else 0)
        tot_sum_a = sum_reg_a + sum_sus_a + (sum_cls_a if include_closed else 0)
        grand_names = ["GRAND TOTAL", "-"] if (show_loc and show_sec) else ["GRAND TOTAL"]
        if include_closed:
            writer.writerow(grand_names + [
                sum_reg_c, sum_reg_a, sum_sus_c, sum_sus_a,
                sum_cls_c, sum_cls_a, tot_sum_c, tot_sum_a,
            ])
        else:
            writer.writerow(grand_names + [
                sum_reg_c, sum_reg_a, sum_sus_c, sum_sus_a,
                tot_sum_c, tot_sum_a,
            ])

        # If Detailed mode requested, append detail records
        if report_mode in ("detailed", "both"):
            writer.writerow([])
            writer.writerow(["DETAILED CONSUMER ARREARS RECORDS"])
            writer.writerow(["Locality"] + selected_cols)
            detected = analysis["detected_columns"]
            loc_col = detected["locality"] or "Locality"
            stat_col = detected["status"] or "Status"

            df_work = df.copy()
            if category == "commercial":
                df_work = df_work[df_work["Sector"].astype(str).str.upper() == "COMMERCIAL"].copy()
                df_work = df_work[~df_work[loc_col].astype(str).str.upper().str.contains("COLONY", na=False)].copy()
            elif category == "domestic":
                df_work = df_work[df_work["Sector"].astype(str).str.upper() != "COMMERCIAL"].copy()

            df_work["_st"] = df_work[stat_col].apply(classify_status)
            valid_statuses = ["Open", "Suspended"] if not include_closed else ["Open", "Suspended", "Closed"]
            df_work_valid = df_work[df_work["_st"].isin(valid_statuses)]

            for loc_name in analysis["active_localities"]:
                grp = df_work_valid[df_work_valid[loc_col].astype(str).str.strip() == loc_name]
                for _, r in grp.iterrows():
                    writer.writerow([loc_name] + [r.get(c, "") for c in selected_cols])

        return Response(
            out.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={slug}.csv"},
        )

    # 3. Excel Export
    if fmt_type == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            sum_rows = []
            sum_reg_c = sum(s["regular_count"] for s in analysis["locality_summaries"])
            sum_reg_a = sum(s["regular_arrears"] for s in analysis["locality_summaries"])
            sum_sus_c = sum(s["suspended_count"] for s in analysis["locality_summaries"])
            sum_sus_a = sum(s["suspended_arrears"] for s in analysis["locality_summaries"])
            sum_cls_c = sum(s["closed_count"] for s in analysis["locality_summaries"])
            sum_cls_a = sum(s["closed_arrears"] for s in analysis["locality_summaries"])

            for s in analysis["locality_summaries"]:
                tot_c = s["regular_count"] + s["suspended_count"] + (s["closed_count"] if include_closed else 0)
                tot_a = s["regular_arrears"] + s["suspended_arrears"] + (s["closed_arrears"] if include_closed else 0)
                row_dict = {}
                if show_loc and show_sec:
                    if col_order == "sec_first":
                        row_dict["Sector"] = s["sector"]
                        row_dict["Locality"] = s["locality"]
                    else:
                        row_dict["Locality"] = s["locality"]
                        row_dict["Sector"] = s["sector"]
                elif show_sec:
                    row_dict["Sector"] = s["sector"]
                else:
                    row_dict["Locality"] = s["locality"]

                row_dict["Regular Connections"] = s["regular_count"]
                row_dict["Regular Arrears (PKR)"] = s["regular_arrears"]
                row_dict["Suspended Connections"] = s["suspended_count"]
                row_dict["Suspended Arrears (PKR)"] = s["suspended_arrears"]
                if include_closed:
                    row_dict["Closed Connections"] = s["closed_count"]
                    row_dict["Closed Arrears (PKR)"] = s["closed_arrears"]
                row_dict["Total Connections"] = tot_c
                row_dict["Total Arrears (PKR)"] = tot_a
                sum_rows.append(row_dict)

            tot_sum_c = sum_reg_c + sum_sus_c + (sum_cls_c if include_closed else 0)
            tot_sum_a = sum_reg_a + sum_sus_a + (sum_cls_a if include_closed else 0)
            grand_row = {}
            if show_loc and show_sec:
                if col_order == "sec_first":
                    grand_row["Sector"] = "GRAND TOTAL"
                    grand_row["Locality"] = "-"
                else:
                    grand_row["Locality"] = "GRAND TOTAL"
                    grand_row["Sector"] = "-"
            elif show_sec:
                grand_row["Sector"] = "GRAND TOTAL"
            else:
                grand_row["Locality"] = "GRAND TOTAL"

            grand_row["Regular Connections"] = sum_reg_c
            grand_row["Regular Arrears (PKR)"] = sum_reg_a
            grand_row["Suspended Connections"] = sum_sus_c
            grand_row["Suspended Arrears (PKR)"] = sum_sus_a
            if include_closed:
                grand_row["Closed Connections"] = sum_cls_c
                grand_row["Closed Arrears (PKR)"] = sum_cls_a
            grand_row["Total Connections"] = tot_sum_c
            grand_row["Total Arrears (PKR)"] = tot_sum_a
            sum_rows.append(grand_row)

            pd.DataFrame(sum_rows).to_excel(writer, sheet_name="Arrears Summary", index=False)

            if report_mode in ("detailed", "both"):
                det_rows = []
                detected = analysis["detected_columns"]
                loc_col = detected["locality"] or "Locality"
                stat_col = detected["status"] or "Status"

                df_work = df.copy()
                if category == "commercial":
                    df_work = df_work[df_work["Sector"].astype(str).str.upper() == "COMMERCIAL"].copy()
                    df_work = df_work[~df_work[loc_col].astype(str).str.upper().str.contains("COLONY", na=False)].copy()
                elif category == "domestic":
                    df_work = df_work[df_work["Sector"].astype(str).str.upper() != "COMMERCIAL"].copy()

                df_work["_st"] = df_work[stat_col].apply(classify_status)
                valid_statuses = ["Open", "Suspended"] if not include_closed else ["Open", "Suspended", "Closed"]
                df_work_valid = df_work[df_work["_st"].isin(valid_statuses)]

                for loc_name in analysis["active_localities"]:
                    grp = df_work_valid[df_work_valid[loc_col].astype(str).str.strip() == loc_name]
                    for _, r in grp.iterrows():
                        d_row = {"Locality": loc_name}
                        for c in selected_cols:
                            d_row[c] = r.get(c, "")
                        det_rows.append(d_row)
                if det_rows:
                    pd.DataFrame(det_rows).to_excel(writer, sheet_name="Consumer Details", index=False)

        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={slug}.xlsx"},
        )

    flash(f"Unsupported export format: {fmt_type}", "error")
    return redirect(url_for("arrears_analysis.arrears_analysis"))
