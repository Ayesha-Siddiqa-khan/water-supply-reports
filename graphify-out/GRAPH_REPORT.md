# Graph Report - water suppy report  (2026-10-02)

## Corpus Check
- 39 files · ~153,157 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: .bat 2, (none) 1, .err 1)

## Summary
- 730 nodes · 1769 edges · 42 communities (35 shown, 7 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 42 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `93c8633d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- arrears_analysis.py
- data_comparison.py
- check_csv_headers_export.py
- app.py
- get_db
- audit_engine.py
- fmt
- DataFrame
- _build_consumer_sector_summary
- fmt_staff_name
- _render_page
- wrap_pdf_body_cells
- handover.py
- _txt
- download_card
- route
- main
- load_dataset
- build_comparison
- _PageMark
- _build_dnc_register_report
- ajax_error
- _build_connection_rate_report
- consumer_report
- parse_export_cols
- export_consumer_report
- NumberedCanvas
- upload-progress.js
- export_new_connection_detail
- classify
- Agent Instructions
- export_arrear_calculator
- _summary_page
- NumberedCanvas
- vercel.json
- Claude Code CLI Prompt: Advanced Bill List Filters and Export
- parse_number
- Water Supply Report Application
- io
- pdf-lib (CDN library)
- SheetJS (CDN library)

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 39 edges
2. `get_db()` - 27 edges
3. `init_bill_list_db()` - 23 edges
4. `parse_number()` - 21 edges
5. `download_card()` - 21 edges
6. `wrap_pdf_body_cells()` - 20 edges
7. `summarize_dataframe()` - 18 edges
8. `arrears_analysis()` - 18 edges
9. `export_six_month_pitch()` - 17 edges
10. `_build_consumer_sector_summary()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `arrears_analysis()` --indirect_call--> `ajax_ok()`  [INFERRED]
  arrears_analysis.py → app.py
- `arrears_analysis()` --indirect_call--> `ajax_error()`  [INFERRED]
  arrears_analysis.py → app.py
- `make_story()` --calls--> `_make_pdf_table()`  [INFERRED]
  handover.py → app.py
- `test_get_filtered_bills_headers()` --calls--> `get_filtered_bills()`  [EXTRACTED]
  check_csv_headers_export.py → app.py
- `test_pdf_sector_locality_are_heading_only()` --calls--> `generate_advanced_filtered_pdf()`  [EXTRACTED]
  check_csv_headers_export.py → app.py

## Import Cycles
- None detected.

## Communities (42 total, 7 thin omitted)

### Community 0 - "arrears_analysis.py"
Cohesion: 0.07
Nodes (61): Any, _app(), arrears_analysis(), arrears_analysis_one_page_summary(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status() (+53 more)

### Community 1 - "data_comparison.py"
Cohesion: 0.15
Nodes (23): _app(), change_rows(), clear_result(), _column(), data_comparison(), _dir(), export_data_comparison(), _handle_upload() (+15 more)

### Community 2 - "check_csv_headers_export.py"
Cohesion: 0.07
Nodes (24): _calc_col_widths(), clean_identifier(), export_advanced_bills(), export_advanced_bills_response(), fast_upload_number(), format_mobile(), generate_advanced_filtered_pdf(), generate_single_group_pdf() (+16 more)

### Community 3 - "app.py"
Cohesion: 0.10
Nodes (31): bill_list(), build_bill_key(), _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _dedupe_value(), get_assignment_conflicts(), _load_new_connection_detail_cache(), _ncd_classification() (+23 more)

### Community 4 - "get_db"
Cohesion: 0.14
Nodes (27): apply_manual_zone_overrides(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data(), export_six_month_pitch(), get_bill_income_category_summary(), get_bill_list_context() (+19 more)

### Community 5 - "audit_engine.py"
Cohesion: 0.08
Nodes (35): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+27 more)

### Community 6 - "fmt"
Cohesion: 0.18
Nodes (16): bill_list_export_rows(), bill_list_zone_export_rows(), make_total_row(), commercial_daily_income_export_rows(), append_day_total(), export_bill_list(), _export_row_selection(), export_season_sector_pitch() (+8 more)

### Community 7 - "DataFrame"
Cohesion: 0.08
Nodes (52): build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report(), build_income_category_summary(), build_monthly_rows() (+44 more)

### Community 8 - "_build_consumer_sector_summary"
Cohesion: 0.10
Nodes (27): build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _domestic_annual_rate_override(), _canonical_consumer_sector_locality(), _classify_connection_status(), _clean_rate_type_name(), consumer_sector_remaining_report(), _is_extra_noor_mohalla_main_road_sector() (+19 more)

### Community 9 - "fmt_staff_name"
Cohesion: 0.20
Nodes (12): _closest_staff_key(), fmt_staff_name(), fmt_staff_name_html(), generate_grouped_advanced_pdf(), get_auto_staff_override(), get_staff_by_connection_rule(), _normalize_sector_locality(), _normalize_staff_name() (+4 more)

### Community 10 - "_render_page"
Cohesion: 0.19
Nodes (22): apply_filters(), add(), build_sector_summary(), col_key(), detail_columns(), detail_rows(), filter_label(), _finalize() (+14 more)

### Community 11 - "wrap_pdf_body_cells"
Cohesion: 0.11
Nodes (25): _bracket_rich_text(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), export_consumer_sector_remaining(), wrap_left(), wrap_left(), generate_commercial_monthly_pdf(), generate_commercial_pdf() (+17 more)

### Community 12 - "handover.py"
Cohesion: 0.14
Nodes (16): _column_extents(), _detail_widths(), _draw_ring_text(), _draw_star(), _draw_watermark(), _emblem_path(), Handover Register — independent feature module. Builds a printable employee…, Longest value per column, used to size the columns and decide wrapping. (+8 more)

### Community 13 - "_txt"
Cohesion: 0.11
Nodes (21): build_handover_dataset(), _canonical_labels(), canonicalise_groups(), _compose(), _conn_key(), drop_excluded_sectors(), _key_frame(), series() (+13 more)

### Community 14 - "download_card"
Cohesion: 0.25
Nodes (9): build_connection_summary(), _card_rows_to_df(), download_card(), fiscal_label_to_calendar_full_label(), fiscal_label_to_calendar_label(), _get_card_col_map(), Compute connection type collection summary from results dict., remove_pdf_column() (+1 more)

### Community 15 - "route"
Cohesion: 0.10
Nodes (25): bill_income_category_export_rows(), download_file(), export_bill_income_category_summary(), export_bill_list_zone(), export_consumer_detail(), export_dnc_register(), export_sectors_summary(), export_staff_summary() (+17 more)

### Community 16 - "main"
Cohesion: 0.14
Nodes (21): main(), _app(), build_sections(), _esc(), export_handover(), make_story(), handover_print(), _index_flowables() (+13 more)

### Community 17 - "load_dataset"
Cohesion: 0.17
Nodes (16): _gunzip(), handover(), _handover_dir(), handover_snapshot(), handover_status(), _list_snapshots(), load_dataset(), route (+8 more)

### Community 18 - "build_comparison"
Cohesion: 0.19
Nodes (16): active_figures(), build_comparison(), comparable(), first_positions(), health(), _identity(), DataFrame, What to print for one record's status. Where the two columns disagree both are… (+8 more)

### Community 19 - "_PageMark"
Cohesion: 0.20
Nodes (8): Flowable, _draw_signature_band(), _page_furniture(), draw(), _PageMark, Signature strip drawn as page furniture, for 'every page'., A zero-height marker that reports the page it lands on. Placed at the head of a…, Page-begin callback. Runs before the frame lays its flowables down, which is…

### Community 20 - "_build_dnc_register_report"
Cohesion: 0.21
Nodes (12): allowed_file(), _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows() (+4 more)

### Community 21 - "ajax_error"
Cohesion: 0.21
Nodes (15): ajax_error(), ajax_ok(), arrear_calculator(), build_dashboard_results(), daily_staff_receive(), index(), is_ajax(), _load_dashboard_results() (+7 more)

### Community 22 - "_build_connection_rate_report"
Cohesion: 0.15
Nodes (20): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _build_rate_lookup(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default() (+12 more)

### Community 23 - "consumer_report"
Cohesion: 0.18
Nodes (11): _clear_consumer_summary_cache(), consumer_report(), _filter_active_rows(), _keep(), Return a copy of `summary` with all rows having zero active connections…, Split a summary dict into (normal, commercial, private_society). COMMERCIAL…, Persist the consumer summary to disk so it survives serverless cold starts.…, Persist consumer individual connection rows (compressed gzip) for drilldown. (+3 more)

### Community 24 - "parse_export_cols"
Cohesion: 0.16
Nodes (14): daily_staff_receive_export_response(), daily_staff_receive_export_tables(), export_daily_staff_receive(), export_daily_staff_receive_summary_pdf(), export_unpaid_amount_section(), export_unpaid_amount_summary(), generate_daily_staff_receive_summary_pdf(), generate_unpaid_amount_pdf() (+6 more)

### Community 25 - "export_consumer_report"
Cohesion: 0.17
Nodes (11): consumer_report_detail_records(), export_consumer_report(), _is_private_society_summary_row(), _load_consumer_rows_cache(), _load_consumer_summary_cache(), Shared sorting for the Consumer Sector Report (preview, PDF, CSV, Excel).…, Return True for domestic private-society rows shown in their own tab., Return consumer connection records for a specific sector/locality/category with… (+3 more)

### Community 27 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 28 - "export_new_connection_detail"
Cohesion: 0.31
Nodes (10): export_new_connection_detail(), _ncd_annual_payload(), _ncd_annual_pdf(), _ncd_detail_pdf(), _ncd_export_rows(), _ncd_general_category_table(), _ncd_general_pdf(), _ncd_pdf_col_widths() (+2 more)

### Community 29 - "classify"
Cohesion: 0.17
Nodes (14): main(), Self-check for the Data Comparison page. Run: python check_data_comparison.py…, read(), classify(), _consumer_active(), _key(), Connection Number reduced to a comparable form. Leading zeros are KEPT. The…, True / False from the Consumer Status column, None when it says nothing. (+6 more)

### Community 30 - "Agent Instructions"
Cohesion: 0.18
Nodes (10): Agent Instructions, Auto-Update on Changes, Commands, Development Guidelines, Graph Status, Graphify - Knowledge Graph, Key Architecture Nodes (from last graphify run), Ponytail - Lazy Senior Dev Mode (+2 more)

### Community 31 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list. Fixed column order: SR,…, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 34 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 36 - "parse_number"
Cohesion: 0.12
Nodes (17): backfill_bill_arrears(), _bill_list_summary_from_rows(), _connection_rate_rows_from_payload(), export_bill_list_staff(), parse_num(), export_connection_rate_report(), pn(), generate_connection_rate_pdf() (+9 more)

### Community 38 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

### Community 44 - "io"
Cohesion: 0.12
Nodes (7): Self-check for the Handover Register join, filters, and snapshot lock. Run:…, read(), io, json, pandas, shutil, sqlite3

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `maxDuration`, `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 228 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_GroupedPdfWrapper` connect `check_csv_headers_export.py` to `wrap_pdf_body_cells`, `fmt_staff_name`, `app.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `NumberedCanvas` connect `NumberedCanvas` to `arrears_analysis.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `NumberedCanvas` connect `NumberedCanvas` to `handover.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **What connects `$schema`, `maxDuration`, `Ponytail - Lazy Senior Dev Mode` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `arrears_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07146087743102668 - nodes in this community are weakly interconnected._
- **Should `check_csv_headers_export.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07057057057057058 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10317460317460317 - nodes in this community are weakly interconnected._