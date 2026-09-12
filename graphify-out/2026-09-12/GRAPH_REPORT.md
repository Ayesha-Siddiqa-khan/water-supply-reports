# Graph Report - .  (2026-09-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 644 nodes · 1605 edges · 55 communities (44 shown, 11 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 47 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e7596fc7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- data_comparison.py
- DataFrame
- arrears_analysis.py
- app.py
- get_db
- audit_engine.py
- consumer_sector_remaining_report
- handover.py
- consumer_report
- _render_page
- match_staff_assignment
- _GroupedPdfWrapper
- fmt
- export_six_month_pitch
- ParagraphStyle
- index
- BytesIO
- route
- NumberedCanvas
- _register_table
- allowed_file
- Agent Instructions
- DataFrame
- load_dataset
- upload-progress.js
- consumer_report_detail_records
- export_new_connection_detail
- _normalize_rate_title
- export_arrear_calculator
- _build_connection_rate_report_from_summary
- handover
- vercel.json
- check_handover.py
- Water Supply Report Application
- Claude Code CLI Prompt: Advanced Bill List Filters and Export
- DataFrame
- Series
- DataFrame
- pdf-lib (CDN library)
- SheetJS (CDN library)
- code:block1 (/graphify . --update)
- code:block2 (/graphify query "how does bill upload work")
- code:bash (# Development server)
- code:text (You are working on an existing running application. This app)
- code:bash (claude)

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 33 edges
2. `get_db()` - 27 edges
3. `init_bill_list_db()` - 23 edges
4. `download_card()` - 23 edges
5. `export_six_month_pitch()` - 19 edges
6. `summarize_dataframe()` - 18 edges
7. `_render_page()` - 17 edges
8. `consumer_report()` - 17 edges
9. `parse_number()` - 16 edges
10. `build_daily_staff_receive_report()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `parse_register()` --calls--> `classify()`  [INFERRED]
  audit_engine.py → data_comparison.py
- `handover()` --calls--> `ajax_error()`  [INFERRED]
  handover.py → app.py
- `handover()` --calls--> `ajax_ok()`  [INFERRED]
  handover.py → app.py
- `handover()` --calls--> `allowed_file()`  [INFERRED]
  handover.py → app.py
- `handover()` --calls--> `is_ajax()`  [INFERRED]
  handover.py → app.py

## Import Cycles
- None detected.

## Communities (55 total, 11 thin omitted)

### Community 0 - "data_comparison.py"
Cohesion: 0.06
Nodes (61): main(), Self-check for the Data Comparison page.  Run:  python check_data_comparison.py, read(), active_figures(), _app(), build_comparison(), change_rows(), classify() (+53 more)

### Community 1 - "DataFrame"
Cohesion: 0.06
Nodes (61): _bill_list_summary_from_rows(), build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report() (+53 more)

### Community 2 - "arrears_analysis.py"
Cohesion: 0.10
Nodes (36): Any, _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+28 more)

### Community 3 - "app.py"
Cohesion: 0.10
Nodes (27): _annualize_connection_rate(), _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _connection_rate_default(), _connection_report_annual_rate(), _get_card_col_map(), _load_new_connection_detail_cache(), _ncd_classification() (+19 more)

### Community 4 - "get_db"
Cohesion: 0.11
Nodes (33): apply_manual_zone_overrides(), backfill_bill_arrears(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data(), export_bill_list_zone() (+25 more)

### Community 5 - "audit_engine.py"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 6 - "consumer_sector_remaining_report"
Cohesion: 0.14
Nodes (26): _build_connection_rate_report(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _classify_connection_status(), _clean_rate_type_name(), consumer_sector_remaining_report(), _is_extra_noor_mohalla_main_road_sector() (+18 more)

### Community 7 - "handover.py"
Cohesion: 0.12
Nodes (20): _app(), _compose(), _conn_key(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path() (+12 more)

### Community 8 - "consumer_report"
Cohesion: 0.15
Nodes (19): ajax_error(), ajax_ok(), arrear_calculator(), bill_list(), _clear_consumer_summary_cache(), consumer_report(), daily_staff_receive(), _ensure_connection_rate_report() (+11 more)

### Community 9 - "_render_page"
Cohesion: 0.20
Nodes (19): apply_filters(), build_sector_summary(), col_key(), detail_columns(), filter_label(), _finalize(), is_commercial(), Count one printable block as a single summary line.      Counts come straight (+11 more)

### Community 10 - "match_staff_assignment"
Cohesion: 0.14
Nodes (18): clean_cell(), _deep_normalize_sector(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), is_large_pdf_text(), _keyword_set(), _levenshtein() (+10 more)

### Community 11 - "_GroupedPdfWrapper"
Cohesion: 0.25
Nodes (7): generate_grouped_advanced_pdf(), generate_single_group_pdf(), _GroupedPdfWrapper, Generate a landscape PDF with one section per group showing detailed bill rows., Helper to write grouped PDF sections with smart pagination and staff zone…, Estimated mm needed for a group: heading + sub-lines + table header + body +…, Insert PageBreak before a group if remaining space is too small.

### Community 12 - "fmt"
Cohesion: 0.18
Nodes (17): bill_income_category_export_rows(), bill_list_export_rows(), build_connection_summary(), commercial_daily_income_export_rows(), download_card(), export_bill_income_category_summary(), export_bill_list(), export_dnc_register() (+9 more)

### Community 13 - "export_six_month_pitch"
Cohesion: 0.18
Nodes (17): _closest_staff_key(), export_bill_list_staff(), export_consumer_sector_remaining(), _export_row_selection(), export_season_sector_pitch(), export_six_month_pitch(), export_unpaid_amount_section(), _filter_rows_by_selection() (+9 more)

### Community 14 - "ParagraphStyle"
Cohesion: 0.27
Nodes (14): _bracket_rich_text(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), daily_staff_receive_export_response(), daily_staff_receive_export_tables(), generate_commercial_monthly_pdf(), generate_daily_staff_receive_pdf(), generate_daily_staff_receive_summary_pdf() (+6 more)

### Community 15 - "index"
Cohesion: 0.16
Nodes (14): build_dashboard_results(), export_consumer_report(), index(), _load_consumer_summary_cache(), _load_dashboard_results(), _load_results_cache(), Build the All Received Bills dashboard once and reuse it for the rendered page…, Load a previously saved consumer summary from disk. Returns (summary, filename,… (+6 more)

### Community 16 - "BytesIO"
Cohesion: 0.20
Nodes (14): _calc_col_widths(), export_advanced_bills(), export_advanced_bills_response(), export_connection_rate_report(), export_unpaid_amount_summary(), generate_advanced_filtered_pdf(), generate_connection_rate_pdf(), generate_unpaid_amount_pdf() (+6 more)

### Community 17 - "route"
Cohesion: 0.16
Nodes (14): download_file(), export_consumer_detail(), export_daily_staff_receive(), export_daily_staff_receive_summary_pdf(), export_sectors_summary(), export_staff_summary(), export_summary_response(), export_zones_summary() (+6 more)

### Community 18 - "NumberedCanvas"
Cohesion: 0.16
Nodes (7): Flowable, NumberedCanvas, _page_furniture(), _PageMark, A zero-height marker that reports the page it lands on.      Placed at the hea, Canvas that stamps "Page X of Y" once the total is known.      ReportLab strea, Page-begin callback.      Runs before the frame lays its flowables down, which

### Community 19 - "_register_table"
Cohesion: 0.15
Nodes (14): _column_extents(), _detail_widths(), _esc(), _index_flowables(), A detail table for the printed register.      Two corrections on top of the sh, Wrap only the long-text columns as Paragraphs.      Matches what ``wrap_pdf_bo, Longest value per column, used to size the columns and decide wrapping., Share the page across columns according to what they actually hold.      Sizin (+6 more)

### Community 20 - "allowed_file"
Cohesion: 0.21
Nodes (12): allowed_file(), _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows() (+4 more)

### Community 21 - "Agent Instructions"
Cohesion: 0.18
Nodes (10): Agent Instructions, Auto-Update on Changes, Commands, Development Guidelines, Graph Status, Graphify - Knowledge Graph, Key Architecture Nodes (from last graphify run), Ponytail - Lazy Senior Dev Mode (+2 more)

### Community 22 - "DataFrame"
Cohesion: 0.25
Nodes (11): build_sections(), detail_rows(), export_handover(), handover_print(), _numeric_amounts(), DataFrame, The one date the register carries.      A finalised record is dated when it wa, Write money columns to Excel as numbers, not "13,040" text, so the     arrears (+3 more)

### Community 23 - "load_dataset"
Cohesion: 0.22
Nodes (11): _handover_dir(), handover_status(), _list_snapshots(), load_dataset(), Whether THIS instance still holds the working register.      Serverless instan, Parse a money cell tolerantly.      Pulls the first number out rather than del, Return (rows, meta). Snapshots read their own frozen copy., _snapshot_dir() (+3 more)

### Community 24 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 25 - "consumer_report_detail_records"
Cohesion: 0.20
Nodes (10): consumer_report_detail_records(), _filter_active_rows(), _is_private_society_summary_row(), _load_consumer_rows_cache(), Return consumer connection records for a specific sector/locality/category with…, Load cached consumer individual connection rows., Return a copy of `summary` with all rows having zero active connections…, Return True for domestic private-society rows shown in their own tab. (+2 more)

### Community 26 - "export_new_connection_detail"
Cohesion: 0.31
Nodes (10): export_new_connection_detail(), _ncd_annual_payload(), _ncd_annual_pdf(), _ncd_detail_pdf(), _ncd_export_rows(), _ncd_general_category_table(), _ncd_general_pdf(), _ncd_pdf_col_widths() (+2 more)

### Community 27 - "_normalize_rate_title"
Cohesion: 0.33
Nodes (7): _add_rate_alias(), _connection_rate_lookup(), _load_rates_csv(), _normalize_rate_title(), Load rate data from the provided rates CSV or bundled rates.json. RATE SOURCE…, Canonical key for rate matching; tolerates case/spacing drift without changing…, Map known legacy consumer rate labels to the active rate title.

### Community 28 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list. Fixed column order: SR,…, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 29 - "_build_connection_rate_report_from_summary"
Cohesion: 0.29
Nodes (7): _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_description(), _connection_rate_report_from_groups(), _norm_report_text(), Fallback for already-cached Consumer Report data without raw upload rows.

### Community 30 - "handover"
Cohesion: 0.50
Nodes (5): _gunzip(), handover(), Read an uploaded CSV/XLSX as text so connection numbers keep leading zeros., Transparently decompress a gzipped upload.      The browser compresses both fi, _read_bytes()

### Community 31 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 32 - "check_handover.py"
Cohesion: 0.67
Nodes (3): main(), Self-check for the Handover Register join, filters, and snapshot lock.  Run:, read()

### Community 33 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

## Knowledge Gaps
- **16 isolated node(s):** `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status`, `When Working on This Project`, `Auto-Update on Changes` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `data_comparison.py` to `audit_engine.py`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `audit_engine.py` to `data_comparison.py`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `_GroupedPdfWrapper` connect `_GroupedPdfWrapper` to `app.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `ParagraphStyle` (e.g. with `_report_pdf()` and `export_handover()`) actually correct?**
  _`ParagraphStyle` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status` to the rest of the system?**
  _170 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06144393241167435 - nodes in this community are weakly interconnected._
- **Should `DataFrame` be split into smaller, more focused modules?**
  _Cohesion score 0.0633879781420765 - nodes in this community are weakly interconnected._