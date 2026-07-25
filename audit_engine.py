"""Sector-wise auditor for the DNS Register connection CSVs.

Pure logic, no Flask. ``app.py`` imports this module; this module never imports
``app.py``. Run it directly to self-check against a register folder::

    python audit_engine.py "C:\\Users\\Rising\\Downloads\\DNS Register\\Year 2025-2026"
"""

from __future__ import annotations

import csv
import io
import os
import sys
from collections import namedtuple

# The register export is rectangular for data rows and short for total rows.
HEADER = (
    "Sector", "Locality", "SR", "Name", "F/H Name", "Connection No", "Old Connection No",
    "Arrear",
    "Half Year 1. (Jul - Dec) - Dmd / Coll.", "Half Year 1. (Jul - Dec) - Balance.",
    "Half Year 2. (Jan - Jun) - Dmd / Coll.", "Half Year 2. (Jan - Jun) - Balance.",
    "Total Demand", "Demand + Arrear", "Total Collection", "Recovered Arrear", "Pending Amount",
)
DATA_FIELDS = 17
# Total rows drop Name, F/H Name, Connection No and Old Connection No.
TOTAL_FIELDS = 13
# Annual demand is billed in 600-rupee steps; anything else is off-tariff.
TARIFF_STEP = 600


def _money(value) -> float | None:
    """'4,800' -> 4800.0, '' -> 0.0, garbage -> None."""
    text = str(value or "").strip().replace(",", "")
    if text in ("", "-"):
        return 0.0
    try:
        return float(text)
    except ValueError:
        return None


def _pair(value) -> tuple[float | None, float | None]:
    """'4,800 / 2,400' -> (4800.0, 2400.0). Demand / collection in one cell."""
    left, sep, right = str(value or "").partition("/")
    if not sep:
        return _money(left), 0.0
    return _money(left), _money(right)


def _default_classify(sector: str, locality: str) -> str:
    """Fallback used when the caller does not supply app.py's classifier."""
    text = f"{sector} {locality}".upper()
    if "COMMERCIAL" in text:
        return "Commercial"
    if any(word in text for word in ("PRIVATE SOCIETY", "PRIVATE SOCITIES", "PRIVATE SOCIETIES", "PRIVATE SO")):
        return "Private Societies"
    return "Domestic"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_register(text: str, source: str = "", classify=None) -> tuple[list[dict], list[dict], list[dict]]:
    """Parse one register CSV into (rows, totals, problems).

    Never raises on malformed input - anything unexpected lands in ``problems``
    so the audit reports the defect instead of dying on it.
    """
    classify = classify or _default_classify
    rows: list[dict] = []
    totals: list[dict] = []
    problems: list[dict] = []

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        problems.append({"source": source, "line": 0, "issue": "Empty file", "detail": ""})
        return rows, totals, problems

    header = [h.lstrip("\ufeff").strip() for h in header]
    if tuple(header) != HEADER:
        problems.append({
            "source": source, "line": 1, "issue": "Unexpected header",
            "detail": f"{len(header)} columns, expected {DATA_FIELDS}",
        })

    for line_no, raw in enumerate(reader, start=2):
        if not any(str(cell).strip() for cell in raw):
            continue
        is_total = len(raw) > 2 and str(raw[2]).strip().lower() == "total"

        if is_total:
            if len(raw) == TOTAL_FIELDS:
                # CSV export drops Name, F/H Name, Connection No, Old Connection No
                raw = raw[:3] + ["", "", "", ""] + raw[3:]
            elif len(raw) != DATA_FIELDS:
                problems.append({
                    "source": source, "line": line_no, "issue": "Total row field count",
                    "detail": f"{len(raw)} fields, expected {TOTAL_FIELDS} or {DATA_FIELDS}",
                })
                continue
            # realigned above, so total rows now read at the same offsets as data rows
            h1d, h1c = _pair(raw[8])
            h2d, h2c = _pair(raw[10])
            totals.append({
                "source": source, "line": line_no,
                "sector": raw[0].strip(), "locality": raw[1].strip(),
                "arrear": _money(raw[7]), "h1_demand": h1d, "h1_collection": h1c,
                "h1_balance": _money(raw[9]), "h2_demand": h2d, "h2_collection": h2c,
                "h2_balance": _money(raw[11]), "total_demand": _money(raw[12]),
                "demand_arrear": _money(raw[13]), "total_collection": _money(raw[14]),
                "recovered_arrear": _money(raw[15]), "pending": _money(raw[16]),
            })
            continue

        if len(raw) != DATA_FIELDS:
            problems.append({
                "source": source, "line": line_no, "issue": "Data row field count",
                "detail": f"{len(raw)} fields, expected {DATA_FIELDS}",
            })
            continue

        h1d, h1c = _pair(raw[8])
        h2d, h2c = _pair(raw[10])
        sector, locality = raw[0].strip(), raw[1].strip()
        row = {
            "source": source, "line": line_no,
            "sector": sector, "locality": locality,
            "sr": raw[2].strip(), "name": raw[3].strip(), "fh_name": raw[4].strip(),
            # keep as text - connection numbers carry leading zeros (002900777)
            "conn_no": raw[5].strip(), "old_conn_no": raw[6].strip(),
            "arrear": _money(raw[7]),
            "h1_demand": h1d, "h1_collection": h1c, "h1_balance": _money(raw[9]),
            "h2_demand": h2d, "h2_collection": h2c, "h2_balance": _money(raw[11]),
            "total_demand": _money(raw[12]), "demand_arrear": _money(raw[13]),
            "total_collection": _money(raw[14]),
            "recovered_arrear": _money(raw[15]), "recovered_arrear_raw": raw[15],
            "pending": _money(raw[16]),
            "classification": classify(sector, locality),
        }
        unparseable = [k for k, v in row.items() if v is None]
        if unparseable:
            problems.append({
                "source": source, "line": line_no, "issue": "Unreadable amount",
                "detail": ", ".join(sorted(unparseable)),
            })
            continue
        rows.append(row)

    return rows, totals, problems


# ---------------------------------------------------------------------------
# Check registry
# ---------------------------------------------------------------------------

Check = namedtuple("Check", "id title severity category scope predicate impact action")

# severity: CRITICAL | HIGH | MEDIUM | LOW
# category: money (cash at risk) | quality (data hygiene)
# scope:    row (list every offender) | systemic (count only, no exception list)

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _hidden_arrear(r: dict) -> float:
    """Balance the half-year demand cannot explain - i.e. dues carried from before."""
    return r["h2_balance"] - (r["h2_demand"] - r["h2_collection"])


CHECKS = [
    Check(
        "A1", "Payment received but shown as minus - arrear never credited",
        "CRITICAL", "money", "row",
        lambda r: r["pending"] < 0,
        lambda r: -r["pending"],
        "Post the excess into 'Recovered Arrear' and clear the negative pending.",
    ),
    Check(
        "A2", "Hidden arrear - Arrear column shows 0 but balance proves old dues",
        "CRITICAL", "money", "row",
        # the h2_balance > 0 guard is load-bearing: without it every A1 overpayer
        # fires here too, because (demand - collection) goes negative.
        lambda r: r["arrear"] == 0 and r["h2_balance"] > 0 and _hidden_arrear(r) > 0.5,
        _hidden_arrear,
        "Post the carried balance into the Arrear column so the receivable is on the books.",
    ),
    Check(
        "A3", "Arrear outstanding although the consumer paid this year",
        "HIGH", "money", "row",
        lambda r: r["arrear"] > 0 and r["recovered_arrear"] == 0 and r["total_collection"] > 0,
        lambda r: r["arrear"],
        "Check the receipt: if part of the payment cleared old dues, record it as Recovered Arrear.",
    ),
    Check(
        "A4", "No Jul-Dec demand raised against a billed connection",
        "HIGH", "money", "row",
        lambda r: r["h1_demand"] == 0 and r["h2_demand"] > 0,
        lambda r: r["h2_demand"],
        "Confirm the connection date; raise the missing first-half demand or flag the connection as new.",
    ),
    Check(
        "A5", "Connection on the register with no demand at all",
        "HIGH", "money", "row",
        lambda r: r["total_demand"] == 0,
        lambda r: 0.0,
        "Bill the connection or close it - it is occupying the register while earning nothing.",
    ),
    Check(
        "A6", "No Jan-Jun demand raised against a billed connection",
        "MEDIUM", "money", "row",
        lambda r: r["h2_demand"] == 0 and r["h1_demand"] > 0,
        lambda r: r["h1_demand"],
        "Confirm whether the connection closed mid-year; otherwise raise the second-half demand.",
    ),
    Check(
        "B1", "Jan-Jun balance does not equal demand minus collection",
        "MEDIUM", "quality", "row",
        lambda r: r["h2_balance"] > 0 and abs(_hidden_arrear(r)) > 0.5,
        lambda r: abs(_hidden_arrear(r)),
        "Recompute the balance column; it is not a running balance and cannot be trusted for recovery.",
    ),
    Check(
        "B2", "Negative arrear carried forward",
        "MEDIUM", "quality", "row",
        lambda r: r["arrear"] < 0,
        lambda r: -r["arrear"],
        "A credit balance cannot sit in Arrear - move it to an advance/credit head.",
    ),
    Check(
        "B3", "Off-tariff annual demand",
        "MEDIUM", "quality", "row",
        lambda r: r["total_demand"] > 0 and round(r["total_demand"]) % TARIFF_STEP != 0,
        lambda r: 0.0,
        f"Demand is not a multiple of {TARIFF_STEP}; verify the tariff applied to this connection.",
    ),
    Check(
        "B4", "'Recovered Arrear' column never posted",
        "HIGH", "quality", "systemic",
        lambda r: r["recovered_arrear_raw"].strip() == "",
        lambda r: 0.0,
        "Make Recovered Arrear mandatory at data entry - it is the only place arrear recovery can be evidenced.",
    ),
    Check(
        "B5", "Old Connection No missing",
        "LOW", "quality", "systemic",
        lambda r: r["old_conn_no"] in ("", "0", "00"),
        lambda r: 0.0,
        "Backfill the old connection number so historic ledgers can be matched.",
    ),
    Check(
        "B6", "Father/Husband name is a placeholder",
        "LOW", "quality", "systemic",
        # dashes run from "-" to 16 chars long and "NONE" is used 128 times, so
        # matching a fixed list of dash strings misses two thirds of these
        lambda r: r["fh_name"].strip("- .").upper() in ("", "NONE", "NIL", "NA", "N/A"),
        lambda r: 0.0,
        "Complete the consumer record - required to trace the connection holder.",
    ),
    Check(
        "B7", "Collection is not a round amount",
        "LOW", "quality", "systemic",
        lambda r: r["total_collection"] and round(r["total_collection"]) % 100 != 0,
        lambda r: 0.0,
        "Verify the receipt: odd amounts usually mean a surcharge or part payment was merged in.",
    ),
]

CHECKS_BY_ID = {c.id: c for c in CHECKS}

# Two very different kinds of money, kept apart so neither headline is inflated:
# RECOVERABLE is already owed to the institute but recorded wrongly, so it can be
# chased today. UNBILLED was never demanded at all - it is revenue to raise, not collect.
RECOVERABLE_CHECKS = {"A1", "A2", "A3", "B2"}
UNBILLED_CHECKS = {"A4", "A6"}


def run_checks(row: dict) -> list[tuple[Check, float]]:
    """Return every check this row fails, with the money it puts at risk."""
    failed = []
    for check in CHECKS:
        try:
            if check.predicate(row):
                failed.append((check, round(check.impact(row), 2)))
        except (TypeError, KeyError):
            continue
    return failed


# ---------------------------------------------------------------------------
# Negative Pending Amount - verdict per record
# ---------------------------------------------------------------------------

SURCHARGE_RATE = 0.10

TRACE = ("Set Pending to 0 - a minus balance must never be carried forward as credit. "
         "Pull the receipt and trace the excess: if it cleared an earlier year, post that year "
         "into Arrear and the payment into Recovered Arrear; if it belongs to another consumer "
         "or period, reverse it and re-post there.")
NEGATIVE_ACTIONS = {
    "No bill exists - receipt posted against zero demand":
        "Raise the missing demand for this connection, then re-apply the receipt. If no bill is "
        "due, the receipt belongs elsewhere - reverse and re-post it. " + TRACE,
    "Credit balance parked in the Arrear column":
        "Clear the negative Arrear to zero and recompute Demand + Arrear. The false credit is "
        "hiding a genuine due - the corrected pending below is what is actually recoverable.",
    "Collection exceeds billed demand - earlier-period due never posted":
        "Treat as unposted arrear, not advance. " + TRACE,
    "Surcharge merged into water collection":
        "Move the surcharge out of Total Collection into the surcharge/fine head - it is not "
        "water demand and must not reduce a future bill. " + TRACE,
    "Keying error in the collection figure":
        "Check the receipt and correct the collection amount (e.g. 2,403 keyed for 2,400). " + TRACE,
}
NEGATIVE_PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "-": 4}


def classify_negative(r: dict) -> tuple[str, str, str, str]:
    """(verdict, reason, priority, action) for a row whose Pending Amount is below zero.

    Policy: a negative pending is ALWAYS an error unless there is positive evidence of a
    genuine advance. This register carries no receipt date, no payment history and no
    advance/credit head, and Recovered Arrear is blank on every row - so no advance can
    be evidenced from this source and nothing here is ever marked Valid. A minus balance
    is a double loss: the original amount stays uncollected somewhere, and the false
    credit silently reduces a future recoverable bill.
    """
    excess = round(-r["pending"], 2)
    demand = r["total_demand"]
    if r["arrear"] < 0:
        reason, pri = "Credit balance parked in the Arrear column", "P1"
    elif demand == 0:
        reason, pri = "No bill exists - receipt posted against zero demand", "P1"
    elif abs(excess - round(demand * SURCHARGE_RATE)) < 0.5:
        reason, pri = "Surcharge merged into water collection", "P3"
    elif excess % 10 != 0:
        reason, pri = "Keying error in the collection figure", "P4"
    else:
        reason, pri = "Collection exceeds billed demand - earlier-period due never posted", "P2"
    return "Incorrect", reason, pri, NEGATIVE_ACTIONS[reason]


def correct_pending(r: dict) -> tuple[float, float]:
    """(correct pending, unallocated receipt) for a row with a negative pending.

    A negative Arrear is not a real reduction of what is owed, so it is floored at zero
    before the receivable is rebuilt - that is what turns a false credit back into a
    genuine due. Collection is then capped at the receivable: the surplus is an
    unallocated receipt to be traced, never a credit against next year.
    """
    receivable = r["total_demand"] + max(0.0, r["arrear"])
    applied = min(r["total_collection"], receivable)
    return round(receivable - applied, 2), round(r["total_collection"] - applied, 2)


def _negative_row(r: dict) -> dict:
    verdict, reason, pri, action = classify_negative(r)
    fixed, unallocated = correct_pending(r)
    flags = []
    if r["arrear"] < 0:
        flags.append("Credit parked in Arrear column")
    if not r["recovered_arrear_raw"].strip():
        flags.append("Recovered Arrear left blank")
    return {
        "sector": r["sector"], "locality": r["locality"], "sr": r["sr"], "name": r["name"],
        "conn_no": r["conn_no"], "arrear": r["arrear"],
        "total_demand": r["total_demand"], "total_collection": r["total_collection"],
        "pending": r["pending"], "excess": round(-r["pending"], 2),
        "correct_pending": fixed, "unallocated": unallocated,
        "half1": f"{r['h1_demand']:,.0f} / {r['h1_collection']:,.0f}",
        "half2": f"{r['h2_demand']:,.0f} / {r['h2_collection']:,.0f}",
        "verdict": verdict, "reason": reason, "priority": pri, "action": action,
        "flags": "; ".join(flags), "source": r["source"],
    }


# ---------------------------------------------------------------------------
# Proposed corrections (derived, never applied)
# ---------------------------------------------------------------------------

def _corrections_for(row: dict, failed: list[tuple[Check, float]]) -> list[dict]:
    out = []
    ids = {c.id for c, _ in failed}
    amounts = {c.id: amt for c, amt in failed}
    base = {
        "sector": row["sector"], "locality": row["locality"], "sr": row["sr"],
        "name": row["name"], "conn_no": row["conn_no"],
    }
    if "A1" in ids:
        excess = amounts["A1"]
        out.append({**base, "check": "A1", "field": "Recovered Arrear",
                    "current_value": row["recovered_arrear_raw"].strip() or "(blank)",
                    "proposed_value": f"{excess:,.0f}", "amount": excess,
                    "reason": "Consumer paid more than the demand; the excess cleared old dues and must be evidenced here."})
        out.append({**base, "check": "A1", "field": "Pending Amount",
                    "current_value": f"{row['pending']:,.0f}", "proposed_value": "0", "amount": excess,
                    "reason": "Negative pending is not a real credit - it masks default elsewhere in the sector total."})
    if "A2" in ids:
        hidden = amounts["A2"]
        out.append({**base, "check": "A2", "field": "Arrear",
                    "current_value": f"{row['arrear']:,.0f}", "proposed_value": f"{hidden:,.0f}", "amount": hidden,
                    "reason": "Balance carries dues the Arrear column does not show, so the receivable is understated."})
    if "B2" in ids:
        out.append({**base, "check": "B2", "field": "Arrear",
                    "current_value": f"{row['arrear']:,.0f}", "proposed_value": "0", "amount": amounts["B2"],
                    "reason": "Credit balance parked in Arrear; move it to an advance head."})
    return out


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

MONEY_KEYS = ("arrear", "total_demand", "demand_arrear", "total_collection", "pending")


def _blank_totals() -> dict:
    return {k: 0.0 for k in MONEY_KEYS}


def _recovery_pct(collected: float, receivable: float) -> float:
    return round(collected / receivable * 100, 2) if receivable else 0.0


def build_audit_report(sources: list[tuple[str, str]], classify=None) -> dict:
    """sources = [(filename, file_text), ...] -> the full audit report."""
    rows: list[dict] = []
    totals: list[dict] = []
    problems: list[dict] = []
    empty_files: list[str] = []

    for name, text in sources:
        r, t, p = parse_register(text, source=name, classify=classify)
        if not r:
            empty_files.append(name)
        rows.extend(r)
        totals.extend(t)
        problems.extend(p)

    exceptions: list[dict] = []
    corrections: list[dict] = []
    finding_rows: dict[str, int] = {c.id: 0 for c in CHECKS}
    finding_amount: dict[str, float] = {c.id: 0.0 for c in CHECKS}
    finding_sectors: dict[str, set] = {c.id: set() for c in CHECKS}
    risk_by_conn: dict[tuple, float] = {}
    unbilled_by_conn: dict[tuple, float] = {}
    sector_bucket: dict[str, dict] = {}

    for row in rows:
        failed = run_checks(row)
        sector = row["sector"]
        bucket = sector_bucket.setdefault(sector, {
            "sector": sector, "classification": row["classification"],
            "connections": 0, "localities": set(), "sources": set(),
            "critical": 0, "high": 0, "money_at_risk": 0.0, "unbilled": 0.0, **_blank_totals(),
        })
        bucket["connections"] += 1
        bucket["localities"].add(row["locality"])
        bucket["sources"].add(row["source"])
        for key in MONEY_KEYS:
            bucket[key] += row[key]

        key = (row["source"], row["sector"], row["locality"], row["conn_no"], row["sr"])
        for check, amount in failed:
            finding_rows[check.id] += 1
            finding_amount[check.id] += amount
            finding_sectors[check.id].add(sector)
            if check.severity == "CRITICAL":
                bucket["critical"] += 1
            elif check.severity == "HIGH":
                bucket["high"] += 1
            # de-duplicate: one connection failing three checks is still one
            # connection's worth of money, so take its largest exposure in each group
            if amount and check.id in RECOVERABLE_CHECKS:
                risk_by_conn[key] = max(risk_by_conn.get(key, 0.0), amount)
            elif amount and check.id in UNBILLED_CHECKS:
                unbilled_by_conn[key] = max(unbilled_by_conn.get(key, 0.0), amount)
            if check.scope == "row":
                exceptions.append({
                    "sector": sector, "locality": row["locality"], "sr": row["sr"],
                    "name": row["name"], "conn_no": row["conn_no"],
                    "check": check.id, "issue": check.title, "severity": check.severity,
                    "amount": amount, "arrear": row["arrear"],
                    "total_demand": row["total_demand"], "demand_arrear": row["demand_arrear"],
                    "total_collection": row["total_collection"], "pending": row["pending"],
                    "action": check.action, "source": row["source"],
                })
        corrections.extend(_corrections_for(row, failed))

    for key, amount in risk_by_conn.items():
        sector_bucket[key[1]]["money_at_risk"] += amount
    for key, amount in unbilled_by_conn.items():
        sector_bucket[key[1]]["unbilled"] += amount

    # --- institute roll-up -------------------------------------------------
    institute = _blank_totals()
    for row in rows:
        for k in MONEY_KEYS:
            institute[k] += row[k]
    institute["connections"] = len(rows)
    institute["recovery_pct"] = _recovery_pct(institute["total_collection"], institute["demand_arrear"])
    institute["money_at_risk"] = round(sum(risk_by_conn.values()), 2)
    institute["unbilled"] = round(sum(unbilled_by_conn.values()), 2)
    institute["critical"] = sum(finding_rows[c.id] for c in CHECKS if c.severity == "CRITICAL")
    institute["high"] = sum(finding_rows[c.id] for c in CHECKS if c.severity == "HIGH")

    # --- findings ----------------------------------------------------------
    findings = [{
        "id": c.id, "issue": c.title, "severity": c.severity,
        "category": "Money at risk" if c.category == "money" else "Data quality",
        "scope": c.scope, "rows": finding_rows[c.id], "amount": round(finding_amount[c.id], 2),
        "sectors": len(finding_sectors[c.id]), "action": c.action,
    } for c in CHECKS if finding_rows[c.id]]
    findings.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], -f["amount"], -f["rows"]))

    # --- sector league table ----------------------------------------------
    sectors = []
    for bucket in sector_bucket.values():
        receivable = bucket["demand_arrear"]
        recovery = _recovery_pct(bucket["total_collection"], receivable)
        # recovery rate less the share of the receivable that is mis-recorded.
        # Deliberately uncapped and allowed to go negative - clamping it made every
        # bad sector score 0.0 and the league table stopped ranking.
        penalty = bucket["money_at_risk"] / receivable * 100 if receivable else 0.0
        sectors.append({
            **{k: round(bucket[k], 2) for k in MONEY_KEYS},
            "sector": bucket["sector"], "classification": bucket["classification"],
            "connections": bucket["connections"], "localities": len(bucket["localities"]),
            "critical": bucket["critical"], "high": bucket["high"],
            "money_at_risk": round(bucket["money_at_risk"], 2),
            "unbilled": round(bucket["unbilled"], 2),
            "recovery_pct": recovery,
            "health_score": round(recovery - penalty, 1),
        })
    sectors.sort(key=lambda s: (s["health_score"], -s["money_at_risk"]))

    sector_findings: dict[str, list[dict]] = {}
    for exc in exceptions:
        sector_findings.setdefault(exc["sector"], []).append(exc)

    exceptions.sort(key=lambda e: (SEVERITY_ORDER[e["severity"]], -e["amount"]))
    corrections.sort(key=lambda c: -c["amount"])

    negatives = [_negative_row(r) for r in rows if r["pending"] < 0]
    negatives.sort(key=lambda n: (NEGATIVE_PRIORITY_ORDER[n["priority"]], -n["excess"]))
    negatives_summary = []
    for pri in ("P1", "P2", "P3", "P4", "-"):
        part = [n for n in negatives if n["priority"] == pri]
        if part:
            negatives_summary.append({
                "priority": pri, "verdict": part[0]["verdict"], "reason": part[0]["reason"],
                "rows": len(part), "amount": round(sum(n["excess"] for n in part), 2),
                "sectors": len({n["sector"] for n in part}), "action": part[0]["action"],
            })

    return {
        "meta": {
            "files": len(sources), "rows": len(rows), "total_rows": len(totals),
            "sectors": len(sector_bucket),
            "localities": len({(r["sector"], r["locality"]) for r in rows}),
            "empty_files": empty_files,
        },
        "institute": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in institute.items()},
        "findings": findings,
        "sectors": sectors,
        "sector_findings": sector_findings,
        "exceptions": exceptions,
        "corrections": corrections,
        "negatives": negatives,
        "negatives_summary": negatives_summary,
        "structural": _structural(rows, totals, problems, empty_files),
    }


def _structural(rows: list[dict], totals: list[dict], problems: list[dict], empty_files: list[str]) -> dict:
    """File-level findings: footing verification, identity checks, empty sectors."""
    by_locality: dict[tuple, list[dict]] = {}
    for row in rows:
        by_locality.setdefault((row["source"], row["sector"], row["locality"]), []).append(row)

    footing = []
    agree = 0
    for total in totals:
        key = (total["source"], total["sector"], total["locality"])
        part = by_locality.get(key, [])
        if not part:
            footing.append({"source": total["source"], "sector": total["sector"],
                            "locality": total["locality"], "column": "(no data rows)",
                            "total_row": "", "column_sum": "", "difference": ""})
            continue
        diffs = []
        for field in ("arrear", "h1_demand", "h1_collection", "h1_balance", "h2_demand",
                      "h2_collection", "h2_balance", "total_demand", "demand_arrear",
                      "total_collection", "pending"):
            summed = sum(r[field] for r in part)
            stated = total[field]
            if stated is None or abs(stated - summed) > 0.5:
                diffs.append((field, stated, summed))
        if diffs:
            for field, stated, summed in diffs:
                footing.append({
                    "source": total["source"], "sector": total["sector"],
                    "locality": total["locality"], "column": field,
                    "total_row": stated, "column_sum": round(summed, 2),
                    "difference": round((stated or 0) - summed, 2),
                })
        else:
            agree += 1

    identity = []
    for row in rows:
        for label, stated, expected in (
            ("Total Demand", row["total_demand"], row["h1_demand"] + row["h2_demand"]),
            ("Demand + Arrear", row["demand_arrear"], row["total_demand"] + row["arrear"]),
            ("Total Collection", row["total_collection"], row["h1_collection"] + row["h2_collection"]),
            ("Pending Amount", row["pending"], row["demand_arrear"] - row["total_collection"]),
        ):
            if abs(stated - expected) > 0.5:
                identity.append({
                    "sector": row["sector"], "locality": row["locality"], "sr": row["sr"],
                    "conn_no": row["conn_no"], "column": label,
                    "stated": stated, "expected": round(expected, 2),
                    "difference": round(stated - expected, 2),
                })

    return {
        "footing_agree": agree,
        "footing_total": len(totals),
        "footing_issues": footing,
        "identity_issues": identity,
        "problems": problems,
        "empty_files": [{"source": name, "issue": "Sector file has no connections",
                         "detail": "Header row only"} for name in empty_files],
        "total_row_shape": {
            "count": len(totals),
            "issue": f"Summary rows carry {TOTAL_FIELDS} fields against a {DATA_FIELDS}-column header",
            "detail": "Name, F/H Name, Connection No and Old Connection No are omitted, so a "
                      "positional read puts Arrear under Name. Pad the export with four empty fields.",
        },
    }


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------

def load_folder(folder: str) -> list[tuple[str, str]]:
    out = []
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith(".csv"):
            with open(os.path.join(folder, name), encoding="utf-8-sig") as fh:
                out.append((name, fh.read()))
    return out


def _selfcheck(folder: str) -> int:
    report = build_audit_report(load_folder(folder))
    meta, inst, struct = report["meta"], report["institute"], report["structural"]
    found = {f["id"]: f for f in report["findings"]}

    def got(cid, field):
        return found.get(cid, {}).get(field, 0)

    expected = [
        ("files", meta["files"], 78),
        ("rows", meta["rows"], 8953),
        ("total rows", meta["total_rows"], 84),
        ("empty files", len(meta["empty_files"]), 9),
        ("A1 rows", got("A1", "rows"), 931),
        ("A1 amount", round(got("A1", "amount")), 1_509_252),
        # regression test for the h2_balance>0 guard - drops to 4253/32612428 without it
        ("A2 rows", got("A2", "rows"), 3779),
        ("A2 amount", round(got("A2", "amount")), 31_296_748),
        ("B1 rows", got("B1", "rows"), 3863),
        ("B4 rows", got("B4", "rows"), 8953),
        ("B5 rows", got("B5", "rows"), 1516),
        ("B6 rows", got("B6", "rows"), 451),
        ("B7 rows", got("B7", "rows"), 673),
        ("footing agree", struct["footing_agree"], 84),
        ("footing issues", len(struct["footing_issues"]), 0),
        ("identity issues", len(struct["identity_issues"]), 0),
        ("parse problems", len(struct["problems"]), 0),
        ("negative rows", len(report["negatives"]), 931),
        # strict policy: nothing is Valid without advance evidence, and this source has none
        ("negative incorrect", sum(1 for n in report["negatives"] if n["verdict"] == "Incorrect"), 931),
        ("negative valid", sum(1 for n in report["negatives"] if n["verdict"] == "Valid"), 0),
        ("negatives left minus", sum(1 for n in report["negatives"] if n["correct_pending"] < 0), 0),
        ("receivable", round(inst["demand_arrear"]), 25_062_554),
        ("collected", round(inst["total_collection"]), 12_184_160),
        ("pending", round(inst["pending"]), 12_878_394),
    ]

    failures = 0
    for label, actual, want in expected:
        ok = actual == want
        failures += 0 if ok else 1
        print(f"  {'OK  ' if ok else 'FAIL'}  {label:<18} {actual:>12,}" + ("" if ok else f"   expected {want:,}"))

    print(f"\n  recovery {inst['recovery_pct']}%   recoverable-now PKR {inst['money_at_risk']:,.0f}"
          f"   unbilled PKR {inst['unbilled']:,.0f}"
          f"   critical {inst['critical']:,}   high {inst['high']:,}")
    print(f"  exceptions {len(report['exceptions']):,}   corrections {len(report['corrections']):,}"
          f"   sectors {meta['sectors']}   localities {meta['localities']}")
    print("\n  findings:")
    for f in report["findings"]:
        print(f"    {f['id']:<3} {f['severity']:<8} {f['rows']:>6,} rows   PKR {f['amount']:>14,.0f}   {f['issue'][:58]}")
    print("\n  worst sectors by health score:")
    for s in report["sectors"][:5]:
        print(f"    {s['health_score']:>6.1f}  {s['recovery_pct']:>6.2f}%  risk {s['money_at_risk']:>12,.0f}  {s['sector'][:44]}")

    print("\nSELF-CHECK " + ("PASSED" if not failures else f"FAILED ({failures} mismatch)"))
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(_selfcheck(sys.argv[1]))
