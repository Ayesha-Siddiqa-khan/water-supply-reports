import csv
import io
import json
import zipfile
import os
import re
import shutil
import sqlite3
import sys
import threading
import webbrowser
from datetime import datetime

import pandas as pd
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    KeepTogether,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from werkzeug.utils import secure_filename

def resource_path(*parts: str) -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, *parts)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts)


def app_data_dir() -> str:
    if os.environ.get("VERCEL") == "1":
        return os.path.join("/tmp", "water-supply-report")
    if getattr(sys, "frozen", False):
        return os.path.abspath(os.path.dirname(sys.executable))
    return os.path.abspath(os.path.dirname(__file__))


BASE_DIR = app_data_dir()
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
RESULTS_CACHE = os.path.join(UPLOAD_FOLDER, "last_results.json")
SAVED_DASHBOARD_CSV = os.path.join(UPLOAD_FOLDER, "saved_dashboard_data.csv")
SAVED_DASHBOARD_META = os.path.join(UPLOAD_FOLDER, "saved_dashboard_meta.json")
BILL_LIST_DB = os.path.join(BASE_DIR, "bill_list.sqlite3")
SEED_ASSIGNMENTS_JSON = resource_path("seed", "staff_assignments.json")
SEED_ASSIGNMENTS_CSV = resource_path("seed", "staff_assignments.csv")
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
app.secret_key = "dev-secret"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(BILL_LIST_DB):
    bundled_db = resource_path("bill_list.sqlite3")
    if os.path.exists(bundled_db):
        shutil.copy2(bundled_db, BILL_LIST_DB)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STAFF_PAIRS = {
    "MUHAMMAD ILYAS": "MUHAMMAD ILYAS\nMUHAMMAD NAEEM",
    "MUHAMMAD IRFAN": "MUHAMMAD IRFAN\nZULFIQAR",
    "MUHAMMAD KHALID": "MUHAMMAD KHALID\nMUHAMMAD NAZAR",
    "MUHAMMAD KASHIF": "MUHAMMAD KASHIF\nMUHAMMAD SHAHID",
    "TAUSEEF": "TAUSEEF\nGOSHI IBRAHIM",
}

AUTO_ASSIGNMENT_RULES = [
    {
        "sector": "29 - Mahboob Colony (SHARQI)",
        "locality": "02 - Mehboob Colony SHARQI Zone B",
        "connection_min": "12020001",
        "connection_max": "12020560",
        "staff_name": "MUHAMMAD KASHIF",
    },
    {
        "sector": "29 - Mahboob Colony (SHARQI)",
        "locality": "02 - Mehboob Colony SHARQI Zone B",
        "connection_min": "12020561",
        "connection_max": None,
        "staff_name": "MUHAMMAD ILYAS",
    },
    {
        "sector": "51 - NoorPura",
        "locality": "01 - Noor Pura Zone C",
        "connection_min": "04010001",
        "connection_max": "04010428",
        "staff_name": "MUHAMMAD MURTAZA",
    },
    {
        "sector": "51 - NoorPura",
        "locality": "01 - Noor Pura Zone C",
        "connection_min": "04010429",
        "connection_max": None,
        "staff_name": "ABDUL LATIF",
    },
]

_AAR_SECTOR = AUTO_ASSIGNMENT_RULES[0]["sector"]
_AAR_LOCALITY = AUTO_ASSIGNMENT_RULES[0]["locality"]

def _normalize_sector_locality(value: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"^\d+\s*[-–—]\s*", "", text)
    text = text.replace("mehbob", "mehboob")
    text = text.replace("noorpura", "noor pura")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_staff_name(name: str) -> str:
    return " ".join(name.split()).upper()

def _levenshtein(a: str, b: str) -> int:
    n, m = len(a), len(b)
    if n < m:
        a, b = b, a
        n, m = m, n
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] * (m + 1)
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[m]

def _closest_staff_key(name: str, max_dist: int = 2):
    if not name:
        return None
    best_key = None
    best_dist = max_dist + 1
    for key in STAFF_PAIRS:
        d = _levenshtein(name, key)
        if d < best_dist:
            best_dist = d
            best_key = key
    return best_key

def fmt_staff_name(name: str) -> str:
    """Return display name: paired staff on separate lines, else as-is."""
    if not name:
        return name
    norm = _normalize_staff_name(name)
    key = _closest_staff_key(norm)
    if key:
        return STAFF_PAIRS[key]
    return name.replace(" / ", "\n")

def fmt_staff_name_html(name: str) -> str:
    """Like fmt_staff_name but returns HTML with <br> for display."""
    if not name:
        return name
    norm = _normalize_staff_name(name)
    key = _closest_staff_key(norm)
    display = STAFF_PAIRS.get(key) if key else name.replace(" / ", "\n")
    from markupsafe import Markup
    return Markup(display.replace("\n", "<br>"))

app.jinja_env.filters["staff_name"] = fmt_staff_name
app.jinja_env.filters["staff_name_html"] = fmt_staff_name_html

def allowed_file(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS


def read_dataframe(path: str) -> pd.DataFrame:
    _, ext = os.path.splitext(path)
    if ext.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def read_uploaded_dataframe(file) -> pd.DataFrame:
    _, ext = os.path.splitext(file.filename)
    if ext.lower() == ".csv":
        return pd.read_csv(file)
    return pd.read_excel(file)


def normalize_column_name(name: str) -> str:
    name = str(name).strip().lower().replace("_", " ")
    return " ".join(name.split())


def normalize_sector_key(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\bprivate\b|\bsociety\b|\bphase\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


SECTOR_VALUE_DELIMITER = "|||"


def split_sector_values(values: list[str]) -> list[str]:
    sectors: list[str] = []
    for value in values:
        for sector in str(value).split(SECTOR_VALUE_DELIMITER):
            sector = sector.strip()
            if sector:
                sectors.append(sector)
    return sorted(set(sectors))


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_column_name(col) for col in df.columns]
    return df


def _dedupe_value(value) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if not text:
        return ""
    compact_number = text.replace(",", "")
    numeric_chars = compact_number.replace(".", "", 1).replace("-", "", 1)
    if numeric_chars.isdigit() and len(numeric_chars) <= 15:
        number = pd.to_numeric(pd.Series([compact_number]), errors="coerce").iloc[0]
        if pd.notna(number):
            return str(int(number)) if float(number).is_integer() else f"{float(number):.6f}".rstrip("0").rstrip(".")
    parsed_date = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.notna(parsed_date):
        return parsed_date.strftime("%Y-%m-%d")
    return " ".join(text.lower().split())


def drop_duplicate_bills(df: pd.DataFrame) -> tuple[pd.DataFrame, int, list[str]]:
    """Remove duplicate uploaded bills without collapsing different bills for one connection."""
    if df.empty:
        return df, 0, []

    normalized_columns = [normalize_column_name(col) for col in df.columns]
    column_lookup = dict(zip(normalized_columns, df.columns))
    key_candidates = [
        ["bill no"],
        ["reference no", "due date", "total bill"],
        ["reference no", "received date", "amount received"],
        ["connection no", "due date", "total bill"],
        ["connection no", "received date", "amount received"],
    ]

    key_columns = []
    for candidate in key_candidates:
        if all(col in column_lookup for col in candidate):
            key_columns = [column_lookup[col] for col in candidate]
            break

    if not key_columns:
        key_columns = list(df.columns)

    key_frame = df[key_columns].apply(lambda col: col.map(_dedupe_value))
    complete_key = key_frame.ne("").all(axis=1)
    duplicate_mask = pd.Series(False, index=df.index)

    if complete_key.any():
        duplicate_mask.loc[complete_key] = key_frame.loc[complete_key].duplicated(keep="last")

    if (~complete_key).any():
        full_row_key = df.apply(lambda col: col.map(_dedupe_value))
        duplicate_mask.loc[~complete_key] = full_row_key.loc[~complete_key].duplicated(keep="last")

    deduped = df.loc[~duplicate_mask].copy()
    return deduped, int(duplicate_mask.sum()), [normalize_column_name(col) for col in key_columns]


def pick_column(columns: list[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def fmt(value) -> str:
    if value is None:
        return "0"
    return f"{value:,.0f}"


def format_mobile(value) -> str:
    if value is None or value == "" or value == 0 or value == "0" or value == "0.0":
        return "-"
    mobile = str(value).strip()
    mobile = mobile.replace(".0", "")
    mobile = re.sub(r"\D", "", mobile)
    if not mobile or mobile == "0":
        return "-"
    if len(mobile) == 10 and mobile.startswith("3"):
        mobile = "0" + mobile
    if len(mobile) == 12 and mobile.startswith("92"):
        mobile = "0" + mobile[2:]
    return mobile


def parse_number(value) -> float:
    if value is None or pd.isna(value):
        return 0.0
    number = pd.to_numeric(pd.Series([str(value).replace(",", "").strip()]), errors="coerce").iloc[0]
    return float(number) if pd.notna(number) else 0.0


def format_fiscal_month(period: pd.Period) -> str:
    month_name = period.strftime("%B")
    fiscal_year = period.year + 1 if period.month >= 7 else period.year
    return f"{month_name} {str(fiscal_year)[-2:]}"


def format_calendar_month(period: pd.Period) -> str:
    return f"{period.strftime('%B')} {str(period.year)[-2:]}"


def fiscal_label_to_calendar_label(label: str) -> str:
    try:
        month_name, year_suffix = str(label).rsplit(" ", 1)
        month_num = datetime.strptime(month_name, "%B").month
        year = 2000 + int(year_suffix)
    except (TypeError, ValueError):
        return str(label)
    if month_num >= 7:
        year -= 1
    return f"{month_name} {str(year)[-2:]}"


def fiscal_label_to_calendar_full_label(label: str) -> str:
    short_label = fiscal_label_to_calendar_label(label)
    try:
        month_name, year_suffix = short_label.rsplit(" ", 1)
        return f"{month_name} {2000 + int(year_suffix)}"
    except (TypeError, ValueError):
        return str(label)


def format_report_date(value) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return str(value or "")
    return parsed.strftime("%d-%m-%Y")


def remove_pdf_column(headers: list[str], rows: list[list], column_name: str, grand: list | None = None):
    if column_name not in headers:
        return headers, rows, grand
    remove_idx = headers.index(column_name)
    pdf_headers = [value for idx, value in enumerate(headers) if idx != remove_idx]
    pdf_rows = [
        [value for idx, value in enumerate(row) if idx != remove_idx]
        for row in rows
    ]
    pdf_grand = None
    if grand is not None:
        pdf_grand = [value for idx, value in enumerate(grand) if idx != remove_idx]
    return pdf_headers, pdf_rows, pdf_grand


def clean_cell(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def match_key(value) -> str:
    return re.sub(r"\s+", " ", clean_cell(value)).casefold()


# ---------------------------------------------------------------------------
# Date parsing (DD-MM swap fix)
# ---------------------------------------------------------------------------

def swap_day_month(dt):
    """Swap day and month of a datetime to fix Excel DD-MM misinterpretation."""
    if pd.isna(dt):
        return pd.NaT
    try:
        if 1 <= dt.day <= 12:
            return dt.replace(month=dt.day, day=dt.month)
        return dt
    except ValueError:
        return pd.NaT


def parse_received_dates(series: pd.Series) -> pd.Series:
    """Parse received dates handling mixed formats and Excel DD-MM swap issues."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.apply(swap_day_month)

    results = []
    for val in series:
        if pd.isna(val):
            results.append(pd.NaT)
        elif isinstance(val, (pd.Timestamp, datetime)):
            results.append(swap_day_month(val))
        else:
            str_val = str(val).strip()
            parsed = pd.to_datetime(str_val, errors="coerce", format="%d/%m/%Y", dayfirst=True)
            if pd.isna(parsed):
                parsed = pd.to_datetime(str_val, errors="coerce", format="%d/%m/%y", dayfirst=True)
            if pd.isna(parsed):
                parsed = pd.to_datetime(str_val, errors="coerce", dayfirst=True)
            results.append(parsed)
    return pd.Series(results, index=series.index, dtype="datetime64[ns]")


def get_fiscal_window() -> tuple[pd.Period, pd.Period]:
    current_period = pd.Period(datetime.now(), freq="M")
    start_year = current_period.year if current_period.month >= 7 else current_period.year - 1
    fiscal_start = pd.Period(year=start_year, month=7, freq="M")
    return fiscal_start, current_period


# ---------------------------------------------------------------------------
# Data builders
# ---------------------------------------------------------------------------

def build_daily_rows(dates: pd.Series, amounts: pd.Series | None, arrears: pd.Series | None) -> list[dict]:
    metric_df = pd.DataFrame({"date": dates})
    if amounts is not None:
        metric_df["amount"] = amounts.reindex(dates.index).fillna(0)
    if arrears is not None:
        metric_df["arrears"] = arrears.reindex(dates.index).fillna(0)
    # Filter to fiscal window
    fiscal_start, current_period = get_fiscal_window()
    fs_date = fiscal_start.start_time.date()
    cp_date = current_period.end_time.date()
    metric_df = metric_df[(metric_df["date"].dt.date >= fs_date) & (metric_df["date"].dt.date <= cp_date)]
    if metric_df.empty:
        return []
    grouped = metric_df.groupby(metric_df["date"].dt.date).agg(
        count=("date", "size"),
        **({} if amounts is None else {"amount": ("amount", "sum")}),
        **({} if arrears is None else {"arrears": ("arrears", "sum")}),
    ).sort_index()
    rows = []
    for label, row in grouped.iterrows():
        item = {"label": label.strftime("%d-%m-%Y"), "count": int(row["count"])}
        if "amount" in row:
            item["amount_total"] = float(row["amount"])
        if "arrears" in row:
            item["arrears_total"] = float(row["arrears"])
        rows.append(item)
    return rows


def build_monthly_rows(dates, amounts, arrears=None):
    metric_df = pd.DataFrame({"date": dates})
    if amounts is not None:
        metric_df["amount"] = amounts.reindex(dates.index).fillna(0)
    if arrears is not None:
        metric_df["arrears"] = arrears.reindex(dates.index).fillna(0)
    agg_dict = {"count": ("date", "size")}
    if amounts is not None:
        agg_dict["amount"] = ("amount", "sum")
    if arrears is not None:
        agg_dict["arrears"] = ("arrears", "sum")
    grouped = metric_df.groupby(metric_df["date"].dt.to_period("M")).agg(**agg_dict).sort_index()
    fiscal_start, current_period = get_fiscal_window()
    grouped = grouped.loc[(grouped.index >= fiscal_start) & (grouped.index <= current_period)]
    rows = []
    for label, row in grouped.iterrows():
        item = {"label": format_fiscal_month(label), "count": int(row["count"])}
        if "amount" in row:
            item["amount_total"] = float(row["amount"])
        if "arrears" in row:
            item["arrears_total"] = float(row["arrears"])
        rows.append(item)
    return rows


def build_commercial_mask(df: pd.DataFrame) -> pd.Series:
    columns = list(df.columns)
    commercial_cols = [
        col
        for col in [
            pick_column(columns, ["connection type", "bill type", "type"]),
            pick_column(columns, ["sector"]),
        ]
        if col
    ]
    if not commercial_cols:
        return pd.Series(False, index=df.index)
    mask = pd.Series(False, index=df.index)
    for col in commercial_cols:
        mask = mask | df[col].astype(str).str.lower().str.contains("commercial", na=False)
    return mask


def build_commercial_rows(df: pd.DataFrame, dates: pd.Series, amount_col: str | None, arrears_col: str | None):
    """Build commercial sector breakdown by locality — total and month-wise."""
    locality_col = pick_column(list(df.columns), ["locality"])
    if not locality_col:
        return None, None

    mask = build_commercial_mask(df)
    comm = df[mask].copy()
    if comm.empty:
        return [], []

    comm_dates = dates.reindex(comm.index).dropna()
    comm = comm.loc[comm_dates.index]
    comm_dates = comm_dates.loc[comm.index]

    comm["_locality"] = comm[locality_col].fillna("Unknown").astype(str).str.strip()
    if amount_col:
        comm["_amount"] = comm[amount_col].apply(clean_amount_value)
    if arrears_col:
        comm["_arrears"] = comm[arrears_col].apply(clean_amount_value)
    comm["_period"] = comm_dates.dt.to_period("M")

    fiscal_start, current_period = get_fiscal_window()
    comm = comm[(comm["_period"] >= fiscal_start) & (comm["_period"] <= current_period)]

    # Total by locality
    agg_t = {"count": ("_locality", "size")}
    if amount_col:
        agg_t["amount"] = ("_amount", "sum")
    if arrears_col:
        agg_t["arrears"] = ("_arrears", "sum")
    total_grouped = comm.groupby("_locality").agg(**agg_t).sort_index()
    total_rows = []
    for loc, row in total_grouped.iterrows():
        item = {"label": loc, "count": int(row["count"])}
        if "amount" in row:
            item["amount_total"] = float(row["amount"])
        if "arrears" in row:
            item["arrears_total"] = float(row["arrears"])
        total_rows.append(item)

    # Month-wise by locality
    agg_m = {"count": ("_locality", "size")}
    if amount_col:
        agg_m["amount"] = ("_amount", "sum")
    if arrears_col:
        agg_m["arrears"] = ("_arrears", "sum")
    monthly_grouped = comm.groupby(["_period", "_locality"]).agg(**agg_m).reset_index()
    monthly_data = {}
    for _, row in monthly_grouped.iterrows():
        month_label = format_fiscal_month(row["_period"])
        if month_label not in monthly_data:
            monthly_data[month_label] = []
        item = {"label": row["_locality"], "count": int(row["count"])}
        if "amount" in row:
            item["amount_total"] = float(row["amount"])
        if "arrears" in row:
            item["arrears_total"] = float(row["arrears"])
        monthly_data[month_label].append(item)

    return total_rows, monthly_data


def build_commercial_daily_income_rows(
    df: pd.DataFrame,
    dates: pd.Series,
    amount_col: str | None,
    arrears_col: str | None,
    areas_col: str | None,
) -> tuple[list[dict], str] | tuple[None, str]:
    columns = list(df.columns)
    required_cols = {
        "consumer_name": pick_column(columns, ["consumer name / f/h name", "consumer name", "name"]),
        "connection_no": pick_column(columns, ["connection no", "connection number", "old connection no"]),
        "sector": pick_column(columns, ["sector"]),
        "locality": pick_column(columns, ["locality"]),
    }
    if not required_cols["sector"] or not required_cols["locality"]:
        return None, "Arrears Received" if arrears_col else "Areas Received"

    metric_col = arrears_col or areas_col
    metric_label = "Arrears Received" if arrears_col else "Areas Received"
    mask = build_commercial_mask(df)
    comm = df[mask].copy()
    if comm.empty:
        return [], metric_label

    comm_dates = dates.reindex(comm.index).dropna()
    comm = comm.loc[comm_dates.index].copy()
    comm_dates = comm_dates.loc[comm.index]

    fiscal_start, current_period = get_fiscal_window()
    periods = comm_dates.dt.to_period("M")
    comm = comm[(periods >= fiscal_start) & (periods <= current_period)].copy()
    comm_dates = comm_dates.loc[comm.index]
    if comm.empty:
        return [], metric_label

    rows = []
    for idx in sorted(comm.index, key=lambda key: (comm_dates.loc[key].date(), str(key))):
        row = comm.loc[idx]
        rows.append(
            {
                "date": comm_dates.loc[idx].strftime("%d-%m-%Y"),
                "consumer_name": clean_cell(row.get(required_cols["consumer_name"])) if required_cols["consumer_name"] else "",
                "connection_no": clean_cell(row.get(required_cols["connection_no"])) if required_cols["connection_no"] else "",
                "sector": clean_cell(row.get(required_cols["sector"])),
                "locality": clean_cell(row.get(required_cols["locality"])),
                "metric_total": parse_number(row.get(metric_col)) if metric_col else 0,
                "amount_total": parse_number(row.get(amount_col)) if amount_col else 0,
            }
        )
    return rows, metric_label


def load_staff_assignment_rows() -> tuple[list[dict], list[dict]]:
    init_bill_list_db()
    with get_db() as conn:
        staff = [dict(row) for row in conn.execute("SELECT id, name FROM staff ORDER BY name").fetchall()]
        assignments = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    sa.staff_id,
                    s.name AS staff_name,
                    sa.zone,
                    COALESCE(sa.sector, '') AS sector,
                    COALESCE(sa.locality, '') AS locality
                FROM staff_assignments sa
                JOIN staff s ON s.id = sa.staff_id
                ORDER BY s.name, sa.zone, sa.sector, sa.locality
                """
            ).fetchall()
        ]
    return staff, assignments


def get_auto_staff_override(sector: str, locality: str, connection_no: str, staff_list: list[dict]) -> dict | None:
    if not connection_no:
        return None
    conn_str = str(connection_no).strip()
    sector_norm = _normalize_sector_locality(sector)
    locality_norm = _normalize_sector_locality(locality)
    with get_db() as conn:
        rules = conn.execute(
            """
            SELECT staff_name, connection_min, connection_max, sector, locality
            FROM auto_assignment_rules
            ORDER BY connection_min
            """,
        ).fetchall()
    for rule in rules:
        rule_sector_norm = _normalize_sector_locality(rule["sector"])
        rule_locality_norm = _normalize_sector_locality(rule["locality"])
        if rule_sector_norm != sector_norm or rule_locality_norm != locality_norm:
            continue
        if conn_str >= rule["connection_min"]:
            if rule["connection_max"] is None or conn_str <= rule["connection_max"]:
                for s in staff_list:
                    if _normalize_staff_name(s["name"]) == _normalize_staff_name(rule["staff_name"]):
                        return {
                            "staff_id": s["id"],
                            "staff_name": s["name"],
                            "zone": "",
                            "sector": sector,
                            "locality": locality,
                        }
    return None


def match_staff_assignment(zone: str, sector: str, locality: str, assignments: list[dict], connection_no: str | None = None) -> dict | None:
    if connection_no:
        with get_db() as conn:
            staff_list = conn.execute("SELECT id, name FROM staff").fetchall()
        override = get_auto_staff_override(sector, locality, connection_no, staff_list)
        if override:
            return override
    zone = clean_cell(zone)
    sector = clean_cell(sector)
    locality = clean_cell(locality)
    zone_key = match_key(zone)
    sector_key = match_key(sector)
    locality_key = match_key(locality)
    for assignment in assignments:
        if (
            match_key(assignment["zone"]) == zone_key
            and match_key(assignment["sector"]) == sector_key
            and match_key(assignment["locality"]) == locality_key
        ):
            return assignment
    for assignment in assignments:
        if (
            match_key(assignment["zone"]) == zone_key
            and match_key(assignment["sector"]) == sector_key
            and not clean_cell(assignment["locality"])
        ):
            return assignment
    for assignment in assignments:
        if (
            match_key(assignment["zone"]) == zone_key
            and not clean_cell(assignment["sector"])
            and not clean_cell(assignment["locality"])
        ):
            return assignment
    return None


def get_staff_by_connection_rule(
    sector: str,
    locality: str,
    connection_no: str,
    staff_list: list[dict],
) -> dict | None:
    if not connection_no:
        return None
    conn_str = str(connection_no).strip()
    if not conn_str:
        return None
    sector_norm = _normalize_sector_locality(sector)
    locality_norm = _normalize_sector_locality(locality)
    for rule in AUTO_ASSIGNMENT_RULES:
        rule_sector_norm = _normalize_sector_locality(rule["sector"])
        rule_locality_norm = _normalize_sector_locality(rule["locality"])
        if rule_sector_norm != sector_norm or rule_locality_norm != locality_norm:
            continue
        if conn_str >= rule["connection_min"]:
            if rule["connection_max"] is None or conn_str <= rule["connection_max"]:
                for s in staff_list:
                    if _normalize_staff_name(s["name"]) == _normalize_staff_name(rule["staff_name"]):
                        return {"staff_id": s["id"], "staff_name": s["name"], "zone": "", "sector": sector, "locality": locality}
    return None


def build_daily_staff_receive_report(
    df: pd.DataFrame,
    dates: pd.Series,
    amount_col: str | None,
    arrears_col: str | None,
    areas_col: str | None,
) -> dict:
    columns = list(df.columns)
    sector_col = pick_column(columns, ["sector"])
    locality_col = pick_column(columns, ["locality"])
    if not sector_col or not locality_col:
        return {"summary_rows": [], "detail_rows": [], "metric_label": "Area Received", "date_range": ""}

    metric_col = arrears_col or areas_col
    connection_no_col = pick_column(columns, ["connection no", "connection number", "old connection no", "consumer no", "customer no", "connection id", "conn id"])
    staff, assignments = load_staff_assignment_rows()
    with get_db() as conn:
        locality_zones = {
            (row["sector"], row["locality"]): row["zone"]
            for row in conn.execute("SELECT sector, locality, zone FROM localities").fetchall()
        }
        sector_zones = {
            row["name"]: row["zone"]
            for row in conn.execute(
                f"""
                SELECT name, zone
                FROM sectors
                ORDER BY {zone_sort_expr('zone')}
                """
            ).fetchall()
        }

    staff_totals = {
        int(row["id"]): {
            "staff_id": int(row["id"]),
            "staff_name": row["name"],
            "zone": "",
            "bills": 0,
            "metric_total": 0.0,
            "amount_total": 0.0,
        }
        for row in staff
    }
    detail_groups: dict[int, dict] = {}

    valid_dates = dates.dropna()
    date_range = ""
    if not valid_dates.empty:
        min_date = valid_dates.min().strftime("%d-%m-%Y")
        max_date = valid_dates.max().strftime("%d-%m-%Y")
        date_range = min_date if min_date == max_date else f"{min_date} to {max_date}"

    for idx in valid_dates.index:
        row = df.loc[idx]
        amount_received = parse_number(row.get(amount_col)) if amount_col else 0.0
        metric_total = parse_number(row.get(metric_col)) if metric_col else 0.0
        if amount_col and amount_received <= 0:
            continue

        sector = clean_cell(row.get(sector_col)) or "Unknown"
        locality = clean_cell(row.get(locality_col)) or "Unknown"
        zone = locality_zones.get((sector, locality)) or sector_zones.get(sector) or infer_zone(sector, locality, row.to_dict())
        connection_no = clean_cell(row.get(connection_no_col)) if connection_no_col else None
        assignment = get_staff_by_connection_rule(sector, locality, connection_no, staff)
        if not assignment:
            assignment = match_staff_assignment(zone, sector, locality, assignments, connection_no)
        if assignment:
            if "MAHBOOB" in sector.upper() or "NOOR" in sector.upper() or "MURTAZA" in assignment.get("staff_name", "").upper() or "LATIF" in assignment.get("staff_name", "").upper():
                print(f"DEBUG_AUTO cn={connection_no} sector={sector!r} locality={locality!r} zone={zone!r} assigned={assignment['staff_name']!r}")
        if assignment:
            staff_id = int(assignment["staff_id"])
            staff_name = assignment["staff_name"]
            assigned_zone = assignment["zone"]
            staff_totals.setdefault(
                staff_id,
                {
                    "staff_id": staff_id,
                    "staff_name": staff_name,
                    "zone": assigned_zone,
                    "bills": 0,
                    "metric_total": 0.0,
                    "amount_total": 0.0,
                },
            )
        else:
            staff_id = 0
            staff_name = "Unassigned"
            assigned_zone = zone
            staff_totals.setdefault(
                staff_id,
                {
                    "staff_id": staff_id,
                    "staff_name": staff_name,
                    "zone": assigned_zone,
                    "bills": 0,
                    "metric_total": 0.0,
                    "amount_total": 0.0,
                },
            )

        total = staff_totals[staff_id]
        total["zone"] = total["zone"] or assigned_zone
        total["bills"] += 1
        total["metric_total"] += metric_total
        total["amount_total"] += amount_received

        group = detail_groups.setdefault(
            staff_id,
            {
                "staff_id": staff_id,
                "staff_name": staff_name,
                "zone": assigned_zone,
                "bills": 0,
                "metric_total": 0.0,
                "amount_total": 0.0,
                "sub_rows": {},
            },
        )
        group["zone"] = group["zone"] or assigned_zone
        group["bills"] += 1
        group["metric_total"] += metric_total
        group["amount_total"] += amount_received
        sub_key = (assigned_zone, sector, locality)
        sub = group["sub_rows"].setdefault(
            sub_key,
            {
                "zone": assigned_zone,
                "sector": sector,
                "locality": locality,
                "bills": 0,
                "metric_total": 0.0,
                "amount_total": 0.0,
            },
        )
        sub["bills"] += 1
        sub["metric_total"] += metric_total
        sub["amount_total"] += amount_received

    summary_rows = sorted(staff_totals.values(), key=lambda item: (item["zone"] or "ZZZ", item["staff_name"]))
    grouped_detail = sorted(
        (
            {
                "staff_id": g["staff_id"],
                "staff_name": g["staff_name"],
                "zone": g["zone"],
                "bills": g["bills"],
                "metric_total": g["metric_total"],
                "amount_total": g["amount_total"],
                "sub_rows": sorted(g["sub_rows"].values(), key=lambda s: (s["zone"], s["sector"], s["locality"])),
            }
            for g in detail_groups.values()
        ),
        key=lambda g: (g["staff_name"], g["zone"]),
    )
    detail_rows = [
        {
            "staff_id": g["staff_id"],
            "staff_name": g["staff_name"],
            "zone": sub["zone"],
            "sector": sub["sector"],
            "locality": sub["locality"],
            "bills": sub["bills"],
            "metric_total": sub["metric_total"],
            "amount_total": sub["amount_total"],
            "_group_bills": g["bills"],
            "_group_metric": g["metric_total"],
            "_group_amount": g["amount_total"],
        }
        for g in grouped_detail
        for sub in g["sub_rows"]
    ]
    return {
        "summary_rows": summary_rows,
        "detail_rows": detail_rows,
        "grouped_detail": grouped_detail,
        "metric_label": "Area Received",
        "date_range": date_range,
    }


# ---------------------------------------------------------------------------
# Summarize
# ---------------------------------------------------------------------------

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def clean_amount_value(val) -> float:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0.0
    s = str(val).strip()
    if not s or s.lower() in ("nan", "null", "none", ""):
        return 0.0
    s = re.sub(r"(?i)Rs\.?\s*", "", s)
    s = s.replace(",", "").replace('"', "").replace("'", "")
    s = s.strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def parse_date_dd_mm_yyyy(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "null", "none", ""):
        return None
    if "water bills receipts" in s.lower():
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.notna(dt):
            return dt.to_pydatetime()
    except Exception:
        pass
    return None


def build_receipt_monthly_rows(df: pd.DataFrame, date_col_name: str, arrears_col_name: str, amount_col_name: str) -> dict | None:
    month_map = {}
    total_rows = 0
    valid_rows = 0
    total_arrears = 0
    total_amount = 0

    for idx, row_ref in df.iterrows():
        total_rows += 1
        raw_date = row_ref[date_col_name]
        if raw_date is None or (isinstance(raw_date, float) and pd.isna(raw_date)):
            continue
        raw_date_str = str(raw_date).strip()
        if not raw_date_str or raw_date_str.lower() in ("nan", "null", "none", ""):
            continue
        if "water bills receipts" in raw_date_str.lower():
            continue

        dt = parse_date_dd_mm_yyyy(raw_date)
        if dt is None:
            continue

        valid_rows += 1
        month_key = f"{dt.year}-{dt.month:02d}"
        arrears_val = clean_amount_value(row_ref[arrears_col_name])
        amount_val = clean_amount_value(row_ref[amount_col_name])

        total_arrears += arrears_val
        total_amount += amount_val

        if month_key not in month_map:
            month_map[month_key] = {
                "date": dt,
                "label": f"{MONTH_NAMES[dt.month - 1]} {str(dt.year)[-2:]}",
                "_sort_key": dt.replace(day=1),
                "count": 0,
                "arrears_total": 0.0,
                "amount_total": 0.0,
            }
        month_map[month_key]["count"] += 1
        month_map[month_key]["arrears_total"] += arrears_val
        month_map[month_key]["amount_total"] += amount_val

    rows = sorted(month_map.values(), key=lambda r: r["_sort_key"])

    if not rows:
        return None

    min_date = rows[0]["_sort_key"]
    max_date = rows[-1]["_sort_key"]

    return {
        "rows": rows,
        "period_start": f"{MONTH_NAMES[min_date.month - 1]} {str(min_date.year)[-2:]}",
        "period_end": f"{MONTH_NAMES[max_date.month - 1]} {str(max_date.year)[-2:]}",
        "total_arrears": total_arrears,
        "total_amount": total_amount,
        "debug": {
            "total_rows_processed": total_rows,
            "valid_rows_used": valid_rows,
        },
    }


def summarize_dataframe(df: pd.DataFrame) -> dict:
    df = normalize_dataframe(df)
    columns = [str(col) for col in df.columns]

    date_col = pick_column(columns, ["received date", "receiving date", "date"])
    amount_col = pick_column(columns, ["amount received", "amount", "total amount", "total bill"])
    arrears_col = pick_column(columns, ["arrears"])
    areas_col = pick_column(columns, ["areas", "area"])
    sector_col = "sector" if "sector" in columns else None

    total_amount = None
    if amount_col:
        total_amount = float(df[amount_col].apply(clean_amount_value).sum())

    total_arrears = None
    if arrears_col:
        total_arrears = float(df[arrears_col].apply(clean_amount_value).sum())

    total_areas = None
    if areas_col:
        total_areas = float(pd.to_numeric(df[areas_col], errors="coerce").sum(skipna=True))

    clean_amount_debug = {}
    daily_rows, monthly_rows, date_note = [], [], None
    fiscal_row_count = None
    commercial_total, commercial_monthly = None, None
    commercial_daily_income, commercial_daily_metric_label = None, "Arrears Received" if arrears_col else "Areas Received"
    daily_staff_receive = {"summary_rows": [], "detail_rows": [], "metric_label": "Area Received", "date_range": ""}
    dates = None

    if date_col:
        dates = parse_received_dates(df[date_col]).dropna()
        if dates.empty:
            date_note = f"No valid dates found in '{date_col}'."
        else:
            amounts_s = df[amount_col].apply(clean_amount_value) if amount_col else None
            arrears_s = df[arrears_col].apply(clean_amount_value) if arrears_col else None

            # Debug: compare wrong vs clean totals
            if amount_col:
                _wrong_amount = float(pd.to_numeric(df[amount_col], errors="coerce").sum(skipna=True))
                _clean_amount = float(df[amount_col].apply(clean_amount_value).sum())
                clean_amount_debug["amount_wrong"] = _wrong_amount
                clean_amount_debug["amount_clean"] = _clean_amount
                clean_amount_debug["amount_diff"] = _clean_amount - _wrong_amount
                if abs(_wrong_amount - _clean_amount) > 1:
                    print(f"CLEAN_AMOUNT_DEBUG: pd.to_numeric sum={_wrong_amount:.0f}, clean_amount_value sum={_clean_amount:.0f} (diff={_clean_amount - _wrong_amount:.0f})")
            if arrears_col:
                _wrong_arrears = float(pd.to_numeric(df[arrears_col], errors="coerce").sum(skipna=True))
                _clean_arrears = float(df[arrears_col].apply(clean_amount_value).sum())
                clean_amount_debug["arrears_wrong"] = _wrong_arrears
                clean_amount_debug["arrears_clean"] = _clean_arrears
                clean_amount_debug["arrears_diff"] = _clean_arrears - _wrong_arrears
                if abs(_wrong_arrears - _clean_arrears) > 1:
                    print(f"CLEAN_AMOUNT_DEBUG: pd.to_numeric sum={_wrong_arrears:.0f}, clean_amount_value sum={_clean_arrears:.0f} (diff={_clean_arrears - _wrong_arrears:.0f})")

            daily_rows = build_daily_rows(dates, amounts_s, arrears_s)
            monthly_rows = build_monthly_rows(dates, amounts_s, arrears_s)
            fiscal_row_count = sum(r.get("count", 0) for r in monthly_rows) if monthly_rows else 0
            commercial_total, commercial_monthly = build_commercial_rows(df, dates, amount_col, arrears_col)
            commercial_daily_income, commercial_daily_metric_label = build_commercial_daily_income_rows(
                df,
                dates,
                amount_col,
                arrears_col,
                areas_col,
            )
            daily_staff_receive = build_daily_staff_receive_report(
                df,
                dates,
                amount_col,
                arrears_col,
                areas_col,
            )
    else:
        date_note = "No received date column found."

    # Sector breakdown
    sector_rows, sector_note = [], None
    if sector_col and (amount_col or areas_col):
        sector_series = df[sector_col].fillna("Unknown").astype(str).str.strip().replace({"": "Unknown"})
        sector_df = pd.DataFrame({"sector": sector_series})
        if amount_col:
            sector_df["amount"] = df[amount_col].apply(clean_amount_value)
        if arrears_col:
            sector_df["arrears"] = df[arrears_col].apply(clean_amount_value)
        if areas_col:
            sector_df["areas"] = pd.to_numeric(df[areas_col], errors="coerce")
        sector_grouped = sector_df.groupby("sector").sum(numeric_only=True).sort_index()
        sector_rows = []
        for label, row in sector_grouped.iterrows():
            item = {"label": label, "count": 0}
            if "amount" in row:
                item["amount_total"] = float(row["amount"])
            if "arrears" in row:
                item["arrears_total"] = float(row["arrears"])
            if "areas" in row:
                item["areas_total"] = float(row["areas"])
            sector_rows.append(item)
    elif not sector_col:
        sector_note = "No sector column found."

    # Receipt month-wise report (new format: Received Date + Arrears + Amount Received)
    receipt_info = None
    if "received date" in columns and arrears_col is not None and amount_col is not None:
        receipt_info = build_receipt_monthly_rows(df, "received date", arrears_col, amount_col)

    has_receipt_format = receipt_info is not None

    return {
        "row_count": int(len(df)),
        "columns": columns,
        "date_column": date_col,
        "amount_column": amount_col,
        "arrears_column": arrears_col,
        "areas_column": areas_col,
        "sector_column": sector_col,
        "total_amount": total_amount,
        "total_amount_formatted": fmt(total_amount),
        "total_arrears": total_arrears,
        "total_arrears_formatted": fmt(total_arrears),
        "total_areas": total_areas,
        "total_areas_formatted": fmt(total_areas),
        "daily_rows": daily_rows,
        "monthly_rows": monthly_rows,
        "sector_rows": sector_rows,
        "date_note": date_note,
        "sector_note": sector_note,
        "fiscal_row_count": fiscal_row_count,
        "has_amount": amount_col is not None,
        "has_arrears": arrears_col is not None,
        "has_areas": areas_col is not None,
        "has_date": date_col is not None,
        "commercial_total": commercial_total,
        "commercial_monthly": commercial_monthly,
        "commercial_daily_income": commercial_daily_income,
        "commercial_daily_metric_label": commercial_daily_metric_label,
        "daily_staff_receive": daily_staff_receive,
        "has_receipt_format": has_receipt_format,
        "receipt_monthly_rows": (receipt_info or {}).get("rows", []),
        "receipt_period_start": (receipt_info or {}).get("period_start", ""),
        "receipt_period_end": (receipt_info or {}).get("period_end", ""),
        "receipt_total_arrears": (receipt_info or {}).get("total_arrears", 0),
        "receipt_total_amount": (receipt_info or {}).get("total_amount", 0),
        "receipt_total_arrears_fmt": fmt((receipt_info or {}).get("total_arrears", 0)),
        "receipt_total_amount_fmt": fmt((receipt_info or {}).get("total_amount", 0)),
        "receipt_debug": (receipt_info or {}).get("debug", {}),
        "clean_amount_debug": clean_amount_debug,
    }


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

ACCENT = colors.HexColor("#2f6f6d")
ACCENT2 = colors.HexColor("#d28b62")
HEADER_BG = colors.HexColor("#2f6f6d")
HEADER_FG = colors.white
ALT_ROW = colors.HexColor("#f4f1ea")
BORDER_CLR = colors.HexColor("#d9d2c6")


def _make_pdf_table(
    data_rows,
    col_widths=None,
    first_col_left=False,
    left_cols=None,
    header_font_size=12,
    body_font_size=11,
    cell_padding=8,
):
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_FG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), header_font_size),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), body_font_size),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ("TOPPADDING", (0, 0), (-1, -1), cell_padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), cell_padding),
        ("LEFTPADDING", (0, 0), (-1, -1), max(3, cell_padding - 2)),
        ("RIGHTPADDING", (0, 0), (-1, -1), max(3, cell_padding - 2)),
    ])
    # Alternate row colors
    for i in range(1, len(data_rows)):
        if i % 2 == 0:
            style.add("BACKGROUND", (0, i), (-1, i), ALT_ROW)
    # Bold last row (grand total)
    if len(data_rows) > 2:
        last = len(data_rows) - 1
        style.add("FONTNAME", (0, last), (-1, last), "Helvetica-Bold")
        style.add("FONTSIZE", (0, last), (-1, last), body_font_size)
        style.add("BACKGROUND", (0, last), (-1, last), colors.HexColor("#e6d8c8"))

    for idx, row in enumerate(data_rows[1:], start=1):
        row_text = " ".join(str(cell) for cell in row)
        if " Total" in row_text or "Grand Total" in row_text:
            style.add("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold")
            style.add("FONTSIZE", (0, idx), (-1, idx), body_font_size)
            style.add("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#e6d8c8"))
            style.add("TEXTCOLOR", (0, idx), (-1, idx), colors.black)
            style.add("BOTTOMPADDING", (0, idx), (-1, idx), cell_padding + 6)

    if first_col_left:
        style.add("ALIGN", (0, 0), (0, -1), "LEFT")
    for col in left_cols or []:
        style.add("ALIGN", (col, 1), (col, -1), "LEFT")

    t = Table(data_rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(style)
    return t


# ---------------------------------------------------------------------------
# Export column selection helpers
# ---------------------------------------------------------------------------

def parse_export_cols(cols_param, col_map, headers, rows):
    if not cols_param:
        return headers, rows
    selected_keys = [k.strip() for k in cols_param.split(",") if k.strip()]
    selected_indices = []
    filtered_headers = []
    for key in selected_keys:
        if key in col_map:
            idx = col_map[key]
            selected_indices.append(idx)
            filtered_headers.append(headers[idx])
    if not selected_indices or selected_indices == list(range(len(headers))):
        return headers, rows
    filtered_rows = [[row[i] for i in selected_indices] for row in rows]
    return filtered_headers, filtered_rows

# Column key maps for dashboard cards (index.html)
CARD_COL_MAPS = {
    "monthly": {"month": 0, "count": 1, "arrearsReceived": 2, "currentAmountReceived": 3, "amountReceived": 4},
    "daily": {"date": 0, "count": 1, "arrearsReceived": 2, "amountReceived": 3},
    "sector": {"sector": 0, "arrearsReceived": 1, "amountReceived": 2},
    "receipt-monthly": {"month": 0, "noOfBills": 1, "arrearsReceived": 2, "currentAmountReceived": 3, "amountReceived": 4},
    "commercial-daily-income": {"sr": 0, "date": 1, "consumerName": 2, "connectionNo": 3, "sector": 4, "locality": 5, "arrearsReceived": 6, "amountReceived": 7},
    "connection-type-summary": {"name": 0, "noOfBills": 1, "arrearsReceived": 2, "currentAmountReceived": 3, "amountReceived": 4},
    "daily-staff-receive": {"sr": 0, "staffName": 1, "bills": 2, "arrears": 3, "amount": 4},
}

def _get_card_col_map(card, r):
    if card in CARD_COL_MAPS:
        return CARD_COL_MAPS[card]
    if card in ("commercial", "commercial-total"):
        if r.get("has_arrears"):
            return {"locality": 0, "count": 1, "arrearsReceived": 2, "amountReceived": 3}
        return {"locality": 0, "count": 1, "amountReceived": 2}
    if card == "commercial-monthly":
        if r.get("has_arrears"):
            return {"month": 0, "locality": 1, "count": 2, "arrearsReceived": 3, "amountReceived": 4}
        return {"month": 0, "locality": 1, "count": 2, "amountReceived": 3}
    return None

def _filter_card_export(cols_param, col_map, headers, rows, grand=None):
    if not cols_param or not col_map:
        return headers, rows, grand
    selected_keys = [k.strip() for k in cols_param.split(",") if k.strip()]
    selected_indices = []
    filtered_headers = []
    for key in selected_keys:
        if key in col_map:
            idx = col_map[key]
            selected_indices.append(idx)
            filtered_headers.append(headers[idx])
    if not selected_indices or selected_indices == list(range(len(headers))):
        return headers, rows, grand
    filtered_rows = [[row[i] for i in selected_indices] for row in rows]
    filtered_grand = [grand[i] for i in selected_indices] if grand else None
    return filtered_headers, filtered_rows, filtered_grand

# Column key maps for each export route
# Sector-wise report: Sr, Sector, Total Bills, Received Bills, Remaining Bills, Total Received Amount, Pending Amount
SECTOR_COL_MAP = {"sr": 0, "sector": 1, "totalBills": 2, "receivedBills": 3, "remainingBills": 4, "totalReceivedAmount": 5, "pendingAmount": 6}

# Zone report (CSV/Excel): Sr, Zone, Sector, Total Bills, Received Bills, Remaining Bills, Amount Received, Pending Amount
ZONE_COL_MAP = {"sr": 0, "zone": 1, "sector": 2, "totalBills": 3, "receivedBills": 4, "remainingBills": 5, "totalReceivedAmount": 6, "pendingAmount": 7}

# Zone PDF detail: Sr, Sector, Total Bills, Received Bills, Remaining Bills, Amount Received, Pending Amount
ZONE_PDF_COL_MAP = {"sr": 0, "sector": 1, "totalBills": 2, "receivedBills": 3, "remainingBills": 4, "totalReceivedAmount": 5, "pendingAmount": 6}

# Zone PDF summary: Sr, Zone, Total Bills, Received Bills, Total Amount, Arrears Received, Total Received, Pending Amount
ZONE_SUMMARY_COL_MAP = {"sr": 0, "zone": 1, "totalBills": 2, "receivedBills": 3, "totalAmount": 4, "arrearsReceived": 5, "totalReceivedAmount": 6, "pendingAmount": 7}

# Unpaid amount summary: Bills, Total Bill Amount, Total Arrears Amount, Current Bill Amount
UNPAID_SUMMARY_COL_MAP = {"bills": 0, "totalBillAmount": 1, "totalArrearsAmount": 2, "currentBillAmount": 3}

# Unpaid amount section (sector/zone/staff): Sr, Name, Bills, Total Bill Amount, Total Arrears Amount, Current Bill Amount
UNPAID_SECTION_COL_MAP = {"sr": 0, "name": 1, "bills": 2, "totalBillAmount": 3, "totalArrearsAmount": 4, "currentBillAmount": 5}

# Staff report detail: Sr, Staff, Zone, Sector, Locality, Total Bills, Received Bills, Remaining Bills, Amount Received, Pending Amount
STAFF_COL_MAP = {"sr": 0, "staff": 1, "zone": 2, "sector": 3, "locality": 4, "totalBills": 5, "receivedBills": 6, "remainingBills": 7, "totalReceivedAmount": 8, "pendingAmount": 9}
STAFF_SUMMARY_COL_MAP = {"sr": 0, "staffName": 1, "totalBills": 2, "receivedBills": 3, "remainingBills": 4, "totalAmount": 5, "amountReceived": 6, "pendingAmount": 7}
PITCH_COL_MAP = {"sr": 0, "staffName": 1, "totalBills": 2, "receivedBills": 3, "remainingBills": 4, "totalAmount": 5, "amountReceived": 6, "currentBillAmount": 7}

# Staff PDF detail: Sr, Sector, Locality, Total Bills, Received Bills, Remaining Bills, Amount Received, Pending Amount
STAFF_PDF_COL_MAP = {"sr": 0, "sector": 1, "locality": 2, "totalBills": 3, "receivedBills": 4, "remainingBills": 5, "totalReceivedAmount": 6, "pendingAmount": 7}

# Advanced filter CSV/Excel: Bill No, Reference No, Connection No, Sector, Locality, Zone, Total Bill, Arrears, Amount Received, Outstanding Amount, Status
ADV_COL_MAP = {"billNo": 0, "referenceNo": 1, "connectionNo": 2, "sector": 3, "locality": 4, "zone": 5, "totalBills": 6, "arrearsReceived": 7, "totalReceivedAmount": 8, "outstanding": 9, "status": 10, "mobileNo": 11}

# Advanced filter PDF: Sr, Bill No, Connection No, Sector, Locality, Zone, Total Bill, Amount Received, Outstanding, Status
ADV_PDF_COL_MAP = {"sr": 0, "billNo": 1, "connectionNo": 2, "sector": 3, "locality": 4, "zone": 5, "totalBills": 6, "totalReceivedAmount": 7, "outstanding": 8, "status": 9, "mobileNo": 10}

# Summary report: Name, Count, Total Amount
SUMMARY_COL_MAP = {"name": 0, "count": 1, "totalAmount": 2}

# Column map for connection type summary (shared between standalone export and month-wise attachment)
CONN_SUMMARY_COL_MAP = {"name": 0, "noOfBills": 1, "arrearsReceived": 2, "currentAmountReceived": 3, "amountReceived": 4}

# Daily Staff Receive summary: Sr, Staff Name, No. of Bills Received, Arrears Received, Total Amount Received
DAILY_STAFF_RECEIVE_SUMMARY_COL_MAP = {"sr": 0, "staffName": 1, "bills": 2, "arrears": 3, "amount": 4}

# Daily Staff Receive detail: Staff Name, Zone, Sr, Sector, Locality, Bills, Arrears Received, Received Amount
DAILY_STAFF_RECEIVE_DETAIL_COL_MAP = {"staffName": 0, "zone": 1, "sr": 2, "sector": 3, "locality": 4, "bills": 5, "arrears": 6, "amount": 7}


def build_connection_summary(r):
    """Compute connection type collection summary from results dict."""
    source_rows = r.get("receipt_monthly_rows") or r.get("monthly_rows") or []
    overall_count = sum(row.get("count", 0) for row in source_rows)
    overall_arrears = sum(row.get("arrears_total", 0) for row in source_rows)
    overall_amount = sum(row.get("amount_total", 0) for row in source_rows)
    overall_current = overall_amount - overall_arrears
    comm_count = sum(row.get("count", 0) for row in (r.get("commercial_total") or []))
    comm_arrears = sum(row.get("arrears_total", 0) for row in (r.get("commercial_total") or []))
    comm_amount = sum(row.get("amount_total", 0) for row in (r.get("commercial_total") or []))
    comm_current = comm_amount - comm_arrears
    res_count = overall_count - comm_count
    res_arrears = overall_arrears - comm_arrears
    res_amount = overall_amount - comm_amount
    res_current = res_amount - res_arrears
    headers = ["Name", "No. of Bills", "Arrears Received", "Current Amount Received", "Amount Received"]
    rows = [
        ["Normal / Residential Connections", fmt(res_count), fmt(res_arrears), fmt(res_current), fmt(res_amount)],
        ["Commercial Connections", fmt(comm_count), fmt(comm_arrears), fmt(comm_current), fmt(comm_amount)],
    ]
    grand = ["Grand Total", fmt(overall_count), fmt(overall_arrears), fmt(overall_current), fmt(overall_amount)]
    return headers, rows, grand


def generate_card_pdf(
    title,
    summary_lines,
    headers,
    rows,
    grand_total_row=None,
    pagesize=A4,
    col_widths=None,
    first_col_left=False,
    left_cols=None,
    header_font_size=12,
    body_font_size=11,
    cell_padding=8,
    extra_section=None,
    compact=False,
):
    buf = io.BytesIO()
    if compact:
        left_margin = right_margin = 12 * mm
        top_margin = 15 * mm
        bottom_margin = 15 * mm
        title_fs = 16
        title_sa = 5*mm
        summary_fs = 10
        summary_sa = 2*mm
        summary_leading = 14
        summary_spacer = 5*mm
        section_fs = 12
        section_sb = 4*mm
        section_sa = 2*mm
        hdr_fs = 10
        bdy_fs = 10
        cp = 8
        extra_spacer = 4*mm
    else:
        left_margin = right_margin = 15 * mm
        top_margin = 20 * mm
        bottom_margin = 15 * mm
        title_fs = 20
        title_sa = 6*mm
        summary_fs = 11
        summary_sa = 2*mm
        summary_leading = 16
        summary_spacer = 8*mm
        section_fs = 14
        section_sb = 6*mm
        section_sa = 3*mm
        hdr_fs = header_font_size
        bdy_fs = body_font_size
        cp = cell_padding
        extra_spacer = 2*mm

    doc = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        leftMargin=left_margin,
        rightMargin=right_margin,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PDFTitle", parent=styles["Heading1"], fontSize=title_fs,
                                  textColor=ACCENT, alignment=1, spaceAfter=title_sa,
                                  fontName="Helvetica-Bold")
    summary_style = ParagraphStyle("PDFSummary", parent=styles["Normal"], fontSize=summary_fs,
                                    alignment=0, spaceAfter=summary_sa,
                                    textColor=colors.HexColor("#333333"),
                                    leading=summary_leading)
    section_style = ParagraphStyle("PDFSection", parent=styles["Heading3"], fontSize=section_fs,
                                    textColor=ACCENT, alignment=0, spaceBefore=section_sb,
                                    spaceAfter=section_sa, fontName="Helvetica-Bold")

    elements = [Paragraph(title, title_style)]
    if summary_lines:
        for line in summary_lines:
            elements.append(Paragraph(line, summary_style))
        elements.append(Spacer(1, summary_spacer))

    header_cell_style = ParagraphStyle(
        "PDFHeaderCell",
        parent=styles["Normal"],
        fontSize=hdr_fs,
        leading=hdr_fs + 2,
        alignment=1,
        textColor=HEADER_FG,
        fontName="Helvetica-Bold",
    )
    wrapped_headers = [Paragraph(str(header), header_cell_style) for header in headers]

    data = [wrapped_headers] + rows
    if grand_total_row:
        data.append(grand_total_row)

    page_w = pagesize[0] - left_margin - right_margin
    n_cols = len(headers)
    if col_widths is None:
        col_w = page_w / n_cols
        col_widths = [col_w] * n_cols
    elif len(col_widths) != n_cols:
        col_w = page_w / n_cols
        col_widths = [col_w] * n_cols
    t = _make_pdf_table(
        data,
        col_widths=col_widths,
        first_col_left=first_col_left,
        left_cols=left_cols,
        header_font_size=hdr_fs,
        body_font_size=bdy_fs,
        cell_padding=cp,
    )
    elements.append(t)

    # Attach extra section (e.g. Connection Type Summary) below main table
    # Uses KeepTogether so title + table stay on same page; flows to next page only when needed
    if extra_section is not None:
        extra_headers = extra_section["headers"]
        extra_rows = extra_section["rows"]
        extra_grand = extra_section.get("grand")
        # Build wrapped header cells without CJK word-wrap to prevent mid-word breaks
        hdr_style = ParagraphStyle(
            "PDFExtraHeaderCell",
            parent=getSampleStyleSheet()["Normal"],
            fontSize=hdr_fs,
            leading=hdr_fs + 2,
            alignment=1,
            textColor=HEADER_FG,
            fontName="Helvetica-Bold",
        )
        extra_data = [[Paragraph(str(h), hdr_style) for h in extra_headers]]
        extra_data.extend(wrap_pdf_body_cells(extra_rows, font_size=bdy_fs,
                                              left_columns={0}))
        if extra_grand:
            extra_data.append(wrap_pdf_body_cells([extra_grand], font_size=bdy_fs,
                                                  left_columns={0})[0])
        n_extra = len(extra_headers)
        extra_page_w = pagesize[0] - left_margin - right_margin
        if n_extra == 5:
            extra_col_widths = [extra_page_w * 0.26, extra_page_w * 0.14,
                                extra_page_w * 0.20, extra_page_w * 0.20, extra_page_w * 0.20]
        elif n_extra == 4:
            extra_col_widths = [extra_page_w * 0.30, extra_page_w * 0.16,
                                extra_page_w * 0.27, extra_page_w * 0.27]
        elif n_extra == 3:
            extra_col_widths = [extra_page_w * 0.40, extra_page_w * 0.28,
                                extra_page_w * 0.32]
        elif n_extra == 2:
            extra_col_widths = [extra_page_w * 0.55, extra_page_w * 0.45]
        else:
            extra_col_widths = [extra_page_w / n_extra] * n_extra
        extra_table = _make_pdf_table(
            extra_data, col_widths=extra_col_widths,
            first_col_left=True, left_cols=[0],
            header_font_size=hdr_fs,
            body_font_size=bdy_fs,
            cell_padding=cp,
        )
        extra_section_elements = []
        extra_section_elements.append(Spacer(1, extra_spacer))
        extra_section_elements.append(Paragraph("Summary", section_style))
        extra_section_elements.append(extra_table)
        elements.append(KeepTogether(extra_section_elements))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


def wrap_pdf_table_cells(rows: list[list], font_size: int = 7) -> list[list]:
    return wrap_pdf_body_cells(rows, font_size=font_size)


def wrap_pdf_header_cells(headers: list[str], font_size: int = 13) -> list:
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "PDFWrappedHeaderCell",
        parent=styles["Normal"],
        fontSize=font_size,
        leading=font_size + 2,
        alignment=1,
        textColor=HEADER_FG,
        fontName="Helvetica-Bold",
        wordWrap="CJK",
    )
    return [Paragraph(str(header or ""), header_style) for header in headers]


def is_large_pdf_text(value, threshold: int = 22) -> bool:
    text = clean_cell(value)
    if not text:
        return False
    if parse_number(text.replace(",", "")) and re.fullmatch(r"[\d,.\-\s]+", text):
        return False
    return len(text) > threshold or "\n" in text


def wrap_pdf_body_cells(
    rows: list[list],
    font_size: int = 8,
    large_text_threshold: int = 22,
    left_columns: set[int] | None = None,
) -> list[list]:
    styles = getSampleStyleSheet()
    wrapped = []
    left_columns = left_columns or set()
    for row in rows:
        wrapped_row = []
        for col_idx, value in enumerate(row):
            if isinstance(value, Paragraph):
                wrapped_row.append(value)
                continue
            align = 0 if col_idx in left_columns or is_large_pdf_text(value, large_text_threshold) else 1
            cell_style = ParagraphStyle(
                "PDFBodyCellLeft" if align == 0 else "PDFBodyCellCenter",
                parent=styles["Normal"],
                fontSize=font_size,
                leading=font_size + 1,
                alignment=align,
                wordWrap="CJK",
            )
            cell_text = str(value or "").replace("\n", "<br/>")
            wrapped_row.append(Paragraph(cell_text, cell_style))
        wrapped.append(wrapped_row)
    return wrapped


def generate_commercial_pdf(
    summary_lines,
    total_headers,
    total_rows,
    total_grand,
    monthly_data,
    has_arrears,
):
    buf = io.BytesIO()
    left_margin = 10 * mm
    right_margin = 10 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=15 * mm,
        leftMargin=left_margin,
        rightMargin=right_margin,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PDFTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=ACCENT,
        alignment=1,
        spaceAfter=6 * mm,
        fontName="Helvetica-Bold",
    )
    summary_style = ParagraphStyle(
        "PDFSummary",
        parent=styles["Normal"],
        fontSize=11,
        alignment=0,
        spaceAfter=2 * mm,
        textColor=colors.HexColor("#333333"),
        leading=16,
    )
    section_style = ParagraphStyle(
        "PDFSection",
        parent=styles["Heading3"],
        fontSize=13,
        textColor=ACCENT,
        alignment=0,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
        fontName="Helvetica-Bold",
    )

    elements = [Paragraph("Commercial Sector — Locality Report", title_style)]
    for line in summary_lines:
        elements.append(Paragraph(line, summary_style))
    elements.append(Spacer(1, 6 * mm))

    data = [total_headers] + total_rows
    if total_grand:
        data.append(total_grand)

    page_w = A4[0] - left_margin - right_margin
    if len(total_headers) == 4:
        col_widths = [page_w * 0.42, page_w * 0.14, page_w * 0.22, page_w * 0.22]
    elif len(total_headers) == 3 and has_arrears:
        col_widths = [page_w * 0.48, page_w * 0.26, page_w * 0.26]
    elif len(total_headers) == 3:
        col_widths = [page_w * 0.55, page_w * 0.18, page_w * 0.27]
    else:
        col_widths = [page_w * 0.62, page_w * 0.38]

    elements.append(_make_pdf_table(data, col_widths=col_widths, first_col_left=True))

    if monthly_data:
        elements.append(Spacer(1, 4 * mm))
        for month_label, rows in monthly_data.items():
            elements.append(Paragraph(month_label, section_style))
            month_headers = total_headers
            month_data = [month_headers] + rows
            elements.append(
                _make_pdf_table(month_data, col_widths=col_widths, first_col_left=True)
            )

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


def generate_commercial_monthly_pdf(summary_lines, monthly_sections, overall_total, has_arrears,
                                     pdf_headers=None, col_widths=None):
    buf = io.BytesIO()
    left_margin = 15 * mm
    right_margin = 15 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=15 * mm,
        leftMargin=left_margin,
        rightMargin=right_margin,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PDFTitle", parent=styles["Heading1"], fontSize=20, textColor=ACCENT, alignment=1, spaceAfter=6 * mm, fontName="Helvetica-Bold")
    summary_style = ParagraphStyle("PDFSummary", parent=styles["Normal"], fontSize=11, alignment=0, spaceAfter=2 * mm, textColor=colors.HexColor("#333333"), leading=16)
    section_style = ParagraphStyle("PDFSection", parent=styles["Heading3"], fontSize=14, textColor=ACCENT, alignment=1, spaceBefore=5 * mm, spaceAfter=3 * mm, fontName="Helvetica-Bold")

    if pdf_headers is None:
        pdf_headers = ["Locality", "No. of Bills"] + (["Arrears Received"] if has_arrears else []) + ["Amount Received"]
    page_w = A4[0] - left_margin - right_margin
    if col_widths is None:
        n = len(pdf_headers)
        if n == 4:
            col_widths = [page_w * 0.38, page_w * 0.20, page_w * 0.21, page_w * 0.21]
        elif n == 3:
            col_widths = [page_w * 0.48, page_w * 0.26, page_w * 0.26]
        elif n == 2:
            col_widths = [page_w * 0.62, page_w * 0.38]
        else:
            col_widths = [page_w / n] * n

    elements = [Paragraph("Commercial Sector - Month-wise Locality Report", title_style)]
    for line in summary_lines:
        elements.append(Paragraph(line, summary_style))
    elements.append(Spacer(1, 5 * mm))

    for section in monthly_sections:
        elements.append(Paragraph(section["month"], section_style))
        data = [wrap_pdf_header_cells(pdf_headers, font_size=11)]
        data.extend(wrap_pdf_body_cells(section["rows"], font_size=9, left_columns={0}))
        data.append(wrap_pdf_body_cells([section["total"]], font_size=9, left_columns={0})[0])
        elements.append(_make_pdf_table(data, col_widths=col_widths, header_font_size=9, body_font_size=9, cell_padding=5, first_col_left=True, left_cols=[0]))

    if overall_total:
        elements.append(Spacer(1, 5 * mm))
        data = [wrap_pdf_header_cells(pdf_headers, font_size=11), wrap_pdf_body_cells([overall_total], font_size=9, left_columns={0})[0]]
        elements.append(_make_pdf_table(data, col_widths=col_widths, header_font_size=9, body_font_size=9, cell_padding=5, first_col_left=True, left_cols=[0]))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


def generate_zone_grouped_pdf(title, summary_lines, grouped_sections, overall_total=None, zone_summary_data=None, pdf_detail_headers=None, zone_summary_sel=None):
    buf = io.BytesIO()
    left_margin = 15 * mm
    right_margin = 15 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        topMargin=20 * mm,
        bottomMargin=15 * mm,
        leftMargin=left_margin,
        rightMargin=right_margin,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PDFTitle", parent=styles["Heading1"], fontSize=20, textColor=ACCENT, alignment=1, spaceAfter=6 * mm, fontName="Helvetica-Bold")
    summary_style = ParagraphStyle("PDFSummary", parent=styles["Normal"], fontSize=11, alignment=0, spaceAfter=2 * mm, textColor=colors.HexColor("#333333"), leading=16)
    section_style = ParagraphStyle("PDFSection", parent=styles["Heading3"], fontSize=14, textColor=ACCENT, alignment=1, spaceBefore=5 * mm, spaceAfter=3 * mm, fontName="Helvetica-Bold")
    card_header_style = ParagraphStyle("CardHeader", parent=styles["Normal"], fontSize=10, textColor=HEADER_FG, fontName="Helvetica-Bold", alignment=1)
    card_label_style = ParagraphStyle("CardLabel", parent=styles["Normal"], fontSize=10, alignment=1, fontName="Helvetica")
    card_value_style = ParagraphStyle("CardValue", parent=styles["Normal"], fontSize=10, alignment=1, fontName="Helvetica")
    headers = pdf_detail_headers or ["Sr", "Sector", "Total Bills", "Received Bills", "Remaining Bills", "Amount Received", "Pending Amount"]
    page_w = landscape(A4)[0] - left_margin - right_margin
    col_widths = [page_w * 0.05, page_w * 0.40, page_w * 0.09, page_w * 0.11, page_w * 0.11, page_w * 0.12, page_w * 0.12]

    elements = [Paragraph(title, title_style)]
    for line in summary_lines:
        elements.append(Paragraph(line, summary_style))

    if zone_summary_data:
        elements.append(Spacer(1, 5 * mm))

        _zs_all_h = ["Sr", "Zone", "Total Bills", "Received Bills", "Total Amount", "Arrears Received", "Total Received", "Pending Amount"]
        _zs_all_w = [page_w * 0.04, page_w * 0.10, page_w * 0.10, page_w * 0.10, page_w * 0.15, page_w * 0.16, page_w * 0.15, page_w * 0.20]
        if zone_summary_sel:
            summ_headers = [_zs_all_h[i] for i in zone_summary_sel]
            summ_col_widths = [_zs_all_w[i] for i in zone_summary_sel]
        else:
            summ_headers = _zs_all_h
            summ_col_widths = _zs_all_w

        summ_header_style = ParagraphStyle("SummHeader", fontSize=10, leading=13, alignment=1, textColor=HEADER_FG, fontName="Helvetica-Bold")
        summ_data = [[Paragraph(h, summ_header_style) for h in summ_headers]]
        gt_bills = gt_received = gt_amount = gt_arrears = gt_received_amt = gt_pending = 0
        for idx, row in enumerate(zone_summary_data, start=1):
            tb = int(row['total_bills'] or 0)
            rb = int(row['received_bills'] or 0)
            ta = int(row['total_amount'] or 0)
            ar = int(row['total_arrears_received'] or 0)
            rv = int(row['total_received_amount'] or 0)
            pd_amt = int(row['pending_amount'] or 0)
            gt_bills += tb
            gt_received += rb
            gt_amount += ta
            gt_arrears += ar
            gt_received_amt += rv
            gt_pending += pd_amt
            _full_zs_row = [f"{idx}", row["zone"], f"{tb:,}", f"{rb:,}", f"{ta:,}", f"{ar:,}", f"{rv:,}", f"{pd_amt:,}"]
            summ_data.append([_full_zs_row[i] for i in (zone_summary_sel or range(8))])
        grand_idx = len(summ_data)
        _full_zs_gt = ["", "Grand Total", f"{gt_bills:,}", f"{gt_received:,}", f"{gt_amount:,}", f"{gt_arrears:,}", f"{gt_received_amt:,}", f"{gt_pending:,}"]
        summ_data.append([_full_zs_gt[i] for i in (zone_summary_sel or range(8))])

        summary_table = Table(summ_data, colWidths=summ_col_widths, repeatRows=1)
        st = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_FG),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 1), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
        ])
        for i in range(2, grand_idx):
            if i % 2 == 0:
                st.add("BACKGROUND", (0, i), (-1, i), ALT_ROW)
        st.add("BACKGROUND", (0, grand_idx), (-1, grand_idx), colors.HexColor("#e6d8c8"))
        st.add("FONTNAME", (0, grand_idx), (-1, grand_idx), "Helvetica-Bold")
        summary_table.setStyle(st)
        elements.append(summary_table)
        elements.append(Spacer(1, 4 * mm))

    for section in grouped_sections:
        elements.append(PageBreak())

        zone_name = section["zone"]
        total_row = section.get("total")

        summary_parts = []
        summary_parts.append(Spacer(1, 6 * mm))
        summary_parts.append(Paragraph(f"{zone_name} Summary", section_style))
        summary_parts.append(Spacer(1, 4 * mm))

        if total_row:
            card_data = [
                [Paragraph("Metric", card_header_style), Paragraph("Value", card_header_style)],
                [Paragraph("Total Bills", card_label_style), Paragraph(total_row[2], card_value_style)],
                [Paragraph("Received Bills", card_label_style), Paragraph(total_row[3], card_value_style)],
                [Paragraph("Remaining Bills", card_label_style), Paragraph(total_row[4], card_value_style)],
                [Paragraph("Amount Received", card_label_style), Paragraph(f"Rs. {total_row[5]}", card_value_style)],
                [Paragraph("Pending Amount", card_label_style), Paragraph(f"Rs. {total_row[6]}", card_value_style)],
            ]
            summary_cw = [page_w * 0.32, page_w * 0.32]
            card_table = Table(card_data, colWidths=summary_cw, hAlign="CENTER")
            card_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_FG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
                ("TOPPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("TOPPADDING", (0, 1), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ])
            for i in range(2, len(card_data)):
                if i % 2 == 0:
                    card_style.add("BACKGROUND", (0, i), (-1, i), ALT_ROW)
            card_table.setStyle(card_style)
            summary_parts.append(card_table)
            summary_parts.append(Spacer(1, 3 * mm))

        elements.append(KeepTogether(summary_parts))
        elements.append(Spacer(1, 6 * mm))

        detail_header_style = ParagraphStyle("DetailHeader", fontSize=10, leading=13, alignment=1, textColor=HEADER_FG, fontName="Helvetica-Bold")
        detail_rows = [[Paragraph(h, detail_header_style) for h in headers]]
        has_dt = section.get("total")
        for row in section["rows"]:
            detail_rows.append(row)
        if has_dt:
            detail_rows.append(has_dt)
        detail_table = Table(detail_rows, colWidths=col_widths, repeatRows=1)
        dt_st = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_FG),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 1), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
        ])
        for i in range(2, len(detail_rows)):
            if i % 2 == 0:
                dt_st.add("BACKGROUND", (0, i), (-1, i), ALT_ROW)
        if has_dt:
            last = len(detail_rows) - 1
            dt_st.add("BACKGROUND", (0, last), (-1, last), colors.HexColor("#e6d8c8"))
            dt_st.add("FONTNAME", (0, last), (-1, last), "Helvetica-Bold")
        detail_table.setStyle(dt_st)
        elements.append(detail_table)
        elements.append(Spacer(1, 6 * mm))

    if overall_total:
        elements.append(Spacer(1, 5 * mm))
        gt_header_style = ParagraphStyle("GtHeader", fontSize=10, leading=13, alignment=1, textColor=HEADER_FG, fontName="Helvetica-Bold")
        gt_rows = [[Paragraph(h, gt_header_style) for h in headers], overall_total]
        gt_table = Table(gt_rows, colWidths=col_widths, repeatRows=1)
        gt_st = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_FG),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_CLR),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 1), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#e6d8c8")),
        ])
        gt_table.setStyle(gt_st)
        elements.append(gt_table)

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Bill List database and reports
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(BILL_LIST_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_bill_list_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS localities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sector TEXT NOT NULL,
                locality TEXT NOT NULL,
                zone TEXT NOT NULL,
                UNIQUE(sector, locality)
            );

            CREATE TABLE IF NOT EXISTS zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS sectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                zone TEXT NOT NULL,
                UNIQUE(name, zone)
            );

            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_key TEXT NOT NULL UNIQUE,
                sector TEXT NOT NULL,
                locality TEXT NOT NULL,
                zone TEXT NOT NULL,
                bill_no TEXT,
                reference_no TEXT,
                connection_no TEXT,
                consumer_name TEXT,
                total_bill REAL NOT NULL DEFAULT 0,
                arrears REAL NOT NULL DEFAULT 0,
                amount_received REAL NOT NULL DEFAULT 0,
                status TEXT,
                raw_data TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS staff_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                zone TEXT NOT NULL,
                sector TEXT,
                locality TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(staff_id) REFERENCES staff(id),
                UNIQUE(staff_id, zone, sector, locality)
            );

            CREATE TABLE IF NOT EXISTS auto_assignment_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sector TEXT NOT NULL,
                locality TEXT NOT NULL,
                connection_min TEXT NOT NULL,
                connection_max TEXT,
                staff_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(sector, locality, connection_min, connection_max, staff_name)
            );
            """
        )
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(staff_assignments)").fetchall()]
        if "locality" not in columns:
            conn.execute("ALTER TABLE staff_assignments ADD COLUMN locality TEXT")
        bill_columns = [row["name"] for row in conn.execute("PRAGMA table_info(bills)").fetchall()]
        if "arrears" not in bill_columns:
            conn.execute("ALTER TABLE bills ADD COLUMN arrears REAL NOT NULL DEFAULT 0")
            backfill_bill_arrears(conn)
        if "consumer_mobile" not in bill_columns:
            conn.execute("ALTER TABLE bills ADD COLUMN consumer_mobile TEXT")
        if "consumer_name" not in bill_columns:
            conn.execute("ALTER TABLE bills ADD COLUMN consumer_name TEXT")
        unique_indexes = conn.execute("PRAGMA index_list(staff_assignments)").fetchall()
        has_locality_unique = False
        for index in unique_indexes:
            if not index["unique"]:
                continue
            index_cols = [
                col["name"]
                for col in conn.execute(f"PRAGMA index_info({index['name']})").fetchall()
            ]
            if index_cols == ["staff_id", "zone", "sector", "locality"]:
                has_locality_unique = True
                break
        if not has_locality_unique:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS staff_assignments_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staff_id INTEGER NOT NULL,
                    zone TEXT NOT NULL,
                    sector TEXT,
                    locality TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(staff_id) REFERENCES staff(id),
                    UNIQUE(staff_id, zone, sector, locality)
                );
                INSERT OR IGNORE INTO staff_assignments_new (id, staff_id, zone, sector, locality, created_at)
                SELECT id, staff_id, zone, sector, locality, created_at FROM staff_assignments;
                DROP TABLE staff_assignments;
                ALTER TABLE staff_assignments_new RENAME TO staff_assignments;
                """
            )
        for zone in ["A", "B", "C", "Commercial", "Unassigned"]:
            conn.execute("INSERT OR IGNORE INTO zones (name) VALUES (?)", (zone,))
        conn.execute(
            """
            INSERT OR IGNORE INTO sectors (name, zone)
            SELECT DISTINCT sector, zone
            FROM localities
            WHERE sector IS NOT NULL AND TRIM(sector) != ''
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO sectors (name, zone)
            SELECT DISTINCT sector, zone
            FROM bills
            WHERE sector IS NOT NULL AND TRIM(sector) != ''
            """
        )
        apply_manual_zone_overrides(conn)
        seed_auto_assignment_rules(conn)
        seed_staff_assignments_from_file(conn)


def seed_auto_assignment_rules(conn) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute("DROP INDEX IF EXISTS idx_auto_unique")
    conn.execute("DELETE FROM auto_assignment_rules")
    for rule in AUTO_ASSIGNMENT_RULES:
        conn.execute(
            """
            INSERT OR IGNORE INTO auto_assignment_rules (sector, locality, connection_min, connection_max, staff_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (rule["sector"], rule["locality"], rule["connection_min"], rule["connection_max"], rule["staff_name"], now),
        )
    conn.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS idx_auto_unique
        ON auto_assignment_rules(sector, locality, connection_min, connection_max, staff_name)"""
    )


def seed_staff_assignments_from_file(conn) -> None:
    if os.environ.get("VERCEL") != "1":
        return
    existing = conn.execute("SELECT COUNT(*) AS cnt FROM staff_assignments").fetchone()
    if existing and existing["cnt"] > 0:
        return

    seed_staff: list[str] = []
    seed_assignments: list[dict] = []

    if os.path.exists(SEED_ASSIGNMENTS_JSON):
        try:
            with open(SEED_ASSIGNMENTS_JSON, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            seed_staff = [str(s).strip() for s in data.get("staff", []) if str(s).strip()]
            seed_assignments = data.get("assignments", []) or []
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return
    elif os.path.exists(SEED_ASSIGNMENTS_CSV):
        try:
            with open(SEED_ASSIGNMENTS_CSV, "r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    seed_assignments.append(row)
                    staff_name = (row.get("staff_name") or "").strip()
                    if staff_name:
                        seed_staff.append(staff_name)
        except OSError:
            return
    else:
        return

    now = datetime.now().isoformat(timespec="seconds")
    staff_names = sorted({name for name in seed_staff if name})
    for name in staff_names:
        conn.execute(
            "INSERT OR IGNORE INTO staff (name, created_at) VALUES (?, ?)",
            (name, now),
        )

    staff_map = {row["name"]: row["id"] for row in conn.execute("SELECT id, name FROM staff").fetchall()}

    for item in seed_assignments:
        staff_name = str(item.get("staff_name") or "").strip()
        if not staff_name:
            continue
        staff_id = staff_map.get(staff_name)
        if staff_id is None:
            conn.execute(
                "INSERT OR IGNORE INTO staff (name, created_at) VALUES (?, ?)",
                (staff_name, now),
            )
            row = conn.execute("SELECT id FROM staff WHERE name = ?", (staff_name,)).fetchone()
            if not row:
                continue
            staff_id = row["id"]
            staff_map[staff_name] = staff_id

        zone = str(item.get("zone") or "").strip() or "Unassigned"
        sector = str(item.get("sector") or "").strip() or None
        locality = str(item.get("locality") or "").strip() or None
        conn.execute(
            """
            INSERT OR IGNORE INTO staff_assignments (staff_id, zone, sector, locality, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (staff_id, zone, sector, locality, now),
        )


def backfill_bill_arrears(conn) -> None:
    rows = conn.execute("SELECT id, raw_data FROM bills").fetchall()
    for row in rows:
        try:
            raw = json.loads(row["raw_data"] or "{}")
        except (TypeError, json.JSONDecodeError):
            raw = {}
        conn.execute(
            "UPDATE bills SET arrears = ? WHERE id = ?",
            (parse_number(raw.get("arrears")), row["id"]),
        )


def apply_manual_zone_overrides(conn) -> None:
    overrides = [
        (
            "Bahu Chowk to Sabz mandi Road",
            "67-Bahu Chowk, Sabzi  Mandi Road,Faisal Colony Zon",
            "A",
        )
    ]
    for sector, locality_prefix, zone in overrides:
        conn.execute(
            """
            UPDATE localities
            SET zone = ?
            WHERE sector = ? AND locality LIKE ? AND zone = 'Unassigned'
            """,
            (zone, sector, f"{locality_prefix}%"),
        )
        conn.execute(
            """
            UPDATE bills
            SET zone = ?
            WHERE sector = ? AND locality LIKE ? AND zone = 'Unassigned'
            """,
            (zone, sector, f"{locality_prefix}%"),
        )
        conn.execute("INSERT OR IGNORE INTO zones (name) VALUES (?)", (zone,))
        conn.execute(
            """
            INSERT OR IGNORE INTO sectors (name, zone)
            SELECT DISTINCT sector, zone
            FROM localities
            WHERE sector = ?
            """,
            (sector,),
        )
    conn.execute(
        """
        DELETE FROM sectors
        WHERE NOT EXISTS (
            SELECT 1 FROM localities WHERE localities.sector = sectors.name AND localities.zone = sectors.zone
        )
        AND NOT EXISTS (
            SELECT 1 FROM bills WHERE bills.sector = sectors.name AND bills.zone = sectors.zone
        )
        """
    )


def pick_saved_zone(conn, sector: str, locality: str, inferred_zone: str) -> str:
    row = conn.execute(
        "SELECT zone FROM localities WHERE sector = ? AND locality = ?",
        (sector, locality),
    ).fetchone()
    if row:
        return row["zone"]

    row = conn.execute(
        """
        SELECT zone
        FROM sectors
        WHERE name = ?
        ORDER BY CASE zone WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 WHEN 'Commercial' THEN 4 ELSE 5 END
        LIMIT 1
        """,
        (sector,),
    ).fetchone()
    if row:
        return row["zone"]

    return inferred_zone


def update_sector_zone(conn, sector: str, zone: str) -> None:
    old_zones = [
        row["zone"]
        for row in conn.execute(
            "SELECT DISTINCT zone FROM sectors WHERE name = ?",
            (sector,),
        ).fetchall()
    ]
    conn.execute("INSERT OR IGNORE INTO zones (name) VALUES (?)", (zone,))
    conn.execute("UPDATE localities SET zone = ? WHERE sector = ?", (zone, sector))
    conn.execute("UPDATE bills SET zone = ? WHERE sector = ?", (zone, sector))
    conn.execute("DELETE FROM sectors WHERE name = ?", (sector,))
    conn.execute("INSERT OR IGNORE INTO sectors (name, zone) VALUES (?, ?)", (sector, zone))
    for old_zone in old_zones:
        conn.execute(
            """
            UPDATE staff_assignments
            SET zone = ?
            WHERE sector = ? AND zone = ?
            """,
            (zone, sector, old_zone),
        )


def clear_bill_list_data() -> None:
    init_bill_list_db()
    with get_db() as conn:
        conn.execute("DELETE FROM bills")
        conn.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name = 'bills'
            """
        )

    upload_root = os.path.abspath(app.config["UPLOAD_FOLDER"])
    for filename in os.listdir(upload_root):
        if not filename.startswith("bill_list_"):
            continue
        path = os.path.abspath(os.path.join(upload_root, filename))
        if path.startswith(upload_root + os.sep) and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


def get_assignment_conflicts(conn, staff_id: str, zone: str, sectors: list[str], localities: list[tuple[str, str]] | None = None) -> list[str]:
    localities = localities or []
    if localities:
        conflicts = []
        for sector, locality in localities:
            row = conn.execute(
                """
                SELECT s.name
                FROM staff_assignments sa
                JOIN staff s ON s.id = sa.staff_id
                WHERE sa.zone = ?
                  AND (
                    sa.sector IS NULL
                    OR (sa.sector = ? AND sa.locality IS NULL)
                    OR (sa.sector = ? AND sa.locality = ?)
                  )
                  AND sa.staff_id != ?
                LIMIT 1
                """,
                (zone, sector, sector, locality, staff_id),
            ).fetchone()
            if row:
                conflicts.append(f"{sector} / {locality} is already assigned to {row['name']}")
        return conflicts

    if sectors:
        conflicts = []
        for sector in sectors:
            row = conn.execute(
                """
                SELECT s.name
                FROM staff_assignments sa
                JOIN staff s ON s.id = sa.staff_id
                WHERE sa.zone = ?
                  AND (sa.sector = ? OR sa.sector IS NULL)
                  AND sa.staff_id != ?
                LIMIT 1
                """,
                (zone, sector, staff_id),
            ).fetchone()
            if row:
                conflicts.append(f"{sector} is already assigned to {row['name']}")
        return conflicts

    rows = conn.execute(
        """
        SELECT DISTINCT COALESCE(sa.sector, 'All sectors') AS sector, s.name
        FROM staff_assignments sa
        JOIN staff s ON s.id = sa.staff_id
        WHERE sa.zone = ? AND sa.staff_id != ?
        ORDER BY sector
        """,
        (zone, staff_id),
    ).fetchall()
    return [f"{row['sector']} is already assigned to {row['name']}" for row in rows]


def infer_zone(sector: str, locality: str, row: dict) -> str:
    text = " ".join(str(value) for value in [sector, locality, row.get("connection type", ""), row.get("bill type", "")]).lower()
    if "commercial" in text:
        return "Commercial"
    match = re.search(r"\bzone\s*[-:]?\s*([abc])\b", text)
    if match:
        return match.group(1).upper()
    match = re.search(r"\b([abc])\s*zone\b", text)
    if match:
        return match.group(1).upper()
    return "Unassigned"


def build_bill_key(row: dict) -> str:
    key_sets = [
        ["bill no"],
        ["reference no", "due date", "total bill"],
        ["reference no", "amount received", "total bill"],
        ["connection no", "due date", "total bill"],
        ["connection no", "amount received", "total bill"],
    ]
    for columns in key_sets:
        values = [_dedupe_value(row.get(col)) for col in columns]
        if all(values):
            return "|".join(values)
    return "|".join(_dedupe_value(row.get(col)) for col in sorted(row.keys()))


def sql_text(value) -> str | None:
    text = _dedupe_value(value)
    return text or None


def import_bill_list_dataframe(df: pd.DataFrame) -> tuple[int, int]:
    df = normalize_dataframe(df)
    required = {"sector", "locality"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    df, duplicate_rows_removed, _ = drop_duplicate_bills(df)
    now = datetime.now().isoformat(timespec="seconds")
    inserted_or_updated = 0

    with get_db() as conn:
        for _, series in df.iterrows():
            row = {str(key): (None if pd.isna(value) else value) for key, value in series.to_dict().items()}
            sector = str(row.get("sector") or "Unknown").strip() or "Unknown"
            locality = str(row.get("locality") or "Unknown").strip() or "Unknown"
            zone = pick_saved_zone(conn, sector, locality, infer_zone(sector, locality, row))
            bill_key = build_bill_key(row)
            total_bill = parse_number(row.get("total bill") or row.get("after due date"))
            consumer_name_value = row.get("consumer name / f/h name")
            if consumer_name_value is None:
                consumer_name_value = row.get("consumer name")
            if consumer_name_value is None:
                consumer_name_value = row.get("f/h name")
            arrears_value = row.get("arrears")
            if arrears_value is None:
                arrears_value = row.get("outstanding amount")
            if arrears_value is None:
                arrears_value = row.get("outstanding")
            arrears = parse_number(arrears_value)
            amount_received = parse_number(row.get("amount received"))
            mobile_value = row.get("consumer mobile")
            if mobile_value is None:
                mobile_value = row.get("mobile no")
            if mobile_value is None:
                mobile_value = row.get("mobile")
            if mobile_value is None:
                mobile_value = row.get("consumer phone")
            if mobile_value is None:
                mobile_value = row.get("phone")
            consumer_mobile = str(mobile_value).strip() if mobile_value is not None else ""

            conn.execute(
                """
                INSERT INTO localities (sector, locality, zone)
                VALUES (?, ?, ?)
                ON CONFLICT(sector, locality) DO NOTHING
                """,
                (sector, locality, zone),
            )
            conn.execute("INSERT OR IGNORE INTO zones (name) VALUES (?)", (zone,))
            conn.execute(
                """
                INSERT INTO sectors (name, zone)
                VALUES (?, ?)
                ON CONFLICT(name, zone) DO NOTHING
                """,
                (sector, zone),
            )
            conn.execute(
                """
                INSERT INTO bills (
                    bill_key, sector, locality, zone, bill_no, reference_no, connection_no, consumer_name,
                    total_bill, arrears, amount_received, status, consumer_mobile, raw_data, uploaded_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(bill_key) DO UPDATE SET
                    sector = excluded.sector,
                    locality = excluded.locality,
                    zone = excluded.zone,
                    bill_no = excluded.bill_no,
                    reference_no = excluded.reference_no,
                    connection_no = excluded.connection_no,
                    consumer_name = excluded.consumer_name,
                    total_bill = excluded.total_bill,
                    arrears = excluded.arrears,
                    amount_received = excluded.amount_received,
                    status = excluded.status,
                    consumer_mobile = excluded.consumer_mobile,
                    raw_data = excluded.raw_data,
                    uploaded_at = excluded.uploaded_at
                """,
                (
                    bill_key,
                    sector,
                    locality,
                    zone,
                    sql_text(row.get("bill no")),
                    sql_text(row.get("reference no")),
                    sql_text(row.get("connection no")),
                    sql_text(consumer_name_value),
                    total_bill,
                    arrears,
                    amount_received,
                    row.get("status"),
                    consumer_mobile or None,
                    json.dumps(row, ensure_ascii=True, default=str),
                    now,
                ),
            )
            inserted_or_updated += 1

    return inserted_or_updated, duplicate_rows_removed


UNPAID_STATUS_SQL = "LOWER(REPLACE(REPLACE(TRIM(COALESCE(status, '')), '-', ''), ' ', '')) IN ('unpaid', 'expired')"


# ---------------------------------------------------------------------------
# Advanced Bill Filtering and Export
# ---------------------------------------------------------------------------

def get_filtered_bills(
    outstanding_amount: float | None = None,
    outstanding_operator: str = "gt",
    bill_status: str = "",
    sector: str | None = None,
    zone: str | None = None,
    staff_id: int | None = None,
):
    init_bill_list_db()
    with get_db() as conn:
        base_query = """
            SELECT
                b.id,
                b.bill_no,
                b.reference_no,
                b.connection_no,
                b.consumer_name,
                b.sector,
                b.locality,
                b.zone,
                b.total_bill,
                b.arrears,
                b.amount_received,
                b.status,
                b.consumer_mobile,
                b.raw_data,
                (b.total_bill - COALESCE(b.amount_received, 0)) AS outstanding_amount
            FROM bills b
            WHERE 1=1
        """
        params = []

        if bill_status == "paid":
            base_query += " AND b.amount_received >= b.total_bill"
        elif bill_status == "unpaid":
            base_query += " AND b.amount_received < b.total_bill"

        if outstanding_amount is not None and outstanding_amount > 0:
            if outstanding_operator == "lt":
                base_query += " AND (b.total_bill - COALESCE(b.amount_received, 0)) < ?"
            else:
                base_query += " AND (b.total_bill - COALESCE(b.amount_received, 0)) > ?"
            params.append(outstanding_amount)

        if sector:
            base_query += " AND b.sector = ?"
            params.append(sector)

        if zone:
            base_query += " AND b.zone = ?"
            params.append(zone)

        if staff_id is not None:
            base_query += """
                AND (
                    EXISTS (
                        SELECT 1 FROM staff_assignments sa
                        WHERE sa.staff_id = ?
                        AND sa.zone = b.zone
                        AND (sa.sector IS NULL OR b.sector = sa.sector)
                        AND (sa.locality IS NULL OR b.locality = sa.locality)
                    )
                    OR EXISTS (
                        SELECT 1 FROM auto_assignment_rules aar
                        JOIN staff s ON UPPER(TRIM(s.name)) = UPPER(TRIM(aar.staff_name))
                        WHERE s.id = ?
                        AND aar.sector = b.sector
                        AND aar.locality = b.locality
                        AND CAST(b.connection_no AS TEXT) >= aar.connection_min
                        AND (aar.connection_max IS NULL OR CAST(b.connection_no AS TEXT) <= aar.connection_max)
                    )
                )
            """
            params.append(staff_id)
            params.append(staff_id)

        base_query += " ORDER BY b.zone, b.sector, b.locality, b.bill_no"

        rows = conn.execute(base_query, params).fetchall()

    bills = []
    for row in rows:
        consumer_mobile = row["consumer_mobile"] or ""
        consumer_name = row["consumer_name"] or ""
        if not consumer_mobile:
            try:
                raw = json.loads(row["raw_data"] or "{}")
                if not consumer_name:
                    for nk in ("consumer name / f/h name", "consumer name", "f/h name"):
                        nv = raw.get(nk)
                        if nv is not None and str(nv).strip():
                            consumer_name = str(nv).strip()
                            break
                for mk in ("consumer mobile", "mobile no", "mobile", "consumer phone", "phone"):
                    mv = raw.get(mk)
                    if mv is not None and str(mv).strip():
                        consumer_mobile = str(mv).strip()
                        break
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        consumer_mobile = format_mobile(consumer_mobile)
        bills.append({
            "bill_no": row["bill_no"] or "",
            "reference_no": row["reference_no"] or "",
            "connection_no": row["connection_no"] or "",
            "consumer_name": consumer_name,
            "sector": row["sector"],
            "locality": row["locality"],
            "zone": row["zone"],
            "total_bill": float(row["total_bill"] or 0),
            "arrears": float(row["arrears"] or 0),
            "amount_received": float(row["amount_received"] or 0),
            "outstanding_amount": float(row["outstanding_amount"] or 0),
            "status": row["status"] or "",
            "consumer_mobile": consumer_mobile,
        })
    return bills


# ---------------------------------------------------------------------------
# Advanced Bill Checking — Grouping helpers
# ---------------------------------------------------------------------------

def map_bills_to_staff(bills: list[dict]) -> list[dict]:
    """Add a 'staff_name' key to each bill based on staff_assignments (locality > sector > zone) then auto_assignment_rules."""
    if not bills:
        return bills
    init_bill_list_db()
    with get_db() as conn:
        assignments = conn.execute("""
            SELECT sa.zone, sa.sector, sa.locality, s.name
            FROM staff_assignments sa
            JOIN staff s ON s.id = sa.staff_id
        """).fetchall()
        auto_rules = conn.execute("""
            SELECT aar.sector, aar.locality, aar.connection_min, aar.connection_max, s.name
            FROM auto_assignment_rules aar
            JOIN staff s ON UPPER(TRIM(s.name)) = UPPER(TRIM(aar.staff_name))
        """).fetchall()

    loc_map = {}
    sec_map = {}
    zone_map = {}
    for a in assignments:
        z, sec, loc, name_ = a["zone"], a["sector"], a["locality"], a["name"]
        if loc:
            loc_map[(z, sec, loc)] = name_
        elif sec:
            sec_map[(z, sec)] = name_
        else:
            zone_map[z] = name_

    for bill in bills:
        k_loc = (bill["zone"], bill["sector"], bill["locality"])
        k_sec = (bill["zone"], bill["sector"])
        k_zone = bill["zone"]
        if k_loc in loc_map:
            bill["staff_name"] = loc_map[k_loc]
        elif k_sec in sec_map:
            bill["staff_name"] = sec_map[k_sec]
        elif k_zone in zone_map:
            bill["staff_name"] = zone_map[k_zone]
        else:
            assigned = "Unassigned"
            for r in auto_rules:
                if (r["sector"] == bill["sector"] and r["locality"] == bill["locality"]
                        and str(bill.get("connection_no") or "") >= str(r["connection_min"])
                        and (r["connection_max"] is None or str(bill.get("connection_no") or "") <= str(r["connection_max"]))):
                    assigned = r["name"]
                    break
            bill["staff_name"] = assigned
    return bills


def _zone_sort_key(zone_name: str) -> tuple:
    """Return sort key for zone ordering: A=1, B=2, C=3, Commercial=4, unknown=99."""
    ZONE_RANK = {"a": 1, "b": 2, "c": 3, "commercial": 4}
    if not zone_name:
        return (99, "")
    n = zone_name.strip().lower().replace("zone ", "").replace("zone", "").strip()
    rank = ZONE_RANK.get(n, 99)
    return (rank, n)


def group_bills(bills: list[dict], group_by: str) -> list[tuple]:
    """Group bills by sector/zone/staff.

    Returns:
      - sector/zone: list of (group_label, [bill_dicts])
      - staff:      list of (zone, staff_name, [bill_dicts])
    """
    if not bills:
        return []
    if group_by == "sector":
        groups = {}
        for bill in bills:
            k = bill.get("sector") or "Unknown Sector"
            groups.setdefault(k, []).append(bill)
        keys = sorted(groups.keys(), key=lambda k: (k == "Unknown Sector", k.lower()))
        return [(k, groups[k]) for k in keys]
    if group_by == "zone":
        groups = {}
        for bill in bills:
            k = bill.get("zone") or "Unknown Zone"
            groups.setdefault(k, []).append(bill)
        keys = sorted(groups.keys(), key=lambda k: (_zone_sort_key(k)[0] if k != "Unknown Zone" else 99, k.lower()))
        return [(k, groups[k]) for k in keys]
    if group_by == "staff":
        bills = map_bills_to_staff(bills)
        zone_groups: dict[str, dict[str, list]] = {}
        for bill in bills:
            z = bill.get("zone") or "Unknown Zone"
            sn = bill.get("staff_name") or "Unassigned"
            zone_groups.setdefault(z, {}).setdefault(sn, []).append(bill)
        z_keys = sorted(zone_groups.keys(), key=_zone_sort_key)
        out = []
        for z in z_keys:
            for sn in sorted(zone_groups[z].keys(), key=str.lower):
                out.append((z, sn, zone_groups[z][sn]))
        return out
    return [("All Bills", bills)]


def generate_grouped_advanced_pdf(
    group_type: str,
    groups: list[tuple],
    filters_applied: str,
    cols_param: str = None,
) -> bytes:
    """Generate a landscape PDF with one section per group showing detailed bill rows."""
    _all_headers = ["Sr", "Bill No", "Reference No", "Connection No", "Consumer Name", "Sector", "Locality", "Zone", "Total Bill", "Arrears", "Amount Received", "Outstanding", "Status", "Mobile No"]
    _all_col_keys = ["sr", "billNo", "referenceNo", "connectionNo", "consumerName", "sector", "locality", "zone", "totalBills", "arrearsReceived", "totalReceivedAmount", "outstanding", "status", "mobileNo"]
    _all_key_map = {k: i for i, k in enumerate(_all_col_keys)}
    if cols_param:
        _sel_keys = [k.strip() for k in cols_param.split(",") if k.strip() in _all_col_keys]
        _col_indices = [_all_key_map[k] for k in _sel_keys]
    else:
        _sel_keys = DEFAULT_ADV_KEYS
        _col_indices = [_all_key_map[k] for k in _sel_keys]
    headers = [_all_headers[i] for i in _col_indices]

    total_outstanding_all = 0
    total_bills_all = 0
    total_amount_all = 0
    for item in groups:
        item_bills = item[2] if len(item) == 3 else item[1]
        for b in item_bills:
            total_bills_all += 1
            total_amount_all += b["total_bill"]
            total_outstanding_all += b["outstanding_amount"]

    group_label_singular = {"sector": "Sector", "zone": "Zone", "staff": "Staff"}.get(group_type, "")
    group_label_plural = {"sector": "Sectors", "zone": "Zones", "staff": "Staff"}.get(group_type, "")

    buf = io.BytesIO()
    margin = 4 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        topMargin=8 * mm,
        bottomMargin=6 * mm,
        leftMargin=margin,
        rightMargin=margin,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PDFTitle", parent=styles["Heading1"], fontSize=16, textColor=ACCENT, alignment=1, spaceAfter=3 * mm, fontName="Helvetica-Bold")
    summary_style = ParagraphStyle("PDFSummary", parent=styles["Normal"], fontSize=9, alignment=0, spaceAfter=1 * mm, textColor=colors.HexColor("#333333"), leading=13)
    group_heading_style = ParagraphStyle("GroupHeading", parent=styles["Heading2"], fontSize=12, textColor=ACCENT, spaceBefore=4 * mm, spaceAfter=1 * mm, fontName="Helvetica-Bold", alignment=0)
    group_sub_style = ParagraphStyle("GroupSub", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#555555"), spaceAfter=1.5 * mm, alignment=0, leading=11)

    elements = [Paragraph(f"Advanced Bill Filter Report — {group_label_plural}", title_style)]
    elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}", summary_style))
    elements.append(Paragraph(f"<b>Filters:</b> {filters_applied}", summary_style))
    elements.append(Paragraph(f"<b>Total Bills:</b> {total_bills_all:,} &nbsp;&nbsp; <b>Total Outstanding:</b> Rs. {fmt(total_outstanding_all)}", summary_style))
    elements.append(Spacer(1, 3 * mm))

    n = len(headers)
    page_w = landscape(A4)[0] - margin - margin
    col_widths = _calc_col_widths(headers, page_w, n)

    left_cols = {i for i, h in enumerate(headers) if h == "Consumer Name"}

    page_h = landscape(A4)[1] - 8 * mm - 6 * mm
    wrapper = _GroupedPdfWrapper(doc, elements, headers, col_widths, group_heading_style, group_sub_style, group_label_singular, _col_indices, group_type, left_cols, page_h)

    for item in groups:
        if len(item) == 3:
            wrapper.add_staff_group(item[0], item[1], item[2])
        else:
            wrapper.add_group(item[0], item[1])

    wrapper.finish()
    buf.seek(0)
    return buf.getvalue()


class _GroupedPdfWrapper:
    """Helper to write grouped PDF sections with smart pagination and staff zone support."""

    _ROW_H = 6.5        # mm – estimated body row height (with padding)
    _TOTAL_ROW_H = 7.5  # mm – estimated grand total row height

    def __init__(self, doc, elements, headers, col_widths, group_heading_style, group_sub_style, group_label, col_indices, group_type, left_cols, page_h):
        self.doc = doc
        self.elements = elements
        self.headers = headers
        self.col_widths = col_widths
        self.group_heading_style = group_heading_style
        self.group_sub_style = group_sub_style
        self.group_label = group_label
        self.col_indices = col_indices
        self.group_type = group_type
        self.left_cols = left_cols
        self._page_h = page_h       # usable height per page
        self._used = 30 * mm        # title block: title + 3 summary lines + spacer
        self._zone_label = ""       # current zone being rendered (staff-wise)

    # ------------------------------------------------------------------
    # Height estimation helpers
    # ------------------------------------------------------------------
    def _est(self, n_rows: int, sub_count: int = 0) -> float:
        """Estimated mm needed for a group: heading + sub-lines + table header + body + total."""
        heading = 9 * mm          # spaceBefore 4mm + text ~4mm + spaceAfter 1mm
        sub = sub_count * 5 * mm
        summary = 5 * mm          # leading 11pt + spaceAfter 1.5mm
        spacer = 2 * mm
        table_h = 7 * mm + n_rows * self._ROW_H + self._TOTAL_ROW_H
        return heading + sub + summary + spacer + table_h

    _MIN_GROUP = 45 * mm  # minimum mm needed: heading + summary + table header + 2 rows + total

    def _maybe_new_page(self, needed_mm: float):
        """Insert PageBreak before a group if remaining space is too small."""
        if self._used > 0 and self._used + self._MIN_GROUP > self._page_h:
            self.elements.append(PageBreak())
            self._used = 0

    def _track(self, added_mm: float):
        self._used += added_mm
        if self._used >= self._page_h:
            self._used = self._used % self._page_h

    # ------------------------------------------------------------------
    # Group rendering methods
    # ------------------------------------------------------------------
    def add_group(self, group_key, group_bills):
        needed = self._est(len(group_bills))
        self._maybe_new_page(needed)
        self._write_heading(f"{self.group_label}: {group_key}")
        self._write_summary(group_bills)
        self._add_detail_table(group_bills)

    def add_staff_group(self, zone, staff_name, group_bills):
        if zone != self._zone_label:
            needed = 9 * mm + self._est(len(group_bills), sub_count=1)
            self._maybe_new_page(needed)
            self._write_heading(f"Zone: {zone}")
            self._zone_label = zone
        else:
            needed = self._est(len(group_bills), sub_count=1)
            self._maybe_new_page(needed)

        self._write_staff_heading(staff_name, group_bills)
        self._write_summary(group_bills)
        self._add_detail_table(group_bills)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _write_heading(self, text):
        self.elements.append(Paragraph(text, self.group_heading_style))
        self._track(9 * mm)

    def _write_staff_heading(self, staff_name, bills):
        display = fmt_staff_name(staff_name).replace("\n", " / ")
        self.elements.append(Paragraph(f"Staff: {display}", self.group_heading_style))

        zones = sorted(set(b["zone"] for b in bills if b.get("zone")), key=lambda z: (_zone_sort_key(z)[0], z.lower()))
        if not zones:
            zones = ["Unknown"]
        zone_prefix = "Zones" if len(zones) > 1 else "Zone"
        self.elements.append(Paragraph(f"<b>{zone_prefix}:</b> {', '.join(zones)}", self.group_sub_style))
        self._track(5 * mm)

        sectors = sorted(set(b["sector"] for b in bills if b.get("sector")))
        ctx_parts = []
        if sectors:
            ctx_parts.append(f"<b>Sectors:</b> {', '.join(sectors)}")
        if ctx_parts:
            self.elements.append(Paragraph(" &nbsp;|&nbsp; ".join(ctx_parts), self.group_sub_style))
            self._track(5 * mm)
        self._track(9 * mm)

    def _write_summary(self, bills):
        total_b = len(bills)
        total_amt = sum(b["total_bill"] for b in bills)
        total_rec = sum(b["amount_received"] for b in bills)
        total_out = sum(b["outstanding_amount"] for b in bills)
        total_arr = sum(b["arrears"] for b in bills)
        self.elements.append(Paragraph(
            f"<b>Bills:</b> {total_b:,} &nbsp;|&nbsp; <b>Total Amount:</b> Rs. {fmt(total_amt)} &nbsp;|&nbsp; "
            f"<b>Received:</b> Rs. {fmt(total_rec)} &nbsp;|&nbsp; <b>Outstanding:</b> Rs. {fmt(total_out)} &nbsp;|&nbsp; "
            f"<b>Arrears:</b> Rs. {fmt(total_arr)}",
            self.group_sub_style,
        ))
        self.elements.append(Spacer(1, 2 * mm))
        self._track(5 * mm + 2 * mm)

    def _add_detail_table(self, group_bills):
        hdr_style = ParagraphStyle("GpHdr", fontSize=8, leading=10, alignment=1, textColor=HEADER_FG, fontName="Helvetica-Bold")
        wrapped_headers = [Paragraph(str(h), hdr_style) for h in self.headers]
        data = [wrapped_headers]

        for idx, bill in enumerate(group_bills, start=1):
            _full = [
                idx,
                bill["bill_no"] or "",
                bill["reference_no"] or "",
                bill["connection_no"] or "",
                bill.get("consumer_name") or "",
                bill["sector"],
                bill["locality"],
                bill["zone"],
                fmt(bill["total_bill"]),
                fmt(bill["arrears"]),
                fmt(bill["amount_received"]),
                fmt(bill["outstanding_amount"]),
                bill["status"] or "",
                bill.get("consumer_mobile") or "",
            ]
            row = [_full[i] for i in self.col_indices]
            data.append(row)

        g_total_b = sum(b["total_bill"] for b in group_bills)
        g_total_r = sum(b["amount_received"] for b in group_bills)
        g_total_o = sum(b["outstanding_amount"] for b in group_bills)
        g_total_a = sum(b["arrears"] for b in group_bills)
        _full_g = ["", "", "", "", "", "", "", "Group Total", fmt(g_total_b), fmt(g_total_a), fmt(g_total_r), fmt(g_total_o), "", ""]
        grand_row = [_full_g[i] for i in self.col_indices]
        data.append(grand_row)

        body_rows = wrap_pdf_body_cells(data[1:], font_size=7, left_columns=self.left_cols)
        all_rows = [data[0]] + body_rows

        t = _make_pdf_table(
            all_rows,
            col_widths=self.col_widths,
            header_font_size=8,
            body_font_size=7,
            cell_padding=5,
            left_cols=self.left_cols,
        )
        self.elements.append(t)
        self.elements.append(Spacer(1, 3 * mm))
        table_est = 7 * mm + len(group_bills) * self._ROW_H + self._TOTAL_ROW_H + 3 * mm
        self._track(table_est)

    def finish(self):
        self.doc.build(self.elements)


def _calc_col_widths(headers, page_w, n):
    """Calculate column widths proportional to content, scaled to fill page_w."""
    prop = {
        "Sr": 3.5,
        "Bill No": 9,
        "Reference No": 9,
        "Connection No": 11,
        "Consumer Name": 24,
        "Sector": 9,
        "Locality": 14,
        "Zone": 7,
        "Total Bill": 10,
        "Arrears": 10,
        "Amount Received": 10,
        "Outstanding": 10,
        "Status": 7,
        "Mobile No": 12,
    }
    widths = []
    total_p = 0
    for h in headers:
        p = prop.get(h, 10)
        widths.append(p)
        total_p += p
    if total_p > 0:
        widths = [page_w * w / total_p for w in widths]
    return widths


def sanitize_filename(name: str) -> str:
    safe = re.sub(r'[<>:"/\\|?*]', '_', name)
    safe = safe.replace(' ', '_')
    safe = re.sub(r'_+', '_', safe)
    safe = safe.strip('_.')
    return safe or "Unknown"


def generate_single_group_pdf(
    group_type: str,
    group_key: str,
    group_bills: list,
    filters_applied: str,
    cols_param: str = None,
    staff_zone: str = None,
) -> bytes:
    _all_headers = ["Sr", "Bill No", "Reference No", "Connection No", "Consumer Name", "Sector", "Locality", "Zone", "Total Bill", "Arrears", "Amount Received", "Outstanding", "Status", "Mobile No"]
    _all_col_keys = ["sr", "billNo", "referenceNo", "connectionNo", "consumerName", "sector", "locality", "zone", "totalBills", "arrearsReceived", "totalReceivedAmount", "outstanding", "status", "mobileNo"]
    _all_key_map = {k: i for i, k in enumerate(_all_col_keys)}
    if cols_param:
        _sel_keys = [k.strip() for k in cols_param.split(",") if k.strip() in _all_col_keys]
        _col_indices = [_all_key_map[k] for k in _sel_keys]
    else:
        _sel_keys = DEFAULT_ADV_KEYS
        _col_indices = [_all_key_map[k] for k in _sel_keys]
    headers = [_all_headers[i] for i in _col_indices]

    total_bills = len(group_bills)
    total_amount = sum(b["total_bill"] for b in group_bills)
    total_outstanding = sum(b["outstanding_amount"] for b in group_bills)

    group_label = {"sector": "Sector", "zone": "Zone", "staff": "Staff"}.get(group_type, "")

    buf = io.BytesIO()
    margin = 4 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        topMargin=8 * mm,
        bottomMargin=6 * mm,
        leftMargin=margin,
        rightMargin=margin,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("PDFTitle", parent=styles["Heading1"], fontSize=16, textColor=ACCENT, alignment=1, spaceAfter=3 * mm, fontName="Helvetica-Bold")
    summary_style = ParagraphStyle("PDFSummary", parent=styles["Normal"], fontSize=9, alignment=0, spaceAfter=1 * mm, textColor=colors.HexColor("#333333"), leading=13)
    group_heading_style = ParagraphStyle("GroupHeading", parent=styles["Heading2"], fontSize=12, textColor=ACCENT, spaceBefore=4 * mm, spaceAfter=1 * mm, fontName="Helvetica-Bold", alignment=0)
    group_sub_style = ParagraphStyle("GroupSub", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#555555"), spaceAfter=1.5 * mm, alignment=0, leading=11)

    elements = [Paragraph(f"Advanced Bill — {group_label}: {group_key}", title_style)]
    elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}", summary_style))
    elements.append(Paragraph(f"<b>Filters:</b> {filters_applied}", summary_style))
    elements.append(Paragraph(f"<b>Total Bills:</b> {total_bills:,} &nbsp;&nbsp; <b>Total Outstanding:</b> Rs. {fmt(total_outstanding)}", summary_style))
    elements.append(Spacer(1, 3 * mm))

    n = len(headers)
    page_w = landscape(A4)[0] - margin - margin
    col_widths = _calc_col_widths(headers, page_w, n)

    left_cols = {i for i, h in enumerate(headers) if h == "Consumer Name"}

    page_h = landscape(A4)[1] - 8 * mm - 6 * mm
    wrapper = _GroupedPdfWrapper(doc, elements, headers, col_widths, group_heading_style, group_sub_style, group_label, _col_indices, group_type, left_cols, page_h)

    if group_type == "staff" and staff_zone:
        wrapper.add_staff_group(staff_zone, group_key, group_bills)
    else:
        wrapper.add_group(group_key, group_bills)

    wrapper.finish()
    buf.seek(0)
    return buf.getvalue()


def generate_zip_of_group_pdfs(
    group_type: str,
    groups: list[tuple],
    filters_applied: str,
    cols_param: str = None,
) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        filenames_used = set()
        for item in groups:
            if group_type == "staff":
                zone, staff_name, group_bills = item
                base_name = sanitize_filename(f"Staff_{staff_name}")
                pdf_bytes = generate_single_group_pdf(group_type, staff_name, group_bills, filters_applied, cols_param, staff_zone=zone)
            elif group_type == "zone":
                zone_name, group_bills = item
                base_name = sanitize_filename(f"Zone_{zone_name}")
                pdf_bytes = generate_single_group_pdf(group_type, zone_name, group_bills, filters_applied, cols_param)
            elif group_type == "sector":
                sector_name, group_bills = item
                base_name = sanitize_filename(f"Sector_{sector_name}")
                pdf_bytes = generate_single_group_pdf(group_type, sector_name, group_bills, filters_applied, cols_param)
            else:
                continue
            filename = f"{base_name}.pdf"
            if filename in filenames_used:
                counter = 2
                while f"{base_name}_{counter}.pdf" in filenames_used:
                    counter += 1
                filename = f"{base_name}_{counter}.pdf"
            filenames_used.add(filename)
            zf.writestr(filename, pdf_bytes)
    buf.seek(0)
    return buf


# Default selected column keys for Advanced Bill Checking in display order
DEFAULT_ADV_KEYS = ["sr", "connectionNo", "consumerName", "mobileNo", "locality", "totalBills", "arrearsReceived", "outstanding"]


def generate_advanced_filtered_pdf(bills: list[dict], filters_applied: str, show_summary: bool = True, cols_param: str = None) -> bytes:
    if not bills:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=15*mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, textColor=ACCENT, alignment=1)
        elements = [Paragraph("Advanced Bill Filter Report", title_style), Paragraph("No bills match the selected filters.", styles["Normal"])]
        doc.build(elements)
        buf.seek(0)
        return buf.getvalue()

    _all_headers = ["Sr", "Bill No", "Reference No", "Connection No", "Consumer Name", "Sector", "Locality", "Zone", "Total Bill", "Arrears", "Amount Received", "Outstanding", "Status", "Mobile No"]
    _all_col_keys = ["sr", "billNo", "referenceNo", "connectionNo", "consumerName", "sector", "locality", "zone", "totalBills", "arrearsReceived", "totalReceivedAmount", "outstanding", "status", "mobileNo"]
    _all_key_map = {k: i for i, k in enumerate(_all_col_keys)}
    if cols_param:
        _sel_keys = [k.strip() for k in cols_param.split(",") if k.strip() in _all_col_keys]
        _pdf_col_indices = [_all_key_map[k] for k in _sel_keys]
    else:
        _sel_keys = DEFAULT_ADV_KEYS
        _pdf_col_indices = [_all_key_map[k] for k in _sel_keys]
    headers = [_all_headers[i] for i in _pdf_col_indices]

    rows = []
    for idx, bill in enumerate(bills, start=1):
        _full_row = [
            idx,
            bill["bill_no"] or "",
            bill["reference_no"] or "",
            bill["connection_no"] or "",
            bill.get("consumer_name") or "",
            bill["sector"],
            bill["locality"],
            bill["zone"],
            fmt(bill["total_bill"]),
            fmt(bill["arrears"]),
            fmt(bill["amount_received"]),
            fmt(bill["outstanding_amount"]),
            bill["status"] or "",
            bill.get("consumer_mobile") or "",
        ]
        rows.append([_full_row[i] for i in _pdf_col_indices])

    total_bill = sum(b["total_bill"] for b in bills)
    amount_received = sum(b["amount_received"] for b in bills)
    outstanding = sum(b["outstanding_amount"] for b in bills)
    _full_grand = ["", "", "", "", "", "", "", "Grand Total", fmt(total_bill), fmt(amount_received), fmt(outstanding), "", "", ""]
    grand_total = [_full_grand[i] for i in _pdf_col_indices]

    page_w = landscape(A4)[0] - 8 * mm
    n = len(headers)
    col_widths = _calc_col_widths(headers, page_w, n)

    left_cols = {i for i, h in enumerate(headers) if h == "Consumer Name"}

    summary_lines = [
        f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}",
        f"<b>Filters:</b> {filters_applied}",
        f"<b>Total Bills:</b> {len(bills)}",
        f"<b>Total Outstanding:</b> Rs. {fmt(outstanding)}",
    ] if show_summary else []

    return generate_card_pdf(
        "Advanced Bill Filter Report",
        summary_lines,
        headers,
        rows,
        grand_total,
        pagesize=landscape(A4),
        col_widths=col_widths,
        left_cols=left_cols,
        header_font_size=8,
        body_font_size=8,
        cell_padding=6,
    )


def export_advanced_bills_response(fmt_type: str, bills: list[dict], filters_applied: str, show_summary: bool = True, cols_param: str = None, group_by: str = "normal"):
    if not bills:
        flash("No bills match the selected filters.")
        return redirect(url_for("bill_list"))

    # Unified 14-column set matching PDF format
    _all_headers_adv = ["Sr", "Bill No", "Reference No", "Connection No", "Consumer Name", "Sector", "Locality", "Zone", "Total Bill", "Arrears", "Amount Received", "Outstanding", "Status", "Mobile No"]
    _all_adv_keys = ["sr", "billNo", "referenceNo", "connectionNo", "consumerName", "sector", "locality", "zone", "totalBills", "arrearsReceived", "totalReceivedAmount", "outstanding", "status", "mobileNo"]
    _adv_key_map = {k: i for i, k in enumerate(_all_adv_keys)}
    if cols_param:
        _sel = [k.strip() for k in cols_param.split(",") if k.strip() in _all_adv_keys]
        _adv_cols = [_adv_key_map[k] for k in _sel]
    else:
        _sel = DEFAULT_ADV_KEYS
        _adv_cols = [_adv_key_map[k] for k in _sel]
    headers = [_all_headers_adv[i] for i in _adv_cols]
    rows = [
        [
            idx,
            bill["bill_no"] or "",
            bill["reference_no"] or "",
            bill["connection_no"] or "",
            bill.get("consumer_name") or "",
            bill["sector"],
            bill["locality"],
            bill["zone"],
            bill["total_bill"],
            bill["arrears"],
            bill["amount_received"],
            bill["outstanding_amount"],
            bill["status"] or "",
            bill.get("consumer_mobile") or "",
        ]
        for idx, bill in enumerate(bills, start=1)
    ]
    rows = [[r[i] for i in _adv_cols] for r in rows]
    # Find mobile column index in filtered output
    mobile_col_idx = None
    for ci, h in enumerate(headers):
        if h == "Mobile No":
            mobile_col_idx = ci
            break

    filename = f"advanced_bills_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    if fmt_type == "pdf":
        if group_by in ("sector", "zone", "staff"):
            groups = group_bills(bills, group_by)
            pdf_bytes = generate_grouped_advanced_pdf(group_by, groups, filters_applied, cols_param=cols_param)
        else:
            pdf_bytes = generate_advanced_filtered_pdf(bills, filters_applied, show_summary=show_summary, cols_param=cols_param)
        return Response(pdf_bytes, mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}.pdf"})

    if fmt_type == "csv":
        if mobile_col_idx is not None:
            for r in rows:
                mv = r[mobile_col_idx]
                if mv and mv != "-" and mv[0].isdigit():
                    r[mobile_col_idx] = '="' + mv + '"'
        df = pd.DataFrame(rows, columns=headers)
        csv_data = df.to_csv(index=False)
        return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}.csv"})

    if fmt_type == "xlsx":
        buf = io.BytesIO()
        df = pd.DataFrame(rows, columns=headers)
        if mobile_col_idx is not None:
            from openpyxl.utils import get_column_letter
            with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                ws = writer.sheets['Sheet1']
                col_letter = get_column_letter(mobile_col_idx + 1)
                for ri in range(2, len(rows) + 2):
                    ws[f'{col_letter}{ri}'].number_format = '@'
            buf.seek(0)
        else:
            df.to_excel(buf, index=False)
            buf.seek(0)
        return Response(buf.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"})

    flash("Unknown export format.")
    return redirect(url_for("bill_list"))


def build_unpaid_amount_summary(conn, bill_ids: set[int] | None = None) -> dict:
    _bid_sql = ""
    _bid_sql_b = ""
    if bill_ids is not None:
        if not bill_ids:
            _bid_sql = "AND 1=0"
            _bid_sql_b = "AND 1=0"
        else:
            id_list = ",".join(str(i) for i in bill_ids)
            _bid_sql = f"AND id IN ({id_list})"
            _bid_sql_b = f"AND b.id IN ({id_list})"

    metric_select = """
        COUNT(*) AS bill_count,
        SUM(COALESCE(total_bill, 0)) AS total_bill_amount,
        SUM(COALESCE(arrears, 0)) AS total_arrears_amount,
        SUM(COALESCE(total_bill, 0) - COALESCE(arrears, 0)) AS current_bill_amount
    """
    total = conn.execute(
        f"""
        SELECT {metric_select}
        FROM bills
        WHERE {UNPAID_STATUS_SQL}
        {_bid_sql}
        """
    ).fetchone()

    sector_rows = conn.execute(
        f"""
        SELECT sector AS name, {metric_select}
        FROM bills
        WHERE {UNPAID_STATUS_SQL}
        {_bid_sql}
        GROUP BY sector
        ORDER BY LOWER(sector)
        """
    ).fetchall()

    zone_rows = conn.execute(
        f"""
        SELECT zone AS name, {metric_select}
        FROM bills
        WHERE {UNPAID_STATUS_SQL}
        {_bid_sql}
        GROUP BY zone
        ORDER BY {zone_sort_expr('zone')}, LOWER(zone)
        """
    ).fetchall()

    has_auto_rules = conn.execute("SELECT COUNT(*) AS cnt FROM auto_assignment_rules").fetchone()["cnt"] > 0
    unpaid_where = UNPAID_STATUS_SQL.replace("status", "b.status")

    if has_auto_rules:
        auto_exclude_clause = "AND NOT EXISTS (SELECT 1 FROM auto_assignment_rules aar WHERE aar.sector = b.sector AND aar.locality = b.locality)"
        auto_assign_sql = f"""
        UNION ALL
        SELECT
            s.name AS name,
            COUNT(b.id) AS bill_count,
            SUM(COALESCE(b.total_bill, 0)) AS total_bill_amount,
            SUM(COALESCE(b.arrears, 0)) AS total_arrears_amount,
            SUM(COALESCE(b.total_bill, 0) - COALESCE(b.arrears, 0)) AS current_bill_amount
        FROM bills b
        JOIN auto_assignment_rules aar
            ON aar.sector = b.sector AND aar.locality = b.locality
            AND CAST(b.connection_no AS TEXT) >= aar.connection_min
            AND (aar.connection_max IS NULL OR CAST(b.connection_no AS TEXT) <= aar.connection_max)
        JOIN staff s ON UPPER(TRIM(s.name)) = UPPER(TRIM(aar.staff_name))
        WHERE {unpaid_where}
        {_bid_sql_b}
        GROUP BY s.id, s.name
        """
    else:
        auto_exclude_clause = ""
        auto_assign_sql = ""

    staff_rows = conn.execute(
        f"""
        SELECT
            s.name AS name,
            COUNT(b.id) AS bill_count,
            SUM(COALESCE(b.total_bill, 0)) AS total_bill_amount,
            SUM(COALESCE(b.arrears, 0)) AS total_arrears_amount,
            SUM(COALESCE(b.total_bill, 0) - COALESCE(b.arrears, 0)) AS current_bill_amount
        FROM staff_assignments sa
        JOIN staff s ON s.id = sa.staff_id
        JOIN bills b
            ON b.zone = sa.zone
            AND (sa.sector IS NULL OR b.sector = sa.sector)
            AND (sa.locality IS NULL OR b.locality = sa.locality)
            {auto_exclude_clause}
        WHERE {unpaid_where}
        {_bid_sql_b}
        GROUP BY s.id, s.name

        {auto_assign_sql}

        UNION ALL
        SELECT
            'Unassigned' AS name,
            COUNT(b.id) AS bill_count,
            SUM(COALESCE(b.total_bill, 0)) AS total_bill_amount,
            SUM(COALESCE(b.arrears, 0)) AS total_arrears_amount,
            SUM(COALESCE(b.total_bill, 0) - COALESCE(b.arrears, 0)) AS current_bill_amount
        FROM bills b
        WHERE {unpaid_where}
        {_bid_sql_b}
          AND NOT EXISTS (
              SELECT 1
              FROM staff_assignments sa
              WHERE sa.zone = b.zone
                AND (sa.sector IS NULL OR sa.sector = b.sector)
                AND (sa.locality IS NULL OR sa.locality = b.locality)
          )
          {('AND NOT EXISTS (SELECT 1 FROM auto_assignment_rules aar WHERE aar.sector = b.sector AND aar.locality = b.locality)' if has_auto_rules else '')}
        HAVING COUNT(b.id) > 0
        ORDER BY name
        """
    ).fetchall()

    def to_amount_row(row, idx: int | None = None) -> dict:
        item = {
            "name": row["name"] if row["name"] else "Unknown",
            "bill_count": int(row["bill_count"] or 0),
            "total_bill_amount": float(row["total_bill_amount"] or 0),
            "total_arrears_amount": float(row["total_arrears_amount"] or 0),
            "current_bill_amount": float(row["current_bill_amount"] or 0),
        }
        if idx is not None:
            item["sr"] = idx
        return item

    return {
        "total": {
            "bill_count": int(total["bill_count"] or 0),
            "total_bill_amount": float(total["total_bill_amount"] or 0),
            "total_arrears_amount": float(total["total_arrears_amount"] or 0),
            "current_bill_amount": float(total["current_bill_amount"] or 0),
        },
        "sector_rows": [to_amount_row(row, idx) for idx, row in enumerate(sector_rows, start=1)],
        "zone_rows": [to_amount_row(row, idx) for idx, row in enumerate(zone_rows, start=1)],
        "staff_rows": [to_amount_row(row, idx) for idx, row in enumerate(staff_rows, start=1)],
    }


def get_bill_list_context():
    init_bill_list_db()
    with get_db() as conn:
        unpaid_amount_summary = build_unpaid_amount_summary(conn)
        for row in unpaid_amount_summary["staff_rows"]:
            row["name"] = fmt_staff_name(row["name"])
        rows = conn.execute(
            """
            SELECT
                sector,
                COUNT(*) AS total_bills,
                SUM(CASE WHEN amount_received > 0 THEN 1 ELSE 0 END) AS received_bills,
                SUM(amount_received) AS total_received_amount,
                SUM(CASE WHEN total_bill > amount_received THEN total_bill - amount_received ELSE 0 END) AS remaining_amount
            FROM bills
            GROUP BY sector
            ORDER BY sector
            """
        ).fetchall()
        report_rows = []
        for idx, row in enumerate(rows, start=1):
            total_bills = int(row["total_bills"] or 0)
            received_bills = int(row["received_bills"] or 0)
            report_rows.append(
                {
                    "sr": idx,
                    "sector": row["sector"],
                    "total_bills": total_bills,
                    "received_bills": received_bills,
                    "remaining_bills": total_bills - received_bills,
                    "total_received_amount": float(row["total_received_amount"] or 0),
                    "remaining_amount": float(row["remaining_amount"] or 0),
                }
            )

        summary = conn.execute(
            """
            SELECT
                COUNT(*) AS total_bills,
                COUNT(DISTINCT NULLIF(connection_no, '')) AS total_connections,
                SUM(CASE WHEN amount_received > 0 THEN 1 ELSE 0 END) AS received_bills,
                SUM(amount_received) AS total_received_amount,
                SUM(CASE WHEN total_bill > amount_received THEN total_bill - amount_received ELSE 0 END) AS remaining_amount
            FROM bills
            """
        ).fetchone()
        total_connections = int(summary["total_connections"] or 0)
        total_bills = int(summary["total_bills"] or 0)
        if total_connections == 0:
            total_connections = total_bills
        received_bills = int(summary["received_bills"] or 0)

        zones = conn.execute(
            """
            SELECT zone, sector, COUNT(DISTINCT locality) AS locality_count, COUNT(*) AS bill_count
            FROM bills
            GROUP BY zone, sector
            ORDER BY CASE zone WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 WHEN 'Commercial' THEN 4 ELSE 5 END, sector
            """
        ).fetchall()
        localities = conn.execute(
            """
            SELECT zone, sector, locality
            FROM localities
            ORDER BY CASE zone WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 WHEN 'Commercial' THEN 4 ELSE 5 END, sector, locality
            """
        ).fetchall()
        staff = conn.execute("SELECT id, name FROM staff ORDER BY name").fetchall()
        assignments = conn.execute(
            """
            SELECT
                sa.id,
                sa.staff_id,
                s.name,
                sa.zone,
                COALESCE(sa.sector, 'All sectors') AS sector,
                COALESCE(sa.locality, '') AS locality
            FROM staff_assignments sa
            JOIN staff s ON s.id = sa.staff_id
            ORDER BY sa.zone, sa.sector, sa.locality, s.name
            """
        ).fetchall()
        sectors = conn.execute(
            f"""
            SELECT name AS sector, zone
            FROM sectors
            ORDER BY {zone_sort_expr('zone')}, LOWER(name)
            """
        ).fetchall()
        assigned_options = conn.execute(
            """
            SELECT
                sa.staff_id,
                sa.zone,
                COALESCE(sa.sector, '*') AS sector,
                COALESCE(sa.locality, '*') AS locality,
                s.name AS staff_name
            FROM staff_assignments sa
            JOIN staff s ON s.id = sa.staff_id
            """
        ).fetchall()

    assigned_exact = {
        f"{row['zone']}||{row['sector']}": {"name": row["staff_name"], "id": str(row["staff_id"])}
        for row in assigned_options
        if row["sector"] != "*" and row["locality"] == "*"
    }
    assigned_localities = {
        f"{row['zone']}||{row['sector']}||{row['locality']}": {"name": row["staff_name"], "id": str(row["staff_id"])}
        for row in assigned_options
        if row["sector"] != "*" and row["locality"] != "*"
    }
    assigned_zones = {
        row["zone"]: {"name": row["staff_name"], "id": str(row["staff_id"])}
        for row in assigned_options
        if row["sector"] == "*"
    }
    sector_rows_by_key = {}
    for row in sectors:
        sector = dict(row)
        key = f"{sector['zone']}||{sector['sector']}"
        assigned = assigned_zones.get(sector["zone"]) or assigned_exact.get(key)
        sector["assigned_to"] = assigned["name"] if assigned else None
        sector["assigned_staff_id"] = assigned["id"] if assigned else ""
        sector["assigned"] = assigned is not None
        sector["sector_values"] = [sector["sector"]]
        display_key = normalize_sector_key(sector["sector"])
        existing = sector_rows_by_key.get(display_key)
        if not existing:
            sector_rows_by_key[display_key] = sector
        else:
            existing["sector_values"].append(sector["sector"])
            if len(sector["sector"]) < len(existing["sector"]):
                existing["sector"] = sector["sector"]
            if existing["zone"] == "Unassigned" and sector["zone"] != "Unassigned":
                existing["zone"] = sector["zone"]
            if not existing["assigned"] and sector["assigned"]:
                existing["assigned_to"] = sector["assigned_to"]
                existing["assigned_staff_id"] = sector["assigned_staff_id"]
                existing["assigned"] = True
    sector_rows = sorted(
        sector_rows_by_key.values(),
        key=lambda row: (
            {"A": 1, "B": 2, "C": 3, "Commercial": 4, "Unassigned": 5}.get(row["zone"], 6),
            row["sector"].lower(),
        ),
    )
    locality_rows = []
    for row in localities:
        locality = dict(row)
        locality_key = f"{locality['zone']}||{locality['sector']}||{locality['locality']}"
        sector_key = f"{locality['zone']}||{locality['sector']}"
        assigned = assigned_zones.get(locality["zone"]) or assigned_exact.get(sector_key) or assigned_localities.get(locality_key)
        locality["assigned_to"] = assigned["name"] if assigned else None
        locality["assigned_staff_id"] = assigned["id"] if assigned else ""
        locality["assigned"] = assigned is not None
        locality_rows.append(locality)

    return {
        "summary": {
            "total_connections": total_connections,
            "total_bills": total_bills,
            "received_bills": received_bills,
            "remaining_bills": total_bills - received_bills,
            "total_received_amount": float(summary["total_received_amount"] or 0),
            "remaining_amount": float(summary["remaining_amount"] or 0),
        },
        "report_rows": report_rows,
        "zones": [dict(row) for row in zones],
        "localities": locality_rows,
        "staff": [dict(row) for row in staff],
        "assignments": [dict(row) for row in assignments],
        "sectors": sector_rows,
        "zone_options": ["A", "B", "C", "Commercial", "Unassigned"],
        "unpaid_amount_summary": unpaid_amount_summary,
    }


def bill_list_export_rows():
    context = get_bill_list_context()
    headers = [
        "Sr",
        "Sector",
        "Total Bills",
        "Received Bills",
        "Remaining Bills",
        "Total Received Amount",
        "Pending Amount",
    ]
    rows = [
        [
            row["sr"],
            row["sector"],
            fmt(row["total_bills"]),
            fmt(row["received_bills"]),
            fmt(row["remaining_bills"]),
            fmt(row["total_received_amount"]),
            fmt(row["remaining_amount"]),
        ]
        for row in context["report_rows"]
    ]
    return headers, rows, context["summary"]


def unpaid_amount_export_data():
    init_bill_list_db()
    with get_db() as conn:
        summary = build_unpaid_amount_summary(conn)

    amount_headers = [
        "Sr",
        "Name",
        "Bills",
        "Total Bill Amount",
        "Total Arrears Amount",
        "Current Bill Amount",
    ]
    total = summary["total"]
    summary_headers = ["Bills", "Total Bill Amount", "Total Arrears Amount", "Current Bill Amount"]
    summary_rows = [[
        fmt(total["bill_count"]),
        fmt(total["total_bill_amount"]),
        fmt(total["total_arrears_amount"]),
        fmt(total["current_bill_amount"]),
    ]]

    def make_rows(source_rows: list[dict], *, is_staff: bool = False) -> list[list]:
        return [
            [
                row["sr"],
                fmt_staff_name(row["name"]) if is_staff else row["name"],
                fmt(row["bill_count"]),
                fmt(row["total_bill_amount"]),
                fmt(row["total_arrears_amount"]),
                fmt(row["current_bill_amount"]),
            ]
            for row in source_rows
        ]

    sections = [
        ("summary", "Summary Totals", summary_headers, summary_rows),
        ("sector", "Sector-wise", amount_headers, make_rows(summary["sector_rows"])),
        ("zone", "Zone-wise", amount_headers, make_rows(summary["zone_rows"])),
        ("staff", "Staff-wise", amount_headers, make_rows(summary["staff_rows"], is_staff=True)),
    ]
    return sections, total


def unpaid_amount_section(sections: list[tuple[str, str, list[str], list[list]]], section_key: str):
    for key, title, headers, rows in sections:
        if key == section_key:
            return key, title, headers, rows
    return None


def generate_unpaid_amount_pdf(sections: list[tuple[str, str, list[str], list[list]]], total: dict, show_summary: bool = True) -> bytes:
    buf = io.BytesIO()
    pagesize = landscape(A4)
    left_margin = right_margin = 15 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        topMargin=18 * mm,
        bottomMargin=14 * mm,
        leftMargin=left_margin,
        rightMargin=right_margin,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "UnpaidAmountTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=ACCENT,
        alignment=1,
        spaceAfter=5 * mm,
        fontName="Helvetica-Bold",
    )
    section_style = ParagraphStyle(
        "UnpaidAmountSection",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#333333"),
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
        fontName="Helvetica-Bold",
    )
    summary_style = ParagraphStyle(
        "UnpaidAmountSummary",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#333333"),
        spaceAfter=1 * mm,
    )
    elements = [
        Paragraph("Unpaid & Expired Bill Amounts", title_style),
    ]
    if show_summary:
        elements.extend([
            Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}", summary_style),
            Paragraph(f"<b>Bills:</b> {fmt(total['bill_count'])}", summary_style),
            Paragraph(f"<b>Total Bill Amount:</b> Rs. {fmt(total['total_bill_amount'])}", summary_style),
            Paragraph(f"<b>Total Arrears Amount:</b> Rs. {fmt(total['total_arrears_amount'])}", summary_style),
            Paragraph(f"<b>Current Bill Amount:</b> Rs. {fmt(total['current_bill_amount'])}", summary_style),
            Spacer(1, 4 * mm),
        ])
    page_w = pagesize[0] - left_margin - right_margin
    for _, title, headers, rows in sections:
        section_rows = rows or [["", "No unpaid or expired bills found.", "", "", "", ""][:len(headers)]]
        if len(headers) == 4:
            col_widths = [page_w * 0.18, page_w * 0.27, page_w * 0.27, page_w * 0.28]
            left_cols = []
        else:
            col_widths = [page_w * 0.05, page_w * 0.35, page_w * 0.10, page_w * 0.17, page_w * 0.17, page_w * 0.16]
            left_cols = [1]
        elements.append(Paragraph(title, section_style))
        elements.append(
            _make_pdf_table(
                [headers] + section_rows,
                col_widths=col_widths,
                left_cols=left_cols,
                header_font_size=8,
                body_font_size=8,
                cell_padding=5,
            )
        )
        elements.append(Spacer(1, 4 * mm))
    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


def zone_sort_expr(column_name: str = "zone") -> str:
    return f"CASE {column_name} WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 WHEN 'Commercial' THEN 4 ELSE 5 END"


def bill_list_zone_export_rows(selected_zone: str = "All"):
    init_bill_list_db()
    headers = [
        "Sr",
        "Zone",
        "Sector",
        "Total Bills",
        "Received Bills",
        "Remaining Bills",
        "Amount Received",
        "Pending Amount",
    ]
    zone_filter = "" if selected_zone == "All" else "WHERE zone = ?"
    params = () if selected_zone == "All" else (selected_zone,)
    with get_db() as conn:
        data = conn.execute(
            f"""
            SELECT
                zone,
                sector,
                COUNT(*) AS total_bills,
                SUM(CASE WHEN amount_received > 0 THEN 1 ELSE 0 END) AS received_bills,
                SUM(amount_received) AS total_received_amount,
                SUM(CASE WHEN total_bill > amount_received THEN total_bill - amount_received ELSE 0 END) AS remaining_amount
            FROM bills
            {zone_filter}
            GROUP BY zone, sector
            ORDER BY {zone_sort_expr('zone')}, sector
            """,
            params,
        ).fetchall()
    def make_total_row(label: str, source_rows: list[list], zone: str = "") -> list:
        return [
            "",
            zone,
            label,
            fmt(sum(parse_number(str(row[3]).replace(",", "")) for row in source_rows)),
            fmt(sum(parse_number(str(row[4]).replace(",", "")) for row in source_rows)),
            fmt(sum(parse_number(str(row[5]).replace(",", "")) for row in source_rows)),
            fmt(sum(parse_number(str(row[6]).replace(",", "")) for row in source_rows)),
            fmt(sum(parse_number(str(row[7]).replace(",", "")) for row in source_rows)),
        ]

    base_rows = []
    for idx, row in enumerate(data, start=1):
        total_bills = int(row["total_bills"] or 0)
        received_bills = int(row["received_bills"] or 0)
        base_rows.append(
            [
                idx,
                row["zone"],
                row["sector"],
                fmt(total_bills),
                fmt(received_bills),
                fmt(total_bills - received_bills),
                fmt(row["total_received_amount"] or 0),
                fmt(row["remaining_amount"] or 0),
            ]
        )

    rows = []
    if selected_zone == "All":
        current_zone = None
        zone_rows = []
        for row in base_rows:
            if current_zone is not None and row[1] != current_zone:
                rows.extend(zone_rows)
                rows.append(make_total_row(f"{current_zone} Total", zone_rows, current_zone))
                zone_rows = []
            current_zone = row[1]
            zone_rows.append(row)
        if zone_rows:
            rows.extend(zone_rows)
            rows.append(make_total_row(f"{current_zone} Total", zone_rows, current_zone))
        if base_rows:
            rows.append(make_total_row("Grand Total", base_rows, "All"))
    else:
        rows = base_rows
        if base_rows:
            rows.append(make_total_row(f"{selected_zone} Total", base_rows, selected_zone))
    return headers, rows


def get_zone_summary_data():
    init_bill_list_db()
    with get_db() as conn:
        rows = conn.execute(
            f"""
            SELECT
                zone,
                COUNT(*) AS total_bills,
                SUM(CASE WHEN amount_received > 0 THEN 1 ELSE 0 END) AS received_bills,
                SUM(COALESCE(total_bill, 0)) AS total_amount,
                SUM(COALESCE(arrears, 0)) AS total_arrears_received,
                SUM(COALESCE(amount_received, 0)) AS total_received_amount,
                SUM(CASE WHEN COALESCE(total_bill, 0) > COALESCE(amount_received, 0)
                    THEN COALESCE(total_bill, 0) - COALESCE(amount_received, 0) ELSE 0 END) AS pending_amount
            FROM bills
            GROUP BY zone
            ORDER BY {zone_sort_expr('zone')}
            """
        ).fetchall()
    return rows


def bill_list_staff_export_rows(staff_id=None, bill_ids: set[int] | None = None):
    init_bill_list_db()
    headers = [
        "Sr",
        "Staff",
        "Zone",
        "Sector",
        "Locality",
        "Total Bills",
        "Received Bills",
        "Remaining Bills",
        "Amount Received",
        "Pending Amount",
    ]
    staff_filter = ""
    params: list = []
    if staff_id:
        staff_filter = "WHERE sa.staff_id = ?"
        params.append(staff_id)

    bill_ids_clause = ""
    if bill_ids is not None:
        if not bill_ids:
            bill_ids_clause = "AND 1=0"
        else:
            id_list = ",".join(str(i) for i in bill_ids)
            bill_ids_clause = f"AND b.id IN ({id_list})"

    with get_db() as conn:
        has_auto_rules = conn.execute("SELECT COUNT(*) AS cnt FROM auto_assignment_rules").fetchone()["cnt"] > 0

        auto_exclude = ""
        if has_auto_rules:
            auto_exclude = "AND NOT EXISTS (SELECT 1 FROM auto_assignment_rules aar WHERE aar.sector = b.sector AND aar.locality = b.locality)"

        data = conn.execute(
            f"""
            SELECT
                sa.staff_id,
                s.name AS staff_name,
                sa.zone,
                sa.sector AS assigned_sector,
                sa.locality AS assigned_locality,
                COALESCE(sa.sector, 'All sectors') AS sector,
                COALESCE(sa.locality, '') AS locality,
                COUNT(DISTINCT b.id) AS total_bills,
                COUNT(DISTINCT CASE WHEN b.amount_received > 0 THEN b.id END) AS received_bills,
                SUM(COALESCE(b.amount_received, 0)) AS total_received_amount,
                SUM(CASE WHEN b.total_bill > b.amount_received THEN b.total_bill - b.amount_received ELSE 0 END) AS remaining_amount
            FROM staff_assignments sa
            JOIN staff s ON s.id = sa.staff_id
            LEFT JOIN bills b
                ON b.zone = sa.zone
                AND (sa.sector IS NULL OR b.sector = sa.sector)
                AND (sa.locality IS NULL OR b.locality = sa.locality)
                {auto_exclude}
                {bill_ids_clause}
            {staff_filter}
            GROUP BY sa.id, s.name, sa.zone, sa.sector, sa.locality
            ORDER BY s.name, sa.zone, sa.sector, sa.locality
            """,
            params,
        ).fetchall()
        data = list(data)
        expanded_data = []
        for row in data:
            if row["zone"] == "Commercial" and not row["assigned_locality"]:
                commercial_bill_ids_clause = ""
                if bill_ids is not None:
                    if not bill_ids:
                        commercial_bill_ids_clause = "AND 1=0"
                    else:
                        id_list = ",".join(str(i) for i in bill_ids)
                        commercial_bill_ids_clause = f"AND b.id IN ({id_list})"
                commercial_rows = conn.execute(
                    f"""
                    SELECT
                        ? AS staff_id,
                        ? AS staff_name,
                        b.zone,
                        b.sector,
                        b.locality,
                        COUNT(DISTINCT b.id) AS total_bills,
                        COUNT(DISTINCT CASE WHEN b.amount_received > 0 THEN b.id END) AS received_bills,
                        SUM(COALESCE(b.amount_received, 0)) AS total_received_amount,
                        SUM(CASE WHEN b.total_bill > b.amount_received THEN b.total_bill - b.amount_received ELSE 0 END) AS remaining_amount
                    FROM bills b
                    WHERE b.zone = ?
                    {auto_exclude if auto_exclude else ''}
                    {commercial_bill_ids_clause}
                    GROUP BY b.zone, b.sector, b.locality
                    ORDER BY b.sector, b.locality
                    """,
                    (
                        row["staff_id"],
                        row["staff_name"],
                        row["zone"],
                    ),
                ).fetchall()
                expanded_data.extend(commercial_rows or [row])
            else:
                expanded_data.append(row)
        data = expanded_data

        if has_auto_rules:
            auto_params: list = []
            auto_filter_sql = ""
            if staff_id:
                auto_filter_sql = "AND s.id = ?"
                auto_params.append(staff_id)
            auto_bill_ids_clause = ""
            if bill_ids is not None:
                if not bill_ids:
                    auto_bill_ids_clause = "AND 1=0"
                else:
                    id_list = ",".join(str(i) for i in bill_ids)
                    auto_bill_ids_clause = f"AND b.id IN ({id_list})"
            auto_rows = conn.execute(
                f"""
                SELECT
                    s.id AS staff_id,
                    s.name AS staff_name,
                    b.zone,
                    b.sector AS assigned_sector,
                    b.locality AS assigned_locality,
                    b.sector,
                    b.locality,
                    COUNT(DISTINCT b.id) AS total_bills,
                    COUNT(DISTINCT CASE WHEN b.amount_received > 0 THEN b.id END) AS received_bills,
                    SUM(COALESCE(b.amount_received, 0)) AS total_received_amount,
                    SUM(CASE WHEN b.total_bill > b.amount_received THEN b.total_bill - b.amount_received ELSE 0 END) AS remaining_amount
                FROM bills b
                JOIN auto_assignment_rules aar
                    ON aar.sector = b.sector AND aar.locality = b.locality
                    AND CAST(b.connection_no AS TEXT) >= aar.connection_min
                    AND (aar.connection_max IS NULL OR CAST(b.connection_no AS TEXT) <= aar.connection_max)
                JOIN staff s ON UPPER(TRIM(s.name)) = UPPER(TRIM(aar.staff_name))
                {auto_filter_sql}
                {auto_bill_ids_clause}
                GROUP BY s.id, b.zone, b.sector, b.locality
                ORDER BY s.name, b.zone, b.sector, b.locality
                """,
                auto_params,
            ).fetchall()
            data.extend(auto_rows)

        if not staff_id:
            unassigned_bill_ids_clause = ""
            if bill_ids is not None:
                if not bill_ids:
                    unassigned_bill_ids_clause = "AND 1=0"
                else:
                    id_list = ",".join(str(i) for i in bill_ids)
                    unassigned_bill_ids_clause = f"AND b.id IN ({id_list})"
            unassigned_data = conn.execute(
                f"""
                SELECT
                    'Unassigned' AS staff_name,
                    b.zone,
                    b.sector,
                    b.locality,
                    COUNT(b.id) AS total_bills,
                    SUM(CASE WHEN b.amount_received > 0 THEN 1 ELSE 0 END) AS received_bills,
                    SUM(COALESCE(b.amount_received, 0)) AS total_received_amount,
                    SUM(CASE WHEN b.total_bill > b.amount_received THEN b.total_bill - b.amount_received ELSE 0 END) AS remaining_amount
                FROM bills b
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM staff_assignments sa
                    WHERE sa.zone = b.zone
                      AND (sa.sector IS NULL OR sa.sector = b.sector)
                      AND (sa.locality IS NULL OR sa.locality = b.locality)
                )
                {('AND NOT EXISTS (SELECT 1 FROM auto_assignment_rules aar WHERE aar.sector = b.sector AND aar.locality = b.locality)' if has_auto_rules else '')}
                {unassigned_bill_ids_clause}
                GROUP BY b.zone, b.sector, b.locality
                ORDER BY b.zone, b.sector, b.locality
                """
            ).fetchall()
            data = list(data) + list(unassigned_data)
    rows = []
    for idx, row in enumerate(data, start=1):
        total_bills = int(row["total_bills"] or 0)
        received_bills = int(row["received_bills"] or 0)
        total_received_amount = float(row["total_received_amount"] or 0)
        remaining_amount = float(row["remaining_amount"] or 0)
        if total_bills == 0 and received_bills == 0 and total_received_amount == 0 and remaining_amount == 0:
            continue
        rows.append(
            [
                idx,
                row["staff_name"],
                row["zone"],
                row["sector"],
                row["locality"],
                fmt(total_bills),
                fmt(received_bills),
                fmt(total_bills - received_bills),
                fmt(total_received_amount),
                fmt(remaining_amount),
            ]
        )
    return headers, rows


def export_table_response(fmt_type: str, title: str, headers: list[str], rows: list[list], filename: str):
    if fmt_type == "pdf":
        page_w = landscape(A4)[0] - 30 * mm
        col_widths = [page_w / len(headers)] * len(headers)
        if len(headers) == 8:
            col_widths = [
                page_w * 0.04,
                page_w * 0.09,
                page_w * 0.31,
                page_w * 0.08,
                page_w * 0.10,
                page_w * 0.10,
                page_w * 0.14,
                page_w * 0.14,
            ]
        elif len(headers) == 9:
            col_widths = [
                page_w * 0.04,
                page_w * 0.15,
                page_w * 0.08,
                page_w * 0.25,
                page_w * 0.08,
                page_w * 0.09,
                page_w * 0.09,
                page_w * 0.11,
                page_w * 0.11,
            ]
        pdf_bytes = generate_card_pdf(
            title,
            [f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}"],
            headers,
            rows,
            pagesize=landscape(A4),
            col_widths=col_widths,
            left_cols=[2] if len(headers) == 8 else [1, 3],
            header_font_size=8,
            body_font_size=8,
        )
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"},
        )
    if fmt_type == "csv":
        csv_data = pd.DataFrame(rows, columns=headers).to_csv(index=False)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"},
        )
    if fmt_type == "xlsx":
        buf = io.BytesIO()
        pd.DataFrame(rows, columns=headers).to_excel(buf, index=False)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"},
        )
    flash("Unknown export format.")
    return redirect(url_for("bill_list"))


def generate_staff_report_pdf(rows: list[list], show_summary: bool = True, cols_param: str = None, summary_cols_param: str = None) -> bytes:
    def numeric(value) -> float:
        return parse_number(str(value).replace(",", ""))

    # 10-col input: sr(0), staff(1), zone(2), sector(3), locality(4), totalBills(5), receivedBills(6), remainingBills(7), totalReceivedAmount(8), pendingAmount(9)
    # PDF 8-col: sr(0), sector(1), locality(2), totalBills(3), receivedBills(4), remainingBills(5), totalReceivedAmount(6), pendingAmount(7)
    # 10-col → PDF: {0:0, 3:1, 4:2, 5:3, 6:4, 7:5, 8:6, 9:7}
    _10TOPDF = {0: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7}
    _pdf_cols = list(range(8))
    _summary_cols = list(range(8))
    if cols_param:
        _sel = [k.strip() for k in cols_param.split(",") if k.strip() in STAFF_COL_MAP]
        _sel_set = set(_sel)
        _sel10 = set(STAFF_COL_MAP[k] for k in _sel)
        _pdf_cols = sorted([_10TOPDF[i] for i in _sel10 if i in _10TOPDF])
        # Summary cols: Sr, Staff Name, Zone, Total Assigned Bills, Total Received Bills, Remaining Bills, Amount Received, Pending Amount
        _sum_keys = ["sr", "staff", "zone", "totalBills", "receivedBills", "remainingBills", "totalReceivedAmount", "pendingAmount"]
        _summary_cols = [i for i, k in enumerate(_sum_keys) if k in _sel_set]

    def total_row(label: str, source_rows: list[list], staff_pdf_row: bool = True) -> list:
        total_bills = sum(numeric(row[5]) for row in source_rows)
        received_bills = sum(numeric(row[6]) for row in source_rows)
        remaining_bills = sum(numeric(row[7]) for row in source_rows)
        amount_received = sum(numeric(row[8]) for row in source_rows)
        pending_amount = sum(numeric(row[9]) for row in source_rows)
        if staff_pdf_row:
            return [
                "",
                label,
                "",
                fmt(total_bills),
                fmt(received_bills),
                fmt(remaining_bills),
                fmt(amount_received),
                fmt(pending_amount),
            ]
        return [
            label,
            fmt(total_bills),
            fmt(received_bills),
            fmt(remaining_bills),
            fmt(amount_received),
            fmt(pending_amount),
        ]

    buf = io.BytesIO()
    left_margin = 8 * mm
    right_margin = 8 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        topMargin=6 * mm,
        bottomMargin=6 * mm,
        leftMargin=6 * mm,
        rightMargin=6 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PDFTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=ACCENT,
        alignment=1,
        spaceAfter=6 * mm,
        fontName="Helvetica-Bold",
    )
    summary_style = ParagraphStyle(
        "PDFSummary",
        parent=styles["Normal"],
        fontSize=14,
        alignment=0,
        spaceAfter=2 * mm,
        textColor=colors.HexColor("#333333"),
        leading=18,
    )
    group_style = ParagraphStyle(
        "PDFGroup",
        parent=styles["Heading3"],
        fontSize=10,
        textColor=colors.HexColor("#222222"),
        alignment=0,
        spaceBefore=1 * mm,
        spaceAfter=0.5 * mm,
        fontName="Helvetica-Bold",
    )

    page_w = landscape(A4)[0] - left_margin - right_margin

    # ── Parse summary column selection ──
    _sum_sel = []
    if summary_cols_param:
        _sum_sel = [k.strip() for k in summary_cols_param.split(",") if k.strip() in STAFF_SUMMARY_COL_MAP]

    _sum_all_headers = [
        "Sr",
        "Staff Name",
        "Total Bills",
        "Received Bills",
        "Remaining Bills",
        "Total Amount",
        "Amount Received",
        "Pending Amount",
    ]
    _sum_all_widths = [
        page_w * 0.04,
        page_w * 0.20,
        page_w * 0.09,
        page_w * 0.09,
        page_w * 0.09,
        page_w * 0.13,
        page_w * 0.13,
        page_w * 0.13,
    ]
    _sum_pdf_cols = sorted([STAFF_SUMMARY_COL_MAP[k] for k in _sum_sel]) if _sum_sel else list(range(8))
    sum_headers = [_sum_all_headers[i] for i in _sum_pdf_cols]
    sum_widths = [_sum_all_widths[i] for i in _sum_pdf_cols]
    # left-align staff name column (index 1 in full 8-col)
    _sum_left_cols = {_sum_pdf_cols.index(1)} if 1 in _sum_pdf_cols else set()

    def wrap_sum_text(value):
        return wrap_pdf_body_cells([[value]], font_size=9)[0][0]

    def wrap_sum_left(value):
        return wrap_pdf_body_cells([[value]], font_size=9, left_columns={0})[0][0]

    grouped = {}
    for row in rows:
        grouped.setdefault((row[1], row[2]), []).append(row)

    zone_order = {"A": 1, "B": 2, "C": 3, "Commercial": 4, "Unassigned": 5}
    grouped_items = sorted(
        grouped.items(),
        key=lambda item: (
            zone_order.get(item[0][1], 99),
            -len(item[1]),
            item[0][0].lower(),
        ),
    )

    summary_data = []
    grand_total_all = {"total_bills": 0, "received_bills": 0, "remaining_bills": 0, "amount_received": 0, "pending_amount": 0}

    for (staff_name, zone), group_rows in grouped_items:
        total_bills = sum(numeric(row[5]) for row in group_rows)
        received_bills = sum(numeric(row[6]) for row in group_rows)
        remaining_bills = sum(numeric(row[7]) for row in group_rows)
        amount_received = sum(numeric(row[8]) for row in group_rows)
        pending_amount = sum(numeric(row[9]) for row in group_rows)

        summary_data.append({
            "staff_name": staff_name,
            "zone": zone,
            "total_bills": total_bills,
            "received_bills": received_bills,
            "remaining_bills": remaining_bills,
            "amount_received": amount_received,
            "pending_amount": pending_amount,
        })

        grand_total_all["total_bills"] += total_bills
        grand_total_all["received_bills"] += received_bills
        grand_total_all["remaining_bills"] += remaining_bills
        grand_total_all["amount_received"] += amount_received
        grand_total_all["pending_amount"] += pending_amount

    # ── Build elements list ──
    elements = []

    # Page 1: Staff-wise Summary Report
    if summary_data:
        _sum_full_headers = _sum_all_headers
        _sum_full_widths = _sum_all_widths
        _sum_sr_headers = [_sum_full_headers[i] for i in _sum_pdf_cols]
        _sum_sr_widths = [_sum_full_widths[i] for i in _sum_pdf_cols]
        _sum_body_rows = []
        _sum_total_vals = [0] * 8
        for idx, sd in enumerate(summary_data, start=1):
            total_amount = sd["amount_received"] + sd["pending_amount"]
            _sr = [
                idx,
                wrap_sum_left(fmt_staff_name(sd["staff_name"])),
                fmt(sd["total_bills"]),
                fmt(sd["received_bills"]),
                fmt(sd["remaining_bills"]),
                fmt(total_amount),
                fmt(sd["amount_received"]),
                fmt(sd["pending_amount"]),
            ]
            _sum_body_rows.append([_sr[i] for i in _sum_pdf_cols])
            _sum_total_vals[2] += sd["total_bills"]
            _sum_total_vals[3] += sd["received_bills"]
            _sum_total_vals[4] += sd["remaining_bills"]
            _sum_total_vals[5] += sd["amount_received"] + sd["pending_amount"]
            _sum_total_vals[6] += sd["amount_received"]
            _sum_total_vals[7] += sd["pending_amount"]
        # Grand total row
        gt_sum = [
            "",
            "Grand Total",
            fmt(_sum_total_vals[2]),
            fmt(_sum_total_vals[3]),
            fmt(_sum_total_vals[4]),
            fmt(_sum_total_vals[5]),
            fmt(_sum_total_vals[6]),
            fmt(_sum_total_vals[7]),
        ]
        _sum_body_rows.append([gt_sum[i] for i in _sum_pdf_cols])
        _sum_table_data = [_sum_sr_headers] + _sum_body_rows
        elements.append(Paragraph("Staff-wise Summary Report", title_style))
        if show_summary:
            elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}", summary_style))
        elements.append(Spacer(1, 4 * mm))
        elements.append(
            _make_pdf_table(
                _sum_table_data,
                col_widths=_sum_sr_widths,
                left_cols=_sum_left_cols,
                header_font_size=10,
                body_font_size=9,
                cell_padding=6,
            )
        )
        elements.append(PageBreak())

    # Page 2+: Detail pages
    elements.append(Paragraph("Bill List - Staff Report", title_style))
    if show_summary:
        elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}", summary_style))

    _all_table_headers = [
        "Sr",
        "Sector",
        "Locality",
        "Total Bills",
        "Received Bills",
        "Remaining Bills",
        "Amount Received",
        "Pending Amount",
    ]
    table_headers = [_all_table_headers[i] for i in _pdf_cols]
    _all_col_widths = [
        page_w * 0.04,
        page_w * 0.24,
        page_w * 0.22,
        page_w * 0.08,
        page_w * 0.10,
        page_w * 0.10,
        page_w * 0.11,
        page_w * 0.11,
    ]
    col_widths = [_all_col_widths[i] for i in _pdf_cols]

    def wrap_text(value):
        return wrap_pdf_body_cells([[value]], font_size=8)[0][0]

    def wrap_text_left(value):
        return wrap_pdf_body_cells([[value]], font_size=8, left_columns={0})[0][0]

    for (staff_name, zone), group_rows in grouped_items:
        staff_elements = [
            Paragraph(f"Staff: {fmt_staff_name(staff_name).replace(chr(10), '<br/>')}", group_style),
            Paragraph(f"Zone: {zone}", group_style),
        ]
        table_rows = []
        for idx, row in enumerate(group_rows, start=1):
            _full_row = [idx, wrap_text_left(row[3]), wrap_text(row[4]), row[5], row[6], row[7], row[8], row[9]]
            table_rows.append([_full_row[i] for i in _pdf_cols])
        data_rows = [table_headers] + table_rows + [total_row("Grand Total", group_rows)]
        staff_elements.append(
            _make_pdf_table(
                data_rows,
                col_widths=col_widths,
                left_cols=[],
                header_font_size=8,
                body_font_size=8,
                cell_padding=5,
            )
        )
        staff_elements.append(Spacer(1, 5 * mm))
        elements.append(KeepTogether(staff_elements))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


def export_zone_report_response(fmt_type: str, selected_zone: str, show_summary: bool = False):
    allowed_zones = {"All", "A", "B", "C", "Commercial", "Unassigned"}
    if selected_zone not in allowed_zones:
        selected_zone = "All"
    headers, rows = bill_list_zone_export_rows(selected_zone)
    cols_param = request.args.get("cols")
    title = "Zone-wise Report" if selected_zone == "All" else f"Zone {selected_zone} Report"
    filename_zone = selected_zone.lower().replace(" ", "_")

    def without_zone(row: list) -> list:
        return [row[0], row[2], row[3], row[4], row[5], row[6], row[7]]

    if fmt_type != "pdf":
        # CSV/Excel: filter full 8-column data (with Zone)
        csv_headers, csv_rows = parse_export_cols(cols_param, ZONE_COL_MAP, headers, rows)
        return export_table_response(fmt_type, title, csv_headers, csv_rows, f"bill_list_zone_{filename_zone}_report")

    # PDF: filter using PDF column map (7 cols, no Zone)
    pdf_col_headers = ["Sr", "Sector", "Total Bills", "Received Bills", "Remaining Bills", "Amount Received", "Pending Amount"]
    # Build a PDF-specific column map based on which of the original 8 cols are selected
    zone_selected = True
    if cols_param:
        selected_keys = [k.strip() for k in cols_param.split(",") if k.strip()]
        zone_selected = "zone" in selected_keys
    # If full 8-col set is used, strip zone; otherwise use filtered subset
    if cols_param:
        # Map original 8-col indices to 7-col PDF indices (removing zone at index 1)
        orig_sel = [k.strip() for k in cols_param.split(",") if k.strip() in ZONE_COL_MAP]
        pdf_indices = []
        for key in orig_sel:
            orig_idx = ZONE_COL_MAP[key]
            if orig_idx == 1:
                continue  # skip Zone
            pdf_idx = orig_idx if orig_idx < 1 else orig_idx - 1
            pdf_indices.append(pdf_idx)
        pdf_headers = [pdf_col_headers[i] for i in pdf_indices]
    else:
        pdf_headers = pdf_col_headers
        pdf_indices = list(range(7))

    def transform_row(row):
        r7 = without_zone(row)
        return [r7[i] for i in pdf_indices]

    grouped_sections = []
    overall_total = None
    if selected_zone == "All":
        current_zone = None
        current_rows = []
        current_total = None
        for row in rows:
            if row[2] == "Grand Total":
                overall_total = transform_row(row)
                continue
            if str(row[2]).endswith(" Total"):
                current_total = transform_row(row)
                if current_zone is not None:
                    grouped_sections.append({"zone": f"Zone {current_zone}", "rows": current_rows, "total": current_total if show_summary else None})
                current_zone = None
                current_rows = []
                current_total = None
                continue
            if current_zone is None:
                current_zone = row[1]
            current_rows.append(transform_row(row))
        if current_zone is not None:
            grouped_sections.append({"zone": f"Zone {current_zone}", "rows": current_rows, "total": current_total if show_summary else None})
    else:
        section_rows = []
        section_total = None
        for row in rows:
            if str(row[2]).endswith(" Total"):
                section_total = transform_row(row)
            else:
                section_rows.append(transform_row(row))
        grouped_sections.append({"zone": f"Zone {selected_zone}", "rows": section_rows, "total": section_total if show_summary else None})

    zone_summary_data = get_zone_summary_data() if show_summary and selected_zone == "All" else None
    # Zone summary table column mapping (table headers include Sr auto-generated)
    # 8 header cols: Sr, Zone, Total Bills, Received Bills, Total Amount, Arrears Received, Total Received, Pending Amount
    _zs_key_order = ["sr", "zone", "totalBills", "receivedBills", "totalAmount", "arrearsReceived", "totalReceivedAmount", "pendingAmount"]
    _zs_sel_indices = list(range(len(_zs_key_order)))  # all by default
    if zone_summary_data and cols_param:
        _zs_sel = [k.strip() for k in cols_param.split(",") if k.strip() in _zs_key_order]
        _zs_sel_indices = [i for i, k in enumerate(_zs_key_order) if k in _zs_sel]
    # We store the selection indices for use in generate_zone_grouped_pdf
    _zs_sel_str = ",".join(str(i) for i in _zs_sel_indices) if _zs_sel_indices != list(range(len(_zs_key_order))) else ""

    summary_lines = [
        f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}",
        f"<b>Zone:</b> {selected_zone}",
    ] if show_summary else []

    pdf_bytes = generate_zone_grouped_pdf(
        title,
        summary_lines,
        grouped_sections,
        overall_total,
        zone_summary_data,
        pdf_detail_headers=pdf_headers,
        zone_summary_sel=_zs_sel_indices if _zs_sel_indices != list(range(8)) else None,
    )
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=bill_list_zone_{filename_zone}_report.pdf"},
    )


def _save_results_cache(results: dict) -> None:
    try:
        with open(RESULTS_CACHE, "w", encoding="utf-8") as handle:
            json.dump(results, handle, ensure_ascii=True)
    except OSError:
        pass


def _load_results_cache() -> dict:
    if not os.path.exists(RESULTS_CACHE):
        return {}
    try:
        with open(RESULTS_CACHE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

# We store dashboard uploads in memory only. Bill List keeps its own SQLite
# data; this first-page data intentionally disappears when the process restarts.
_last_results = {}
_last_merged_df = None
_last_uploaded_names = None
_last_daily_staff_results = {}
_last_daily_staff_uploaded_names = []


def read_and_merge_uploaded_files(files) -> tuple[pd.DataFrame | None, list[str]]:
    dataframes = []
    base_columns = None
    uploaded_names = []

    for file in files:
        if not file or not file.filename:
            continue
        if not allowed_file(file.filename):
            flash(f"Unsupported file type: {file.filename}")
            continue

        filename = secure_filename(file.filename)
        try:
            df = read_uploaded_dataframe(file)
            if base_columns is None:
                base_columns = list(df.columns)
            else:
                df = df.reindex(columns=base_columns)
            dataframes.append(df)
            uploaded_names.append(filename)
        except Exception as exc:
            flash(f"Failed to read {filename}: {exc}")

    if not dataframes:
        return None, uploaded_names
    return pd.concat(dataframes, ignore_index=True, sort=False), uploaded_names


@app.route("/", methods=["GET", "POST"])
def index():
    global _last_results, _last_merged_df, _last_uploaded_names
    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "save_data":
            files = request.files.getlist("files")
            if not files or all(not f.filename for f in files):
                flash("Please choose a CSV or Excel file first.")
                return redirect(url_for("index"))

            merged, uploaded_names = read_and_merge_uploaded_files(files)
            if merged is None:
                flash("No valid files were processed.")
                return redirect(url_for("index"))

            # Persist to disk so data survives page refresh
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            merged.to_csv(SAVED_DASHBOARD_CSV, index=False)
            with open(SAVED_DASHBOARD_META, "w") as f:
                json.dump({
                    "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "file_names": uploaded_names,
                    "row_count": len(merged),
                }, f)

            _last_merged_df = merged.copy()
            _last_uploaded_names = uploaded_names
            flash("Data saved successfully.")
            return render_template("index.html", results=None, uploaded_names=uploaded_names,
                                   saved_meta={
                                       "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                       "file_names": uploaded_names,
                                       "row_count": len(merged),
                                   })

        if action == "generate_reports":
            merged = _last_merged_df
            if merged is None and os.path.exists(SAVED_DASHBOARD_CSV):
                merged = pd.read_csv(SAVED_DASHBOARD_CSV)
                if merged is not None:
                    _last_merged_df = merged.copy()
                    if os.path.exists(SAVED_DASHBOARD_META):
                        with open(SAVED_DASHBOARD_META) as f:
                            meta = json.load(f)
                        _last_uploaded_names = meta.get("file_names")
            if merged is None:
                flash("Please save data first before generating reports.")
                return redirect(url_for("index"))

            results = summarize_dataframe(merged)
            results["raw_row_count"] = int(len(merged))
            results["duplicate_rows_removed"] = 0
            results["duplicate_key_columns"] = []

            results["merged_csv_name"] = "merged_latest.csv"
            results["merged_xlsx_name"] = "merged_latest.xlsx"

            _last_results = results
            saved_meta = None
            if os.path.exists(SAVED_DASHBOARD_META):
                with open(SAVED_DASHBOARD_META) as f:
                    saved_meta = json.load(f)
            flash("Reports generated successfully.")
            return render_template("index.html", results=results,
                                   uploaded_names=_last_uploaded_names,
                                   saved_meta=saved_meta)

        if action == "clear_saved_data":
            for path in [SAVED_DASHBOARD_CSV, SAVED_DASHBOARD_META]:
                if os.path.exists(path):
                    os.remove(path)
            _last_merged_df = None
            _last_results = {}
            _last_uploaded_names = None
            flash("Saved data cleared.")
            return redirect(url_for("index"))

        # Fallback — treat as old-style process-files for backward compat
        files = request.files.getlist("files")
        if not files or all(not f.filename for f in files):
            flash("Please choose at least one CSV or Excel file.")
            return redirect(url_for("index"))

        merged, uploaded_names = read_and_merge_uploaded_files(files)
        if merged is None:
            flash("No valid files were processed.")
            return redirect(url_for("index"))

        results = summarize_dataframe(merged)
        results["raw_row_count"] = int(len(merged))
        results["duplicate_rows_removed"] = 0
        results["duplicate_key_columns"] = []

        results["merged_csv_name"] = "merged_latest.csv"
        results["merged_xlsx_name"] = "merged_latest.xlsx"

        _last_results = results
        _last_merged_df = merged.copy()
        _last_uploaded_names = uploaded_names
        return render_template("index.html", results=results, uploaded_names=uploaded_names)

    # GET — restore metadata from persistent storage and pass to template
    _last_results = {}
    _last_merged_df = None
    _last_uploaded_names = None
    saved_meta = None
    if os.path.exists(SAVED_DASHBOARD_META):
        with open(SAVED_DASHBOARD_META) as f:
            saved_meta = json.load(f)
        _last_uploaded_names = saved_meta.get("file_names")
    return render_template("index.html", results=None, uploaded_names=None,
                           saved_meta=saved_meta)


@app.route("/download/<path:filename>")
def download_file(filename: str):
    if filename == "merged_latest.csv" and _last_merged_df is not None:
        return Response(
            _last_merged_df.to_csv(index=False),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=merged_latest.csv"},
        )
    if filename == "merged_latest.xlsx" and _last_merged_df is not None:
        buf = io.BytesIO()
        _last_merged_df.to_excel(buf, index=False)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=merged_latest.xlsx"},
        )
    flash("No uploaded dashboard data is available. Please upload the file again.")
    return redirect(url_for("index"))


@app.route("/daily-staff-receive", methods=["GET", "POST"])
def daily_staff_receive():
    global _last_daily_staff_results, _last_daily_staff_uploaded_names
    if request.method == "POST":
        files = request.files.getlist("files")
        if not files or all(not f.filename for f in files):
            flash("Please choose at least one CSV or Excel file.")
            return redirect(url_for("daily_staff_receive"))

        merged, uploaded_names = read_and_merge_uploaded_files(files)
        if merged is None:
            flash("No valid files were processed.")
            return redirect(url_for("daily_staff_receive"))

        results = summarize_dataframe(merged)
        _last_daily_staff_results = {"daily_staff_receive": results.get("daily_staff_receive") or {}}
        _last_daily_staff_uploaded_names = uploaded_names
        return render_template(
            "daily_staff_receive.html",
            report=_last_daily_staff_results["daily_staff_receive"],
            uploaded_names=uploaded_names,
        )

    return render_template(
        "daily_staff_receive.html",
        report=(_last_daily_staff_results or {}).get("daily_staff_receive"),
        uploaded_names=_last_daily_staff_uploaded_names,
    )


@app.route("/bill-list", methods=["GET", "POST"])
def bill_list():
    init_bill_list_db()
    if request.method == "POST":
        action = request.form.get("action", "")
        if not action and request.files.get("bill_file"):
            action = "save_data"
        if action == "clear_bill_list_data":
            clear_bill_list_data()
            flash("Bill rows and saved upload copies have been removed. Staff, assignments, sectors, localities, and zones were kept.")
            return redirect(url_for("bill_list"))

        if action == "save_data":
            file = request.files.get("bill_file")
            if not file or not file.filename:
                flash("Please choose a bill file first.")
                return redirect(url_for("bill_list"))
            if not allowed_file(file.filename):
                flash(f"Unsupported file type: {file.filename}")
                return redirect(url_for("bill_list"))

            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], f"bill_list_{timestamp}_{filename}")
            file.save(save_path)
            try:
                df = read_dataframe(save_path)
                imported, duplicates = import_bill_list_dataframe(df)
                flash(f"Bill data saved successfully. Imported {imported:,} row(s).")
                if duplicates:
                    flash(f"Skipped {duplicates:,} duplicate row(s) inside the uploaded file.")
            except Exception as exc:
                flash(f"Failed to import Bill List file: {exc}")
            return redirect(url_for("bill_list"))

        if action == "generate_reports":
            with get_db() as conn:
                count = conn.execute("SELECT COUNT(*) as cnt FROM bills").fetchone()["cnt"]
                if count == 0:
                    flash("Please save or upload bill data first.")
                    return redirect(url_for("bill_list"))
            flash("Reports generated successfully.")
            return redirect(url_for("bill_list"))

        if action == "add_staff":
            name = (request.form.get("staff_name") or "").strip()
            if not name:
                flash("Enter a staff name.")
                return redirect(url_for("bill_list"))
            try:
                with get_db() as conn:
                    conn.execute(
                        "INSERT INTO staff (name, created_at) VALUES (?, ?)",
                        (name, datetime.now().isoformat(timespec="seconds")),
                    )
                flash(f"Added staff member: {name}")
            except sqlite3.IntegrityError:
                flash(f"Staff member already exists: {name}")
            return redirect(url_for("bill_list"))

        if action == "update_staff":
            staff_id = request.form.get("staff_id")
            name = (request.form.get("staff_name") or "").strip()
            if not staff_id or not name:
                flash("Choose a staff member and enter a new name.")
                return redirect(url_for("bill_list"))
            try:
                with get_db() as conn:
                    conn.execute("UPDATE staff SET name = ? WHERE id = ?", (name, staff_id))
                flash(f"Updated staff member: {name}")
            except sqlite3.IntegrityError:
                flash(f"Staff member already exists: {name}")
            return redirect(url_for("bill_list"))

        if action == "delete_staff":
            staff_id = request.form.get("staff_id")
            if staff_id:
                with get_db() as conn:
                    row = conn.execute("SELECT name FROM staff WHERE id = ?", (staff_id,)).fetchone()
                    conn.execute("DELETE FROM staff_assignments WHERE staff_id = ?", (staff_id,))
                    conn.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
                flash(f"Deleted staff member: {row['name'] if row else staff_id}")
            return redirect(url_for("bill_list"))

        if action == "assign_staff":
            staff_id = request.form.get("staff_id")
            zone = (request.form.get("zone") or "").strip()
            selected_sectors = split_sector_values(request.form.getlist("sectors"))
            selected_localities = []
            for value in request.form.getlist("localities"):
                if "||" not in value:
                    continue
                sector_value, locality_value = value.split("||", 1)
                sector_value = sector_value.strip()
                locality_value = locality_value.strip()
                if sector_value and locality_value:
                    selected_localities.append((sector_value, locality_value))
            if not staff_id or not zone:
                flash("Choose a staff member and zone.")
                return redirect(url_for("bill_list"))
            effective_localities = [] if selected_sectors else selected_localities
            try:
                with get_db() as conn:
                    conflicts = get_assignment_conflicts(conn, staff_id, zone, selected_sectors, effective_localities)
                    if conflicts:
                        flash("Cannot save assignment. " + "; ".join(conflicts[:5]))
                        return redirect(url_for("bill_list"))
                    if effective_localities:
                        conn.execute(
                            "DELETE FROM staff_assignments WHERE staff_id = ? AND zone = ?",
                            (staff_id, zone),
                        )
                        for sector, locality in effective_localities:
                            conn.execute(
                                """
                                INSERT INTO staff_assignments (staff_id, zone, sector, locality, created_at)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (staff_id, zone, sector, locality, datetime.now().isoformat(timespec="seconds")),
                            )
                    elif selected_sectors:
                        conn.execute(
                            "DELETE FROM staff_assignments WHERE staff_id = ? AND zone = ?",
                            (staff_id, zone),
                        )
                        for sector in selected_sectors:
                            conn.execute(
                                """
                                INSERT INTO staff_assignments (staff_id, zone, sector, locality, created_at)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (staff_id, zone, sector, None, datetime.now().isoformat(timespec="seconds")),
                            )
                    else:
                        available_sectors = conn.execute(
                            """
                            SELECT name
                            FROM sectors
                            WHERE zone = ?
                              AND NOT EXISTS (
                                  SELECT 1
                                  FROM staff_assignments sa
                                  WHERE sa.zone = sectors.zone
                                    AND (sa.sector = sectors.name OR sa.sector IS NULL)
                              )
                            ORDER BY name
                            """,
                            (zone,),
                        ).fetchall()
                        if not available_sectors:
                            flash("No available sectors remain in that zone.")
                            return redirect(url_for("bill_list"))
                        for row in available_sectors:
                            conn.execute(
                                """
                                INSERT INTO staff_assignments (staff_id, zone, sector, locality, created_at)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (staff_id, zone, row["name"], None, datetime.now().isoformat(timespec="seconds")),
                            )
                flash("Staff assignment saved.")
            except sqlite3.IntegrityError:
                flash("One or more selected staff assignments already exist.")
            return redirect(url_for("bill_list"))

        if action == "delete_assignment":
            assignment_id = request.form.get("assignment_id")
            if assignment_id:
                with get_db() as conn:
                    conn.execute("DELETE FROM staff_assignments WHERE id = ?", (assignment_id,))
                flash("Staff assignment removed.")
            return redirect(url_for("bill_list"))

        if action == "update_sector_zone":
            selected_sectors = split_sector_values(request.form.getlist("sectors"))
            fallback_sector = (request.form.get("sector") or "").strip()
            if fallback_sector:
                selected_sectors.append(fallback_sector)
            zone = (request.form.get("zone") or "").strip()
            selected_sectors = sorted(set(selected_sectors))
            if not selected_sectors or not zone:
                flash("Choose one or more sectors and a zone to update.")
                return redirect(url_for("bill_list"))
            with get_db() as conn:
                for sector in selected_sectors:
                    update_sector_zone(conn, sector, zone)
            flash(f"Updated {len(selected_sectors):,} sector(s) to Zone {zone}.")
            return redirect(url_for("bill_list"))

    return render_template("bill_list.html", **get_bill_list_context())


@app.route("/bill-list/export/<fmt_type>")
def export_bill_list(fmt_type: str):
    headers, rows, summary = bill_list_export_rows()
    cols_param = request.args.get("cols")
    headers, rows = parse_export_cols(cols_param, SECTOR_COL_MAP, headers, rows)
    if fmt_type == "pdf":
        show_summary = request.args.get("show_summary", "0") == "1"
        n = len(headers)
        page_w = landscape(A4)[0] - 30 * mm
        col_widths = [page_w / n] * n
        summary_lines = [
            f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}",
            f"<b>Total Bills:</b> {fmt(summary['total_bills'])}",
            f"<b>Received Bills:</b> {fmt(summary['received_bills'])}",
            f"<b>Remaining Bills:</b> {fmt(summary['remaining_bills'])}",
            f"<b>Amount Received:</b> Rs. {fmt(summary['total_received_amount'])}",
            f"<b>Pending Amount:</b> Rs. {fmt(summary['remaining_amount'])}",
        ] if show_summary else []
        pdf_bytes = generate_card_pdf(
            "Bill List - Sector-wise Report",
            summary_lines,
            headers,
            rows,
            pagesize=landscape(A4),
            col_widths=col_widths,
            left_cols=[i for i, h in enumerate(headers) if h.lower() == "sector"],
            header_font_size=9,
            body_font_size=9,
        )
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=bill_list_sector_report.pdf"},
        )
    if fmt_type == "csv":
        csv_data = pd.DataFrame(rows, columns=headers).to_csv(index=False)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=bill_list_sector_report.csv"},
        )
    if fmt_type == "xlsx":
        buf = io.BytesIO()
        pd.DataFrame(rows, columns=headers).to_excel(buf, index=False)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=bill_list_sector_report.xlsx"},
        )
    flash("Unknown export format.")
    return redirect(url_for("bill_list"))


@app.route("/bill-list/export/unpaid-amounts/<fmt_type>")
def export_unpaid_amount_summary(fmt_type: str):
    sections, total = unpaid_amount_export_data()
    cols_param = request.args.get("cols")
    filename = "unpaid_expired_bill_amounts"

    # Filter columns for each section
    if cols_param:
        filtered_sections = []
        for key, title, headers, rows in sections:
            if key == "summary":
                col_map = UNPAID_SUMMARY_COL_MAP
            else:
                col_map = UNPAID_SECTION_COL_MAP
            fh, fr = parse_export_cols(cols_param, col_map, headers, rows)
            filtered_sections.append((key, title, fh, fr))
        sections = filtered_sections

    if fmt_type == "pdf":
        show_summary = request.args.get("show_summary", "0") == "1"
        pdf_bytes = generate_unpaid_amount_pdf(sections, total, show_summary=show_summary)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"},
        )

    if fmt_type == "csv":
        out = io.StringIO()
        writer = csv.writer(out)
        for _, section_title, headers, rows in sections:
            writer.writerow([section_title])
            writer.writerow(headers)
            writer.writerows(rows)
            writer.writerow([])
        return Response(
            out.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"},
        )

    if fmt_type == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            for _, section_title, headers, rows in sections:
                pd.DataFrame(rows, columns=headers).to_excel(
                    writer,
                    sheet_name=section_title[:31],
                    index=False,
                )
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"},
        )

    flash("Unknown export format.")
    return redirect(url_for("bill_list"))


@app.route("/bill-list/export/unpaid-amounts/<section_key>/<fmt_type>")
def export_unpaid_amount_section(section_key: str, fmt_type: str):
    sections, total = unpaid_amount_export_data()
    section = unpaid_amount_section(sections, section_key)
    if section is None:
        flash("Unknown unpaid amount report section.")
        return redirect(url_for("bill_list"))

    key, title, headers, rows = section
    cols_param = request.args.get("cols")
    if key == "summary":
        col_map = UNPAID_SUMMARY_COL_MAP
    else:
        col_map = UNPAID_SECTION_COL_MAP
    headers, rows = parse_export_cols(cols_param, col_map, headers, rows)
    section = (key, title, headers, rows)
    filename = f"unpaid_expired_{key}_amounts"
    selected_sections = [section]

    if fmt_type == "pdf":
        show_summary = request.args.get("show_summary", "0") == "1"
        pdf_bytes = generate_unpaid_amount_pdf(selected_sections, total, show_summary=show_summary)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"},
        )

    if fmt_type == "csv":
        csv_data = pd.DataFrame(rows, columns=headers).to_csv(index=False)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"},
        )

    if fmt_type == "xlsx":
        buf = io.BytesIO()
        pd.DataFrame(rows, columns=headers).to_excel(buf, sheet_name=title[:31], index=False)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"},
        )

    flash("Unknown export format.")
    return redirect(url_for("bill_list"))


@app.route("/bill-list/export/zone/<fmt_type>")
def export_bill_list_zone(fmt_type: str):
    show_summary = request.args.get("show_summary", "0") == "1"
    return export_zone_report_response(fmt_type, request.args.get("zone", "All"), show_summary=show_summary)


@app.route("/bill-list/export/staff/<fmt_type>")
def export_bill_list_staff(fmt_type: str):
    staff_id = request.args.get("staff_id") or None
    show_summary = request.args.get("show_summary", "0") == "1"
    cols_param = request.args.get("cols")
    summary_cols_param = request.args.get("summary_cols")
    headers, rows = bill_list_staff_export_rows(staff_id)
    if fmt_type == "pdf":
        pdf_bytes = generate_staff_report_pdf(rows, show_summary=show_summary, cols_param=cols_param, summary_cols_param=summary_cols_param)
        suffix = f"_{staff_id}" if staff_id else ""
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=bill_list_staff_report{suffix}.pdf"},
        )

    if staff_id:
        fh, fr = parse_export_cols(cols_param, STAFF_COL_MAP, headers, rows)
        return export_table_response(fmt_type, "Bill List - Staff Report", fh, fr, f"bill_list_staff_report_{staff_id}")

    def parse_num(val):
        return parse_number(str(val).replace(",", ""))

    grouped = {}
    for row in rows:
        grouped.setdefault((row[1], row[2]), []).append(row)

    summary_rows = []
    grand_total = {"total_bills": 0, "received_bills": 0, "remaining_bills": 0, "amount_received": 0, "pending_amount": 0}

    for idx, ((staff_name, zone), group_rows) in enumerate(sorted(grouped.items()), start=1):
        total_bills = sum(parse_num(r[5]) for r in group_rows)
        received_bills = sum(parse_num(r[6]) for r in group_rows)
        remaining_bills = sum(parse_num(r[7]) for r in group_rows)
        amount_received = sum(parse_num(r[8]) for r in group_rows)
        pending_amount = sum(parse_num(r[9]) for r in group_rows)
        total_amount = amount_received + pending_amount

        summary_rows.append([
            idx,
            fmt_staff_name(staff_name),
            total_bills,
            received_bills,
            remaining_bills,
            total_amount,
            amount_received,
            pending_amount,
        ])

        grand_total["total_bills"] += total_bills
        grand_total["received_bills"] += received_bills
        grand_total["remaining_bills"] += remaining_bills
        grand_total["amount_received"] += amount_received
        grand_total["pending_amount"] += pending_amount

    gt_total_amount = grand_total["amount_received"] + grand_total["pending_amount"]
    summary_rows.append(["", "Grand Total", grand_total["total_bills"], grand_total["received_bills"], grand_total["remaining_bills"], gt_total_amount, grand_total["amount_received"], grand_total["pending_amount"]])

    summary_headers = ["Sr", "Staff Name", "Total Bills", "Received Bills", "Remaining Bills", "Total Amount", "Amount Received", "Pending Amount"]

    # Apply column filtering for CSV/Excel
    # Detail cols filtering
    if cols_param:
        _sel = [k.strip() for k in cols_param.split(",") if k.strip() in STAFF_COL_MAP]
        _csv_detail_cols = sorted([STAFF_COL_MAP[k] for k in _sel if k in STAFF_COL_MAP])
        if _csv_detail_cols:
            headers = [headers[i] for i in _csv_detail_cols]
            rows = [[r[i] for i in _csv_detail_cols] for r in rows]
    # Summary cols filtering
    _sum_keys = ["sr", "staffName", "totalBills", "receivedBills", "remainingBills", "totalAmount", "amountReceived", "pendingAmount"]
    _csv_summary_cols = list(range(8))
    if summary_cols_param:
        _sum_sel = [k.strip() for k in summary_cols_param.split(",") if k.strip() in STAFF_SUMMARY_COL_MAP]
        _csv_summary_cols = sorted([STAFF_SUMMARY_COL_MAP[k] for k in _sum_sel]) if _sum_sel else list(range(8))
    if _csv_summary_cols != list(range(8)):
        summary_headers = [summary_headers[i] for i in _csv_summary_cols]
        summary_rows = [[r[i] for i in _csv_summary_cols] for r in summary_rows]

    if fmt_type == "csv":
        csv_lines = []
        csv_lines.append(",".join(summary_headers))
        for sr in summary_rows:
            csv_lines.append(",".join(str(x) for x in sr))
        csv_lines.append("")
        csv_lines.append("Detailed Report")
        csv_lines.append(",".join(headers))
        for r in rows:
            csv_lines.append(",".join(str(x) for x in r))
        csv_data = "\n".join(csv_lines)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=bill_list_staff_report.csv"},
        )

    if fmt_type == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame(summary_rows, columns=summary_headers).to_excel(writer, sheet_name="Summary", index=False)
            pd.DataFrame(rows, columns=headers).to_excel(writer, sheet_name="Detailed", index=False)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=bill_list_staff_report.xlsx"},
        )

    flash("Unknown export format.")
    return redirect(url_for("bill_list"))


def _get_season_bill_ids(season: str) -> set[int]:
    """Return set of bill IDs whose due date falls in the given season.
    season: 'jan-jun' or 'jul-dec'
    """
    init_bill_list_db()
    target_months = set(range(1, 7)) if season == "jan-jun" else set(range(7, 13))
    ids: set[int] = set()
    with get_db() as conn:
        rows = conn.execute("SELECT id, raw_data FROM bills").fetchall()
    for row in rows:
        try:
            data = json.loads(row["raw_data"])
            due = data.get("due date")
            if due:
                dt = pd.to_datetime(str(due), dayfirst=True, errors="coerce")
                if pd.notna(dt) and dt.month in target_months:
                    ids.add(row["id"])
        except Exception:
            continue
    return ids


@app.route("/bill-list/export/six-month-pitch/<fmt_type>")
def export_six_month_pitch(fmt_type: str):
    cols_param = request.args.get("cols")
    season = request.args.get("season", "").strip().lower()

    # Auto-detect default season from current month
    if season not in ("jan-jun", "jul-dec"):
        current_month = datetime.now().month
        season = "jan-jun" if current_month <= 6 else "jul-dec"

    season_label = "January to June" if season == "jan-jun" else "July to December"
    report_title = f"Six Month {season_label} Report"
    file_slug = f"Six_Month_{season_label.replace(' ', '_')}_Report"

    # Get bill IDs for the selected season
    season_bill_ids = _get_season_bill_ids(season)

    headers, detail_rows = bill_list_staff_export_rows(bill_ids=season_bill_ids)
    init_bill_list_db()
    with get_db() as conn:
        unpaid_summary = build_unpaid_amount_summary(conn, bill_ids=season_bill_ids)
    unpaid_staff_rows = unpaid_summary.get("staff_rows", [])

    # Build unpaid lookup: normalized base name → current_bill_amount
    unpaid_lookup = {}
    for row in unpaid_staff_rows:
        norm = _normalize_staff_name(row["name"])
        closest = _closest_staff_key(norm)
        key = _normalize_staff_name(closest) if closest and closest != norm else norm
        unpaid_lookup[key] = float(row["current_bill_amount"])

    # Group staff summary by staff name (10-col: sr(0), staff(1), zone(2), sector(3), locality(4), totalBills(5), receivedBills(6), remainingBills(7), totalReceivedAmount(8), pendingAmount(9))
    def pn(v):
        return parse_number(str(v).replace(",", ""))
    staff_groups = {}
    for row in detail_rows:
        name = row[1]
        staff_groups.setdefault(name, []).append(row)

    pitch_rows = []
    pitch_grand = {"totalBills": 0, "receivedBills": 0, "remainingBills": 0, "totalAmount": 0, "amountReceived": 0, "currentBillAmount": 0}
    for idx, (staff_name, group_rows) in enumerate(sorted(staff_groups.items()), start=1):
        total_bills = sum(pn(r[5]) for r in group_rows)
        received_bills = sum(pn(r[6]) for r in group_rows)
        remaining_bills = sum(pn(r[7]) for r in group_rows)
        amount_received = sum(pn(r[8]) for r in group_rows)
        pending_amount = sum(pn(r[9]) for r in group_rows)
        total_amount = amount_received + pending_amount

        norm = _normalize_staff_name(staff_name)
        closest = _closest_staff_key(norm)
        lookup_key = _normalize_staff_name(closest) if closest and closest != norm else norm if norm in unpaid_lookup else _normalize_staff_name(staff_name)
        current_bill = unpaid_lookup.get(lookup_key, 0)

        pitch_rows.append([
            idx,
            fmt_staff_name(staff_name),
            fmt(total_bills),
            fmt(received_bills),
            fmt(remaining_bills),
            fmt(total_amount),
            fmt(amount_received),
            fmt(current_bill),
        ])
        pitch_grand["totalBills"] += total_bills
        pitch_grand["receivedBills"] += received_bills
        pitch_grand["remainingBills"] += remaining_bills
        pitch_grand["totalAmount"] += total_amount
        pitch_grand["amountReceived"] += amount_received
        pitch_grand["currentBillAmount"] += current_bill

    pitch_grand_row = ["", "Grand Total", fmt(pitch_grand["totalBills"]), fmt(pitch_grand["receivedBills"]), fmt(pitch_grand["remainingBills"]), fmt(pitch_grand["totalAmount"]), fmt(pitch_grand["amountReceived"]), fmt(pitch_grand["currentBillAmount"])]

    pitch_headers = ["Sr", "Staff Name", "Total Bills", "Received Bills", "Remaining Bills", "Total Amount", "Amount Received", "Pending Amount"]

    # Column filtering
    _pitch_sel = []
    if cols_param:
        _pitch_sel = [k.strip() for k in cols_param.split(",") if k.strip() in PITCH_COL_MAP]
    _pitch_pdf_cols = sorted([PITCH_COL_MAP[k] for k in _pitch_sel]) if _pitch_sel else list(range(8))
    _pitch_headers = [pitch_headers[i] for i in _pitch_pdf_cols]
    _pitch_left_cols = {_pitch_pdf_cols.index(1)} if 1 in _pitch_pdf_cols else set()

    # PDF
    if fmt_type == "pdf":
        buf = io.BytesIO()
        margins = 8 * mm
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=6*mm, bottomMargin=6*mm, leftMargin=6*mm, rightMargin=6*mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("PitchTitle", parent=styles["Heading1"], fontSize=20, textColor=ACCENT, alignment=1, spaceAfter=6*mm, fontName="Helvetica-Bold")
        elements = [Paragraph(report_title, title_style)]
        page_w = landscape(A4)[0] - 2 * margins
        _all_pw = [page_w*0.04, page_w*0.15, page_w*0.09, page_w*0.13, page_w*0.13, page_w*0.14, page_w*0.14, page_w*0.18]
        _pw = [_all_pw[i] for i in _pitch_pdf_cols]

        def wrap_left(v):
            return wrap_pdf_body_cells([[v]], font_size=9, left_columns={0})[0][0]

        body_rows = []
        for r in pitch_rows:
            full = [r[0], wrap_left(r[1]), r[2], r[3], r[4], r[5], r[6], r[7]]
            body_rows.append([full[i] for i in _pitch_pdf_cols])
        gt_full = [pitch_grand_row[0], pitch_grand_row[1], pitch_grand_row[2], pitch_grand_row[3], pitch_grand_row[4], pitch_grand_row[5], pitch_grand_row[6], pitch_grand_row[7]]
        body_rows.append([gt_full[i] for i in _pitch_pdf_cols])
        table_data = [_pitch_headers] + body_rows
        elements.append(_make_pdf_table(table_data, col_widths=_pw, left_cols=_pitch_left_cols, header_font_size=10, body_font_size=9, cell_padding=6))
        doc.build(elements)
        buf.seek(0)
        return Response(buf.getvalue(), mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={file_slug}.pdf"})

    # CSV
    if fmt_type == "csv":
        _csv_rows = [[r[i] for i in _pitch_pdf_cols] for r in pitch_rows]
        _csv_gt = [pitch_grand_row[i] for i in _pitch_pdf_cols]
        _csv_rows.append(_csv_gt)
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(_pitch_headers)
        writer.writerows(_csv_rows)
        return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={file_slug}.csv"})

    # Excel
    if fmt_type == "xlsx":
        _ex_rows = [[r[i] for i in _pitch_pdf_cols] for r in pitch_rows]
        _ex_gt = [pitch_grand_row[i] for i in _pitch_pdf_cols]
        _ex_rows.append(_ex_gt)
        df = pd.DataFrame(_ex_rows, columns=_pitch_headers)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="SixMonthPitch", index=False)
        buf.seek(0)
        return Response(buf.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={file_slug}.xlsx"})

    flash("Unknown export format.")
    return redirect(url_for("bill_list"))


@app.route("/bill-list/advanced-filter/<fmt_type>")
def export_advanced_bills(fmt_type: str):
    outstanding_amount = request.args.get("outstanding_amount")
    outstanding_amount = parse_number(outstanding_amount) if outstanding_amount else None

    outstanding_operator = request.args.get("outstanding_operator", "gt")

    bill_status = request.args.get("bill_status") or ""

    sector = request.args.get("sector") or None
    zone = request.args.get("zone") or None
    staff_id = request.args.get("staff_id")
    staff_id = int(staff_id) if staff_id and staff_id.isdigit() else None
    show_summary = request.args.get("show_summary", "0") == "1"
    cols_param = request.args.get("cols")
    group_by = request.args.get("group_by", "normal")

    bills = get_filtered_bills(
        outstanding_amount=outstanding_amount,
        outstanding_operator=outstanding_operator,
        bill_status=bill_status,
        sector=sector,
        zone=zone,
        staff_id=staff_id,
    )

    staff_name = None
    if staff_id:
        with get_db() as conn:
            row = conn.execute("SELECT name FROM staff WHERE id = ?", (staff_id,)).fetchone()
            staff_name = row["name"] if row else f"Staff #{staff_id}"

    filters_list = []
    if bill_status:
        filters_list.append("Paid" if bill_status == "paid" else "Unpaid")
    if outstanding_amount:
        op_label = ">" if outstanding_operator == "gt" else "<"
        filters_list.append(f"Outstanding {op_label} {fmt(outstanding_amount)}")
    if sector:
        filters_list.append(f"Sector: {sector}")
    if zone:
        filters_list.append(f"Zone: {zone}")
    if staff_name:
        filters_list.append(f"Staff: {staff_name}")

    filters_applied = ", ".join(filters_list) if filters_list else "None"

    if fmt_type == "zip":
        if not bills:
            flash("No bills match the selected filters.")
            return redirect(url_for("bill_list"))
        if group_by not in ("sector", "zone", "staff"):
            flash("ZIP export is available for Sector-wise, Zone-wise, and Staff-wise reports only.")
            return redirect(url_for("bill_list"))
        groups = group_bills(bills, group_by)
        if not groups:
            flash("No bills match the selected filters for ZIP export.")
            return redirect(url_for("bill_list"))
        zip_buf = generate_zip_of_group_pdfs(group_by, groups, filters_applied, cols_param=cols_param)
        zip_parts = [f"{group_by.capitalize()}_Wise"]
        if bill_status:
            zip_parts.append("Paid" if bill_status == "paid" else "Unpaid")
        if outstanding_amount:
            op_str = "Gt" if outstanding_operator == "gt" else "Lt"
            zip_parts.append(f"Outstanding{op_str}_{int(outstanding_amount)}")
        if sector:
            zip_parts.append(f"Sector_{sector}")
        if zone:
            zip_parts.append(f"Zone_{zone}")
        if staff_name:
            zip_parts.append(f"Staff_{staff_name.replace(' ', '_')}")
        zip_filename = sanitize_filename("_".join(zip_parts)) + ".zip"
        return Response(zip_buf.getvalue(), mimetype="application/zip", headers={"Content-Disposition": f"attachment; filename={zip_filename}"})

    return export_advanced_bills_response(fmt_type, bills, filters_applied, show_summary=show_summary, cols_param=cols_param, group_by=group_by)


# ---------------------------------------------------------------------------
# Summary Reports (Zones, Sectors, Staff)
# ---------------------------------------------------------------------------

def get_zones_summary():
    init_bill_list_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT
                zone,
                COUNT(*) AS bill_count,
                SUM(total_bill) AS total_amount
            FROM bills
            GROUP BY zone
            ORDER BY CASE zone WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 WHEN 'Commercial' THEN 4 ELSE 5 END
            """
        ).fetchall()
    return [
        {"name": row["zone"], "count": int(row["bill_count"] or 0), "total_amount": float(row["total_amount"] or 0)}
        for row in rows
    ]


def get_sectors_summary():
    init_bill_list_db()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT
                sector,
                COUNT(*) AS bill_count,
                SUM(total_bill) AS total_amount
            FROM bills
            GROUP BY sector
            ORDER BY sector
            """
        ).fetchall()
    return [
        {"name": row["sector"], "count": int(row["bill_count"] or 0), "total_amount": float(row["total_amount"] or 0)}
        for row in rows
    ]


def get_staff_summary():
    init_bill_list_db()
    with get_db() as conn:
        has_auto_rules = conn.execute("SELECT COUNT(*) AS cnt FROM auto_assignment_rules").fetchone()["cnt"] > 0

        if has_auto_rules:
            auto_exclude = "AND NOT EXISTS (SELECT 1 FROM auto_assignment_rules aar WHERE aar.sector = b.sector AND aar.locality = b.locality)"
            auto_assign_sql = """
            UNION ALL
            SELECT
                s.name AS staff_name,
                COUNT(b.id) AS bill_count,
                SUM(b.total_bill) AS total_amount
            FROM bills b
            JOIN auto_assignment_rules aar
                ON aar.sector = b.sector AND aar.locality = b.locality
                AND CAST(b.connection_no AS TEXT) >= aar.connection_min
                AND (aar.connection_max IS NULL OR CAST(b.connection_no AS TEXT) <= aar.connection_max)
            JOIN staff s ON UPPER(TRIM(s.name)) = UPPER(TRIM(aar.staff_name))
            GROUP BY s.id, s.name
            """
        else:
            auto_exclude = ""
            auto_assign_sql = ""

        rows = conn.execute(
            f"""
            SELECT
                s.name AS staff_name,
                COUNT(b.id) AS bill_count,
                SUM(b.total_bill) AS total_amount
            FROM staff_assignments sa
            JOIN staff s ON s.id = sa.staff_id
            LEFT JOIN bills b
                ON b.zone = sa.zone
                AND (sa.sector IS NULL OR b.sector = sa.sector)
                AND (sa.locality IS NULL OR b.locality = sa.locality)
                {auto_exclude}
            GROUP BY s.id, s.name

            {auto_assign_sql}

            UNION ALL
            SELECT
                'Unassigned' AS staff_name,
                COUNT(b.id) AS bill_count,
                SUM(b.total_bill) AS total_amount
            FROM bills b
            WHERE NOT EXISTS (
                SELECT 1
                FROM staff_assignments sa
                WHERE sa.zone = b.zone
                  AND (sa.sector IS NULL OR sa.sector = b.sector)
                  AND (sa.locality IS NULL OR sa.locality = b.locality)
            )
            {('AND NOT EXISTS (SELECT 1 FROM auto_assignment_rules aar WHERE aar.sector = b.sector AND aar.locality = b.locality)' if has_auto_rules else '')}
            HAVING COUNT(b.id) > 0
            ORDER BY staff_name
            """
        ).fetchall()
    return [
        {"name": fmt_staff_name(row["staff_name"]), "count": int(row["bill_count"] or 0), "total_amount": float(row["total_amount"] or 0)}
        for row in rows
    ]


def generate_summary_pdf(title: str, headers: list[str], rows: list[list], total_row: list[str] = None, show_summary: bool = True) -> bytes:
    page_w = A4[0] - 30 * mm
    col_widths = [page_w / len(headers)] * len(headers)
    summary_lines = [f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}"] if show_summary else []

    return generate_card_pdf(
        title,
        summary_lines,
        headers,
        rows,
        total_row,
        pagesize=A4,
        col_widths=col_widths,
        left_cols=[0],
        header_font_size=11,
        body_font_size=10,
    )


def export_summary_response(fmt_type: str, title: str, data: list[dict], filename_prefix: str, show_summary: bool = True, cols_param: str = None):
    all_headers = ["Name", "Count", "Total Amount"]
    all_rows = [[item["name"], fmt(item["count"]), fmt(item["total_amount"])] for item in data]
    headers, rows = parse_export_cols(cols_param, SUMMARY_COL_MAP, all_headers, all_rows)

    total_count = sum(item["count"] for item in data)
    total_amount = sum(item["total_amount"] for item in data)
    total_row = ["Total", fmt(total_count), fmt(total_amount)]
    # Filter total_row to match selected columns (same key order as headers)
    if cols_param:
        _sel = [k.strip() for k in cols_param.split(",") if k.strip() in SUMMARY_COL_MAP]
        _idx = [SUMMARY_COL_MAP[k] for k in _sel]
        total_row = [total_row[i] for i in _idx] if _idx else total_row

    if fmt_type == "pdf":
        pdf_bytes = generate_summary_pdf(title, headers, rows, total_row, show_summary=show_summary)
        return Response(pdf_bytes, mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename_prefix}.pdf"})

    if fmt_type == "csv":
        df = pd.DataFrame(rows, columns=headers)
        total_df = pd.DataFrame([total_row], columns=headers)
        combined_df = pd.concat([df, total_df], ignore_index=True)
        csv_data = combined_df.to_csv(index=False)
        return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename_prefix}.csv"})

    if fmt_type == "xlsx":
        buf = io.BytesIO()
        df = pd.DataFrame(rows, columns=headers)
        total_df = pd.DataFrame([total_row], columns=headers)
        combined_df = pd.concat([df, total_df], ignore_index=True)
        combined_df.to_excel(buf, index=False)
        buf.seek(0)
        return Response(buf.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={filename_prefix}.xlsx"})

    flash("Unknown export format.")
    return redirect(url_for("bill_list"))


@app.route("/bill-list/summary/zones/<fmt_type>")
def export_zones_summary(fmt_type: str):
    show_summary = request.args.get("show_summary", "0") == "1"
    cols_param = request.args.get("cols")
    data = get_zones_summary()
    return export_summary_response(fmt_type, "All Zones Summary Report", data, "all_zones_summary", show_summary=show_summary, cols_param=cols_param)


@app.route("/bill-list/summary/sectors/<fmt_type>")
def export_sectors_summary(fmt_type: str):
    show_summary = request.args.get("show_summary", "0") == "1"
    cols_param = request.args.get("cols")
    data = get_sectors_summary()
    return export_summary_response(fmt_type, "All Sectors Summary Report", data, "all_sectors_summary", show_summary=show_summary, cols_param=cols_param)


@app.route("/bill-list/summary/staff/<fmt_type>")
def export_staff_summary(fmt_type: str):
    show_summary = request.args.get("show_summary", "0") == "1"
    cols_param = request.args.get("cols")
    data = get_staff_summary()
    return export_summary_response(fmt_type, "All Staff Summary Report", data, "all_staff_summary", show_summary=show_summary, cols_param=cols_param)


# ---------------------------------------------------------------------------
# Card download endpoints (PDF / CSV / Excel)
# ---------------------------------------------------------------------------

def _card_rows_to_df(headers, rows):
    return pd.DataFrame(rows, columns=headers)


def commercial_daily_income_export_rows(results: dict):
    metric_header = results.get("commercial_daily_metric_label") or "Arrears Received"
    headers = [
        "Sr",
        "Date",
        "Consumer Name",
        "Connection No",
        "Sector",
        "Locality",
        metric_header,
        "Amount Received",
    ]
    rows = []
    current_date = None
    day_metric = 0
    day_amount = 0
    total_metric = 0
    total_amount = 0
    sr = 1

    def append_day_total(date_label: str):
        rows.append(["", "", f"{date_label} Total", "", "", "", fmt(day_metric), fmt(day_amount)])

    for row in results.get("commercial_daily_income") or []:
        date_label = row.get("date", "")
        if current_date is not None and date_label != current_date:
            append_day_total(current_date)
            day_metric = 0
            day_amount = 0
        current_date = date_label
        metric_total = row.get("metric_total", 0)
        amount_total = row.get("amount_total", 0)
        rows.append(
            [
                sr,
                date_label,
                row.get("consumer_name", ""),
                row.get("connection_no", ""),
                row.get("sector", ""),
                row.get("locality", ""),
                fmt(metric_total),
                fmt(amount_total),
            ]
        )
        sr += 1
        day_metric += metric_total
        day_amount += amount_total
        total_metric += metric_total
        total_amount += amount_total

    if current_date is not None:
        append_day_total(current_date)
    grand = ["", "", "Grand Total", "", "", "", fmt(total_metric), fmt(total_amount)] if rows else None
    return headers, rows, grand


def daily_staff_receive_export_tables(results: dict):
    report = results.get("daily_staff_receive") or {}
    summary_headers = ["Sr", "Staff Name", "No. of Bills Received", "Arrears Received", "Total Amount Received"]
    detail_headers = ["Staff Name", "Zone", "Sr", "Sector", "Locality", "Bills", "Arrears Received", "Received Amount"]

    summary_rows = []
    total_bills = 0
    total_metric = 0
    total_amount = 0
    for idx, row in enumerate(report.get("summary_rows") or [], start=1):
        bills = row.get("bills", 0)
        metric_total = row.get("metric_total", 0)
        amount_total = row.get("amount_total", 0)
        summary_rows.append([idx, fmt_staff_name(row.get("staff_name", "")), fmt(bills), fmt(metric_total), fmt(amount_total)])
        total_bills += bills
        total_metric += metric_total
        total_amount += amount_total
    summary_grand = ["", "Grand Total", fmt(total_bills), fmt(total_metric), fmt(total_amount)] if summary_rows else None

    detail_rows: list[list] = []
    for group in report.get("grouped_detail") or []:
        staff_name = fmt_staff_name(group.get("staff_name", ""))
        zone = group.get("zone", "")
        for idx, sub in enumerate(group.get("sub_rows") or [], start=1):
            detail_rows.append(
                [
                    staff_name,
                    zone,
                    idx,
                    sub.get("sector", ""),
                    sub.get("locality", ""),
                    fmt(sub.get("bills", 0)),
                    fmt(sub.get("metric_total", 0)),
                    fmt(sub.get("amount_total", 0)),
                ]
            )
    return summary_headers, summary_rows, summary_grand, detail_headers, detail_rows


def generate_daily_staff_receive_pdf(results: dict) -> bytes:
    summary_headers, summary_rows, summary_grand, detail_headers, detail_rows = daily_staff_receive_export_tables(results)
    report = results.get("daily_staff_receive") or {}
    buf = io.BytesIO()

    portrait_size = A4
    portrait_frame = Frame(15 * mm, 15 * mm, portrait_size[0] - 30 * mm, portrait_size[1] - 30 * mm, id="portrait")
    doc = BaseDocTemplate(
        buf,
        pagesize=portrait_size,
        pageTemplates=[
            PageTemplate(id="portrait", frames=[portrait_frame], pagesize=portrait_size),
        ],
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DailyStaffTitle", parent=styles["Heading1"], fontSize=19, textColor=ACCENT, alignment=1, spaceAfter=5 * mm, fontName="Helvetica-Bold")
    summary_style = ParagraphStyle("DailyStaffSummary", parent=styles["Normal"], fontSize=11, leading=15, spaceAfter=2 * mm)
    group_style = ParagraphStyle("DailyStaffGroup", parent=styles["Heading3"], fontSize=13, leading=16, spaceBefore=5 * mm, spaceAfter=2 * mm, fontName="Helvetica-Bold")
    staff_progress_style = ParagraphStyle(
        "DailyStaffProgress",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        spaceBefore=1 * mm,
        spaceAfter=3 * mm,
        textColor=colors.HexColor("#222222"),
    )

    def make_progress_summary(total_bills, total_metric, total_amount):
        return Paragraph(
            f"<b>Total Received Connections:</b> {fmt(total_bills)} &nbsp;&nbsp;&nbsp; "
            f"<b>Arrears Received:</b> {fmt(total_metric)} &nbsp;&nbsp;&nbsp; "
            f"<b>Total Amount Received:</b> {fmt(total_amount)}",
            staff_progress_style,
        )

    progress_style_small = ParagraphStyle(
        "DailyStaffProgressSmall",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        spaceBefore=1 * mm,
        spaceAfter=3 * mm,
        textColor=colors.HexColor("#222222"),
    )

    elements = [
        Paragraph("Daily Receive Amount of Staff", title_style),
        Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}", summary_style),
    ]
    if report.get("date_range"):
        elements.append(Paragraph(f"<b>Report Date:</b> {report['date_range']}", summary_style))

    page_w = portrait_size[0] - 30 * mm
    report_total_bills = report_total_metric = report_total_amount = 0
    for row in report.get("summary_rows") or []:
        report_total_bills += row.get("bills", 0)
        report_total_metric += row.get("metric_total", 0)
        report_total_amount += row.get("amount_total", 0)
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        f"<b>Total Received Connections:</b> {fmt(report_total_bills)} &nbsp;&nbsp;&nbsp; "
        f"<b>Arrears Received:</b> {fmt(report_total_metric)} &nbsp;&nbsp;&nbsp; "
        f"<b>Total Amount Received:</b> {fmt(report_total_amount)}",
        progress_style_small,
    ))
    elements.append(Spacer(1, 5 * mm))

    summary_data = [wrap_pdf_header_cells(summary_headers, font_size=11)] + wrap_pdf_body_cells(summary_rows, font_size=10, left_columns={1})
    if summary_grand:
        summary_data.append(wrap_pdf_body_cells([summary_grand], font_size=10, left_columns={1})[0])
    elements.append(
        _make_pdf_table(
            summary_data,
            col_widths=[page_w * 0.06, page_w * 0.30, page_w * 0.22, page_w * 0.20, page_w * 0.22],
            first_col_left=False,
            left_cols=[1],
            header_font_size=11,
            body_font_size=10,
            cell_padding=4,
        )
    )

    if detail_rows:
        elements.append(PageBreak())
        detail_page_w = portrait_size[0] - 30 * mm
        detail_table_headers = detail_headers[2:]
        current_group = None
        group_rows = []

        def flush_group():
            if not group_rows or current_group is None:
                return
            staff_name = current_group
            staff_elements = [
                Paragraph(f"Staff: {fmt_staff_name(staff_name).replace(chr(10), '<br/>')}", group_style),
            ]
            data_rows = []
            total_bills = total_metric = total_amount = 0
            for row in group_rows:
                data_rows.append([row[2], row[3], row[4], row[5], row[6], row[7]])
                total_bills += parse_number(str(row[5]).replace(",", ""))
                total_metric += parse_number(str(row[6]).replace(",", ""))
                total_amount += parse_number(str(row[7]).replace(",", ""))
            staff_elements.append(
                Paragraph(
                    f"<b>Total Received Connections:</b> {fmt(total_bills)} &nbsp;&nbsp; "
                    f"<b>Arrears Received:</b> {fmt(total_metric)} &nbsp;&nbsp; "
                    f"<b>Total Amount Received:</b> {fmt(total_amount)}",
                    progress_style_small,
                )
            )
            staff_elements.append(Spacer(1, 3 * mm))
            data_rows.append(["", "Grand Total", "", fmt(total_bills), fmt(total_metric), fmt(total_amount)])
            wrapped_rows = []
            for row in data_rows:
                wrapped_rows.append([row[0], *wrap_pdf_table_cells([row[1:3]], font_size=10)[0], row[3], row[4], row[5]])
            staff_elements.append(
                _make_pdf_table(
                    [wrap_pdf_header_cells(detail_table_headers, font_size=11)] + wrapped_rows,
                    col_widths=[detail_page_w * 0.06, detail_page_w * 0.27, detail_page_w * 0.27, detail_page_w * 0.10, detail_page_w * 0.15, detail_page_w * 0.15],
                    left_cols=[1, 2],
                    header_font_size=11,
                    body_font_size=10,
                    cell_padding=3,
                )
            )
            staff_elements.append(Spacer(1, 4 * mm))
            elements.append(KeepTogether(staff_elements))

        for row in detail_rows:
            group = row[0]
            if current_group is not None and group != current_group:
                flush_group()
                group_rows = []
            current_group = group
            group_rows.append(row)
        flush_group()

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()


def daily_staff_receive_export_response(fmt_type: str, results: dict, cols: str = "", detail_cols: str = ""):
    summary_headers, summary_rows, summary_grand, detail_headers, detail_rows = daily_staff_receive_export_tables(results)
    if cols:
        summary_headers, summary_rows = parse_export_cols(cols, DAILY_STAFF_RECEIVE_SUMMARY_COL_MAP, summary_headers, summary_rows)
        if summary_grand:
            _, g = parse_export_cols(cols, DAILY_STAFF_RECEIVE_SUMMARY_COL_MAP, summary_headers, [summary_grand])
            summary_grand = g[0] if g else summary_grand
    if detail_cols:
        detail_headers, detail_rows = parse_export_cols(detail_cols, DAILY_STAFF_RECEIVE_DETAIL_COL_MAP, detail_headers, detail_rows)
    filename = "daily_staff_receive_report"
    if fmt_type == "pdf":
        return Response(
            generate_daily_staff_receive_pdf(results),
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"},
        )
    if fmt_type == "csv":
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["Summary", *summary_headers])
        for row in summary_rows:
            writer.writerow(["Summary", *row])
        if summary_grand:
            writer.writerow(["Summary", *summary_grand])
        writer.writerow([])
        writer.writerow(["Details", *detail_headers])
        for row in detail_rows:
            writer.writerow(["Details", *row])
        return Response(
            out.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"},
        )
    if fmt_type == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame(summary_rows + ([summary_grand] if summary_grand else []), columns=summary_headers).to_excel(writer, sheet_name="Summary", index=False)
            pd.DataFrame(detail_rows, columns=detail_headers).to_excel(writer, sheet_name="Details", index=False)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"},
        )
    flash("Unknown export format.")
    return redirect(url_for("daily_staff_receive"))


@app.route("/download-card/<card>/<fmt_type>")
def download_card(card: str, fmt_type: str):
    r = _last_results
    if not r:
        flash("No data available. Please upload files first.")
        return redirect(url_for("index"))

    if card == "monthly":
        title = "Month-wise Report"
        fiscal_start, current_period = get_fiscal_window()
        period_str = f"{format_calendar_month(fiscal_start)} to {format_calendar_month(current_period)}"
        headers = ["Month", "No. of Bills", "Arrears Received", "Current Amount Received", "Amount Received"]
        rows = []
        gt_count, gt_arrears, gt_amount = 0, 0, 0
        for row in r.get("monthly_rows", []):
            c = row.get("count", 0)
            ar = row.get("arrears_total", 0)
            am = row.get("amount_total", 0)
            current = am - ar
            rows.append([row["label"], fmt(c), fmt(ar), fmt(current), fmt(am)])
            gt_count += c
            gt_arrears += ar
            gt_amount += am
        gt_current = gt_amount - gt_arrears
        summary = [
            f"<b>Period:</b> {period_str}",
            f"<b>Total Amount Received:</b> Rs. {fmt(gt_amount)}",
            f"<b>Total Arrears Received:</b> Rs. {fmt(gt_arrears)}",
            f"<b>Total Current Amount Received:</b> Rs. {fmt(gt_current)}",
        ]
        grand = ["Grand Total", fmt(gt_count), fmt(gt_arrears), fmt(gt_current), fmt(gt_amount)]

    elif card == "daily":
        title = "Date-wise Report"
        summary = [f"<b>Total Connections:</b> {fmt(r.get('fiscal_row_count'))}"]
        headers = ["Date", "No. of Bills", "Arrears Received", "Amount Received"]
        rows = []
        gt_count, gt_arrears, gt_amount = 0, 0, 0
        for row in r.get("daily_rows", []):
            c = row.get("count", 0)
            ar = row.get("arrears_total", 0)
            am = row.get("amount_total", 0)
            rows.append([row["label"], fmt(c), fmt(ar), fmt(am)])
            gt_count += c
            gt_arrears += ar
            gt_amount += am
        grand = ["Grand Total", fmt(gt_count), fmt(gt_arrears), fmt(gt_amount)]

    elif card == "sector":
        title = "Sector-wise Report"
        summary = [f"<b>Total Amount:</b> Rs. {r.get('total_amount_formatted', '0')}"]
        headers = ["Sector", "Arrears Received", "Amount Received"]
        rows = []
        gt_arrears, gt_amount = 0, 0
        for row in r.get("sector_rows", []):
            ar = row.get("arrears_total", 0)
            am = row.get("amount_total", 0)
            rows.append([row["label"], fmt(ar), fmt(am)])
            gt_arrears += ar
            gt_amount += am
        grand = ["Grand Total", fmt(gt_arrears), fmt(gt_amount)]

    elif card in ("commercial", "commercial-total"):
        title = "Commercial Sector — Locality Report"
        summary = [f"<b>Total (July to May)</b>"]
        headers = ["Locality", "No. of Bills"]
        if r.get("has_arrears"):
            headers.append("Arrears Received")
        headers.append("Amount Received")
        rows = []
        gt_count, gt_amount, gt_arrears = 0, 0, 0
        for row in r.get("commercial_total", []):
            c = row.get("count", 0)
            am = row.get("amount_total", 0)
            ar = row.get("arrears_total", 0)
            row_vals = [row["label"], fmt(c)]
            if r.get("has_arrears"):
                row_vals.append(fmt(ar))
                gt_arrears += ar
            row_vals.append(fmt(am))
            rows.append(row_vals)
            gt_count += c
            gt_amount += am
        grand = ["Grand Total", fmt(gt_count)]
        if r.get("has_arrears"):
            grand.append(fmt(gt_arrears))
        grand.append(fmt(gt_amount))

    elif card == "commercial-monthly":
        title = "Commercial Sector - Month-wise Locality Report"
        summary = [f"<b>Month-wise locality breakdown</b>"]
        headers = ["Month", "Locality", "No. of Bills"]
        if r.get("has_arrears"):
            headers.append("Arrears Received")
        headers.append("Amount Received")
        rows = []
        gt_count, gt_amount, gt_arrears = 0, 0, 0
        for month_label, month_rows in r.get("commercial_monthly", {}).items():
            for row in month_rows:
                c = row.get("count", 0)
                am = row.get("amount_total", 0)
                ar = row.get("arrears_total", 0)
                row_vals = [month_label, row["label"], fmt(c)]
                if r.get("has_arrears"):
                    row_vals.append(fmt(ar))
                    gt_arrears += ar
                row_vals.append(fmt(am))
                rows.append(row_vals)
                gt_count += c
                gt_amount += am
        grand = ["Grand Total", "", fmt(gt_count)]
        if r.get("has_arrears"):
            grand.append(fmt(gt_arrears))
        grand.append(fmt(gt_amount))

    elif card == "commercial-daily-income":
        title = "Daily Income for Commercials"
        headers, rows, grand = commercial_daily_income_export_rows(r)
        summary = [
            f"<b>Total Commercial Records:</b> {fmt(len(r.get('commercial_daily_income') or []))}",
            f"<b>{headers[-2]}:</b> Rs. {grand[-2] if grand else '0'}",
            f"<b>Total Amount Received:</b> Rs. {grand[-1] if grand else '0'}",
        ]

    elif card == "daily-staff-receive":
        title = "Daily Receive Amount of Staff"
        summary_headers, summary_rows, summary_grand, detail_headers, detail_rows = daily_staff_receive_export_tables(r)
        headers = ["Section", *summary_headers]
        rows = [["Summary", *row] for row in summary_rows]
        grand = ["Summary", *summary_grand] if summary_grand else None
        rows.extend([["", "", "", "", "", ""], ["Details", *detail_headers[:5]]])
        rows.extend([["Details", *row[:5]] for row in detail_rows])
        summary = [f"<b>Report Date:</b> {(r.get('daily_staff_receive') or {}).get('date_range') or 'Uploaded data'}"]

    elif card == "receipt-monthly":
        title = "Month-wise Report"
        headers = ["Month", "No. of Bills", "Arrears Received", "Current Amount Received", "Amount Received"]
        rows = []
        gt_count, gt_arrears, gt_amount = 0, 0, 0
        for row in r.get("receipt_monthly_rows", []):
            c = row.get("count", 0)
            ar = row.get("arrears_total", 0)
            am = row.get("amount_total", 0)
            current = am - ar
            rows.append([row["label"], fmt(c), fmt(ar), fmt(current), fmt(am)])
            gt_count += c
            gt_arrears += ar
            gt_amount += am
        gt_current = gt_amount - gt_arrears
        summary = [
            f"<b>Period:</b> {r.get('receipt_period_start', '')} to {r.get('receipt_period_end', '')}",
            f"<b>Total Amount Received:</b> Rs. {fmt(gt_amount)}",
            f"<b>Total Arrears Received:</b> Rs. {fmt(gt_arrears)}",
            f"<b>Total Current Amount Received:</b> Rs. {fmt(gt_current)}",
        ]
        grand = ["Grand Total", fmt(gt_count), fmt(gt_arrears), fmt(gt_current), fmt(gt_amount)]

    elif card == "connection-type-summary":
        title = "Summary"
        summary = ["<b>Connection type breakdown of total collections</b>"]
        source_rows = r.get("receipt_monthly_rows") or r.get("monthly_rows") or []
        overall_count = sum(row.get("count", 0) for row in source_rows)
        overall_arrears = sum(row.get("arrears_total", 0) for row in source_rows)
        overall_amount = sum(row.get("amount_total", 0) for row in source_rows)
        overall_current = overall_amount - overall_arrears
        comm_count = sum(row.get("count", 0) for row in (r.get("commercial_total") or []))
        comm_arrears = sum(row.get("arrears_total", 0) for row in (r.get("commercial_total") or []))
        comm_amount = sum(row.get("amount_total", 0) for row in (r.get("commercial_total") or []))
        comm_current = comm_amount - comm_arrears
        res_count = overall_count - comm_count
        res_arrears = overall_arrears - comm_arrears
        res_amount = overall_amount - comm_amount
        res_current = res_amount - res_arrears
        headers = ["Name", "No. of Bills", "Arrears Received", "Current Amount Received", "Amount Received"]
        rows = [
            ["Normal / Residential Connections", fmt(res_count), fmt(res_arrears), fmt(res_current), fmt(res_amount)],
            ["Commercial Connections", fmt(comm_count), fmt(comm_arrears), fmt(comm_current), fmt(comm_amount)],
        ]
        grand = ["Grand Total", fmt(overall_count), fmt(overall_arrears), fmt(overall_current), fmt(overall_amount)]

    else:
        flash("Unknown card type.")
        return redirect(url_for("index"))

    # Apply per-card column selection filtering for dashboard exports
    if card != "daily-staff-receive":
        cols_param = request.args.get("cols")
        col_map = _get_card_col_map(card, r)
        if cols_param and col_map:
            headers, rows, grand = _filter_card_export(cols_param, col_map, headers, rows, grand)

    # Build connection type summary if it should be attached to month-wise export
    conn_summary = None
    if request.args.get("include_connection_summary") == "true":
        conn_headers, conn_rows, conn_grand = build_connection_summary(r)
        conn_cols_param = request.args.get("connection_cols")
        if conn_cols_param:
            conn_headers, conn_rows, conn_grand = _filter_card_export(
                conn_cols_param, CONN_SUMMARY_COL_MAP, conn_headers, conn_rows, conn_grand)
        conn_summary = {"headers": conn_headers, "rows": conn_rows, "grand": conn_grand}

    if fmt_type == "pdf":
        if card == "commercial":
            month_rows = {}
            for month_label, m_rows in r.get("commercial_monthly", {}).items():
                section_rows = []
                for m_row in m_rows:
                    vals = [m_row["label"], fmt(m_row.get("count", 0))]
                    if r.get("has_arrears"):
                        vals.append(fmt(m_row.get("arrears_total", 0)))
                    vals.append(fmt(m_row.get("amount_total", 0)))
                    section_rows.append(vals)
                month_rows[fiscal_label_to_calendar_label(month_label)] = section_rows
            pdf_headers, pdf_rows, pdf_grand = remove_pdf_column(headers, rows, "No. of Bills", grand)
            for month_label, section_rows in list(month_rows.items()):
                _, section_pdf_rows, _ = remove_pdf_column(headers, section_rows, "No. of Bills")
                month_rows[month_label] = section_pdf_rows
            pdf_bytes = generate_commercial_pdf(
                summary,
                pdf_headers,
                pdf_rows,
                pdf_grand,
                month_rows,
                r.get("has_arrears"),
            )
        else:
            pdf_kwargs = {}
            pdf_headers, pdf_rows, pdf_grand = headers, rows, grand
            if card == "monthly":
                pdf_rows = [[fiscal_label_to_calendar_label(row[0]), *row[1:]] for row in pdf_rows]
            if card == "sector":
                page_w = landscape(A4)[0] - 30 * mm
                col_widths = [page_w * 0.58, page_w * 0.21, page_w * 0.21]
                pdf_kwargs = {
                    "pagesize": landscape(A4),
                    "col_widths": col_widths,
                    "first_col_left": True,
                }
            elif card == "commercial-total":
                page_w = A4[0] - 30 * mm
                if r.get("has_arrears"):
                    col_widths = [page_w * 0.38, page_w * 0.20, page_w * 0.21, page_w * 0.21]
                else:
                    col_widths = [page_w * 0.48, page_w * 0.26, page_w * 0.26]
                pdf_kwargs = {
                    "pagesize": A4,
                    "col_widths": col_widths,
                    "first_col_left": True,
                }
            elif card == "commercial-monthly":
                monthly_sections = []
                overall_arrears = 0
                overall_amount = 0
                overall_count = 0
                for month_label, month_rows in r.get("commercial_monthly", {}).items():
                    section_rows = []
                    month_arrears = 0
                    month_amount = 0
                    month_count = 0
                    for row in month_rows:
                        c = row.get("count", 0)
                        arrears_total = row.get("arrears_total", 0)
                        amount_total = row.get("amount_total", 0)
                        vals = [row["label"], fmt(c)]
                        if r.get("has_arrears"):
                            vals.append(fmt(arrears_total))
                            month_arrears += arrears_total
                        vals.append(fmt(amount_total))
                        month_amount += amount_total
                        month_count += c
                        section_rows.append(vals)
                    total_vals = ["Grand Total", fmt(month_count)]
                    if r.get("has_arrears"):
                        total_vals.append(fmt(month_arrears))
                        overall_arrears += month_arrears
                    total_vals.append(fmt(month_amount))
                    overall_amount += month_amount
                    overall_count += month_count
                    monthly_sections.append(
                        {
                            "month": fiscal_label_to_calendar_full_label(month_label),
                            "rows": section_rows,
                            "total": total_vals,
                        }
                    )
                overall_vals = ["Overall Total", fmt(overall_count)]
                if r.get("has_arrears"):
                    overall_vals.append(fmt(overall_arrears))
                overall_vals.append(fmt(overall_amount))

                # Apply column filtering to monthly_sections for PDF
                pdf_headers = ["Locality", "No. of Bills"]
                if r.get("has_arrears"):
                    pdf_headers.append("Arrears Received")
                pdf_headers.append("Amount Received")
                cols_param = request.args.get("cols")
                col_map = _get_card_col_map(card, r)
                if cols_param and col_map:
                    selected_keys = [k.strip() for k in cols_param.split(",") if k.strip()]
                    pdf_key_idx = {"locality": 0, "count": 1}
                    if r.get("has_arrears"):
                        pdf_key_idx["arrearsReceived"] = 2
                        pdf_key_idx["amountReceived"] = 3
                    else:
                        pdf_key_idx["amountReceived"] = 2
                    pdf_selected = [pdf_key_idx[k] for k in selected_keys if k in pdf_key_idx]
                    if pdf_selected and pdf_selected != list(range(len(pdf_headers))):
                        pdf_headers = [pdf_headers[i] for i in pdf_selected]
                        for section in monthly_sections:
                            section["rows"] = [[row[j] for j in pdf_selected] for row in section["rows"]]
                            section["total"] = [section["total"][0]] + [section["total"][j+1] for j in pdf_selected]
                        overall_vals = [overall_vals[0]] + [overall_vals[j+1] for j in pdf_selected]

                # Build PDF column widths dynamically
                n_cols = len(pdf_headers)
                page_w = A4[0] - 30 * mm
                if n_cols == 4:
                    pdf_col_widths = [page_w * 0.38, page_w * 0.20, page_w * 0.21, page_w * 0.21]
                elif n_cols == 3:
                    pdf_col_widths = [page_w * 0.48, page_w * 0.26, page_w * 0.26]
                elif n_cols == 2:
                    pdf_col_widths = [page_w * 0.62, page_w * 0.38]
                else:
                    pdf_col_widths = [page_w / n_cols] * n_cols

                pdf_bytes = generate_commercial_monthly_pdf(
                    summary,
                    monthly_sections,
                    overall_vals if monthly_sections else None,
                    r.get("has_arrears"),
                    pdf_headers=pdf_headers,
                    col_widths=pdf_col_widths,
                )
            elif card == "commercial-daily-income":
                page_w = landscape(A4)[0] - 18 * mm
                col_widths = [
                    page_w * 0.03,
                    page_w * 0.09,
                    page_w * 0.24,
                    page_w * 0.10,
                    page_w * 0.14,
                    page_w * 0.18,
                    page_w * 0.11,
                    page_w * 0.11,
                ]
                pdf_rows = wrap_pdf_table_cells(rows, font_size=10)
                pdf_kwargs = {
                    "pagesize": landscape(A4),
                    "col_widths": col_widths,
                    "first_col_left": False,
                    "left_cols": [],
                    "header_font_size": 11,
                    "body_font_size": 10,
                    "cell_padding": 8,
                }
            elif card == "connection-type-summary":
                page_w = A4[0] - 30 * mm
                col_widths = [page_w * 0.38, page_w * 0.20, page_w * 0.21, page_w * 0.21]
                pdf_kwargs = {
                    "pagesize": A4,
                    "col_widths": col_widths,
                    "first_col_left": True,
                    "left_cols": [0],
                }
            if card == "daily-staff-receive":
                pdf_bytes = generate_daily_staff_receive_pdf(r)
            elif card == "commercial-monthly":
                pass
            else:
                # Attach connection summary under month-wise/monthly report when checkbox checked
                if card in ("receipt-monthly", "monthly") and conn_summary is not None:
                    pdf_kwargs["extra_section"] = conn_summary
                    pdf_kwargs["compact"] = True
                pdf_bytes = generate_card_pdf(title, summary, pdf_headers, pdf_rows, pdf_grand, **pdf_kwargs)
        return Response(pdf_bytes, mimetype="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename={card}_report.pdf"})
    elif fmt_type == "csv":
        if card == "daily-staff-receive":
            summary_headers, summary_rows, summary_grand, detail_headers, detail_rows = daily_staff_receive_export_tables(r)
            csv_rows = [["Summary", *summary_headers]]
            csv_rows.extend([["Summary", *row] for row in summary_rows])
            if summary_grand:
                csv_rows.append(["Summary", *summary_grand])
            csv_rows.append([])
            csv_rows.append(["Details", *detail_headers])
            csv_rows.extend([["Details", *row] for row in detail_rows])
            csv_data = "\n".join(",".join(f'"{str(value).replace(chr(34), chr(34) + chr(34))}"' for value in row) for row in csv_rows)
            return Response(csv_data, mimetype="text/csv",
                            headers={"Content-Disposition": f"attachment; filename={card}_report.csv"})
        all_rows = rows + [grand] if grand else rows
        if headers and headers[0] == "Month":
            out = io.StringIO()
            out.write('\ufeff')
            out.write(",".join('"' + h + '"' for h in headers) + "\n")
            for row_data in all_rows:
                parts = []
                for i, val in enumerate(row_data):
                    val_str = str(val)
                    if i == 0:
                        parts.append('="' + val_str + '"')
                    else:
                        if ',' in val_str or '"' in val_str:
                            parts.append('"' + val_str.replace('"', '""') + '"')
                        else:
                            parts.append(val_str)
                out.write(",".join(parts) + "\n")
            csv_data = out.getvalue()
            # Append connection summary to monthly CSV when included
            if card in ("receipt-monthly", "monthly") and conn_summary is not None:
                csv_data += "\n"
                csv_data += "Summary\n"
                csv_data += ",".join('"' + h + '"' for h in conn_summary["headers"]) + "\n"
                conn_all_rows = conn_summary["rows"] + [conn_summary["grand"]]
                for row_data in conn_all_rows:
                    parts = []
                    for val in row_data:
                        val_str = str(val)
                        if ',' in val_str or '"' in val_str:
                            parts.append('"' + val_str.replace('"', '""') + '"')
                        else:
                            parts.append(val_str)
                    csv_data += ",".join(parts) + "\n"
        else:
            df = _card_rows_to_df(headers, all_rows)
            csv_data = df.to_csv(index=False)
        return Response(csv_data, mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={card}_report.csv"})
    elif fmt_type == "xlsx":
        if card == "daily-staff-receive":
            summary_headers, summary_rows, summary_grand, detail_headers, detail_rows = daily_staff_receive_export_tables(r)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                pd.DataFrame(summary_rows + ([summary_grand] if summary_grand else []), columns=summary_headers).to_excel(writer, sheet_name="Summary", index=False)
                pd.DataFrame(detail_rows, columns=detail_headers).to_excel(writer, sheet_name="Details", index=False)
            buf.seek(0)
            return Response(buf.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": f"attachment; filename={card}_report.xlsx"})
        all_rows = rows + [grand] if grand else rows
        buf = io.BytesIO()
        if headers and headers[0] == "Month":
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(headers)
            for row_data in all_rows:
                ws.append(row_data)
            for cell in ws["A"][1:]:
                cell.number_format = "@"
                cell.value = str(cell.value) if cell.value is not None else ""
            # Append connection summary to monthly XLSX when included
            if card in ("receipt-monthly", "monthly") and conn_summary is not None:
                ws.append([])
                ws.append(["Summary"])
                ws.append(conn_summary["headers"])
                conn_all_rows = conn_summary["rows"] + [conn_summary["grand"]]
                for row_data in conn_all_rows:
                    ws.append(row_data)
            wb.save(buf)
        else:
            df = _card_rows_to_df(headers, all_rows)
            df.to_excel(buf, index=False)
        buf.seek(0)
        return Response(buf.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f"attachment; filename={card}_report.xlsx"})

    flash("Unknown format type.")
    return redirect(url_for("index"))


@app.route("/daily-staff-receive/export/<fmt_type>")
def export_daily_staff_receive(fmt_type: str):
    if not _last_daily_staff_results:
        flash("No daily staff report is available. Please upload files first.")
        return redirect(url_for("daily_staff_receive"))
    cols = request.args.get("cols", "")
    detail_cols = request.args.get("detail_cols", "")
    return daily_staff_receive_export_response(fmt_type, _last_daily_staff_results, cols=cols, detail_cols=detail_cols)


if __name__ == "__main__":
    port = int(os.environ.get("WATER_SUPPLY_PORT", "5000"))
    host = os.environ.get("WATER_SUPPLY_HOST", "127.0.0.1")
    url = f"http://{host}:{port}"

    if os.environ.get("WATER_SUPPLY_NO_BROWSER") != "1":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print(f"Water Supply Report is running at {url}")
    print("Close this window to stop the app.")
    app.run(host=host, port=port, debug=False, use_reloader=False)
