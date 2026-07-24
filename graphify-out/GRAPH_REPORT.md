# Graph Report - water suppy report  (2026-07-24)

## Corpus Check
- 29 files · ~92,039 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 396 nodes · 1016 edges · 28 communities (26 shown, 2 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 17 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d5e20877`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BytesIO
- app.py
- DataFrame
- consumer_report
- _build_new_connection_detail_report
- Base Template
- upload-progress.js
- export_arrear_calculator
- app.py
- vercel.json
- Agent Instructions
- Claude Code CLI Prompt: Advanced Bill List Filters and Export
- Advanced Bill Filters Feature Prompt
- match_staff_assignment
- match_staff_assignment
- _build_connection_rate_report
- _normalize_staff_name
- new_connection_detail
- export_arrear_calculator

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 31 edges
2. `get_db()` - 26 edges
3. `init_bill_list_db()` - 22 edges
4. `download_card()` - 22 edges
5. `export_six_month_pitch()` - 18 edges
6. `summarize_dataframe()` - 17 edges
7. `parse_number()` - 16 edges
8. `build_daily_staff_receive_report()` - 16 edges
9. `Base Template` - 16 edges
10. `_GroupedPdfWrapper` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Arrear Calculator Page` --semantically_similar_to--> `Consumer Sector Report Page`  [INFERRED] [semantically similar]
  templates/arrear_calculator.html → templates/consumer_report.html
- `File Merger Page` --references--> `Flask route: file_merger`  [EXTRACTED]
  templates/file_merger.html → templates/base.html
- `Arrear Calculator Page` --extends--> `Base Template`  [EXTRACTED]
  templates/arrear_calculator.html → templates/base.html
- `Bills Reports Page` --extends--> `Base Template`  [EXTRACTED]
  templates/bill_list.html → templates/base.html
- `Consumer Sector Report Page` --extends--> `Base Template`  [EXTRACTED]
  templates/consumer_report.html → templates/base.html

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Reports-section pages extending base.html with shared sidebar nav** — tpl_index, tpl_bill_list, tpl_daily, tpl_consumer, tpl_consumer_remaining, tpl_arrear, tpl_base [INFERRED]
- **Client-side-only file tools (no server route, use browser CDN libraries)** — tpl_fcm, tpl_merge, ext_sheetjs, ext_pdflib [INFERRED]
- **Report pages with PDF/CSV/XLSX export endpoint families** — tpl_index, tpl_bill_list, tpl_consumer, tpl_consumer_remaining, tpl_daily, tpl_arrear, exp_index, exp_bill_list, exp_consumer, exp_consumer_remaining, exp_daily, exp_arrear [INFERRED]

## Communities (28 total, 2 thin omitted)

### Community 0 - "BytesIO"
Cohesion: 0.08
Nodes (65): bill_list_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), _bracket_rich_text(), build_connection_summary(), _card_rows_to_df(), commercial_daily_income_export_rows(), daily_staff_receive_export_response() (+57 more)

### Community 1 - "app.py"
Cohesion: 0.14
Nodes (17): _calc_col_widths(), export_advanced_bills(), export_advanced_bills_response(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), generate_zip_of_group_pdfs(), group_bills(), _GroupedPdfWrapper (+9 more)

### Community 2 - "DataFrame"
Cohesion: 0.10
Nodes (41): build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_monthly_rows(), build_private_society_mask() (+33 more)

### Community 3 - "consumer_report"
Cohesion: 0.11
Nodes (31): apply_manual_zone_overrides(), bill_list(), bill_list_sector_seasonly_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data(), export_sectors_summary(), export_staff_summary(), export_zones_summary() (+23 more)

### Community 4 - "_build_new_connection_detail_report"
Cohesion: 0.23
Nodes (12): _build_new_connection_detail_report(), _ncd_classification(), _ncd_decimal(), _ncd_int(), _ncd_load_file(), _ncd_norm(), _ncd_parse_date(), _ncd_pick_column() (+4 more)

### Community 5 - "Base Template"
Cohesion: 0.09
Nodes (31): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database, Portable App README (root), Python Dependencies (requirements.txt), Export Endpoints: export_arrear_calculator, Bill List Export Endpoints (zones/sectors/staff/unpaid/zone/staff/six-month/season) (+23 more)

### Community 6 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 7 - "export_arrear_calculator"
Cohesion: 0.06
Nodes (55): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), build_dashboard_results(), _canonical_consumer_sector_locality() (+47 more)

### Community 8 - "app.py"
Cohesion: 0.08
Nodes (20): _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), download_file(), export_bill_list_zone(), export_daily_staff_receive(), export_daily_staff_receive_summary_pdf(), file_column_matcher(), file_merger() (+12 more)

### Community 9 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 19 - "Agent Instructions"
Cohesion: 0.18
Nodes (10): Agent Instructions, Auto-Update on Changes, Commands, Development Guidelines, Graph Status, Graphify - Knowledge Graph, Key Architecture Nodes (from last graphify run), Ponytail - Lazy Senior Dev Mode (+2 more)

### Community 22 - "match_staff_assignment"
Cohesion: 0.12
Nodes (18): backfill_bill_arrears(), _bill_list_summary_from_rows(), build_daily_staff_receive_report(), clear_unmatched_log(), _connection_rate_rows_from_payload(), get_unmatched_log(), is_large_pdf_text(), load_staff_assignment_rows() (+10 more)

### Community 23 - "match_staff_assignment"
Cohesion: 0.31
Nodes (9): clean_cell(), _deep_normalize_sector(), _keyword_set(), load_alias_rules(), match_by_alias(), match_key(), match_staff_assignment(), Aggressively normalize a sector/locality name for robust matching. (+1 more)

### Community 24 - "_build_connection_rate_report"
Cohesion: 0.15
Nodes (19): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description() (+11 more)

### Community 25 - "_normalize_staff_name"
Cohesion: 0.29
Nodes (8): _closest_staff_key(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), _levenshtein(), _normalize_sector_locality(), _normalize_staff_name(), Like fmt_staff_name but returns HTML with <br> for display.

### Community 26 - "new_connection_detail"
Cohesion: 0.67
Nodes (4): _clear_new_connection_detail_cache(), _load_new_connection_detail_cache(), new_connection_detail(), _save_new_connection_detail_cache()

### Community 27 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list.      Fixed column orde, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

## Knowledge Gaps
- **18 isolated node(s):** `$schema`, `maxDuration`, `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_GroupedPdfWrapper` connect `app.py` to `app.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `generate_grouped_advanced_pdf()` connect `app.py` to `app.py`, `BytesIO`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `_get_season_bill_ids()` connect `consumer_report` to `app.py`, `BytesIO`, `export_arrear_calculator`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **What connects `Aggressively normalize a sector/locality name for robust matching.`, `Extract significant keywords from a sector/locality name.`, `Return display name: paired staff on separate lines, else as-is.` to the rest of the system?**
  _84 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `BytesIO` be split into smaller, more focused modules?**
  _Cohesion score 0.08076923076923077 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1402116402116402 - nodes in this community are weakly interconnected._
- **Should `DataFrame` be split into smaller, more focused modules?**
  _Cohesion score 0.09878048780487805 - nodes in this community are weakly interconnected._