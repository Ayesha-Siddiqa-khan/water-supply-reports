# Graph Report - water suppy report  (2026-10-22)

## Corpus Check
- 43 files · ~164,820 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: .bat 2, (none) 1, .csv 1)

## Summary
- 778 nodes · 1910 edges · 47 communities (40 shown, 7 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0b0cfc7e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- compute_category_arrears_summary
- data_comparison.py
- export_advanced_bills
- _build_new_connection_detail_report
- get_db
- audit_engine.py
- route
- DataFrame
- _build_consumer_sector_summary
- app.py
- _render_page
- wrap_pdf_body_cells
- handover.py
- monthly_account_branch.py
- check_new_connection_detail.py
- export_bill_list
- _txt
- make_story
- arrears_analysis.py
- _PageMark
- bill_list
- handover
- _build_connection_rate_report
- consumer_report
- parse_number
- export_consumer_report
- NumberedCanvas
- upload-progress.js
- export_six_month_pitch
- fmt
- Agent Instructions
- export_arrear_calculator
- DataFrame
- NumberedCanvas
- vercel.json
- Claude Code CLI Prompt: Advanced Bill List Filters and Export
- check_csv_headers_export.py
- _build_dnc_register_report
- Water Supply Report Application
- _GroupedPdfWrapper
- arrears_analysis_print
- _bracket_rich_text
- pandas
- export_zone_report_response
- pdf-lib (CDN library)
- SheetJS (CDN library)

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 43 edges
2. `get_db()` - 28 edges
3. `init_bill_list_db()` - 24 edges
4. `parse_number()` - 21 edges
5. `wrap_pdf_body_cells()` - 21 edges
6. `export_six_month_pitch()` - 21 edges
7. `download_card()` - 21 edges
8. `summarize_dataframe()` - 18 edges
9. `get_bill_list_context()` - 18 edges
10. `_build_new_connection_detail_report()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `arrears_analysis()` --indirect_call--> `ajax_ok()`  [INFERRED]
  arrears_analysis.py → app.py
- `arrears_analysis()` --indirect_call--> `ajax_error()`  [INFERRED]
  arrears_analysis.py → app.py
- `make_story()` --calls--> `_make_pdf_table()`  [INFERRED]
  handover.py → app.py
- `test_pdf_sector_locality_are_heading_only()` --calls--> `generate_advanced_filtered_pdf()`  [EXTRACTED]
  check_csv_headers_export.py → app.py
- `main()` --calls--> `get_bill_list_context()`  [EXTRACTED]
  check_sector_category_report.py → app.py

## Import Cycles
- None detected.

## Communities (47 total, 7 thin omitted)

### Community 0 - "compute_category_arrears_summary"
Cohesion: 0.17
Nodes (21): Any, build_arrears_pdf(), compute_arrears_analysis(), compute_category_arrears_summary(), _detect_column(), format_pkr(), get_one_page_summary_rows(), inspect_dataframe_columns() (+13 more)

### Community 1 - "data_comparison.py"
Cohesion: 0.08
Nodes (47): main(), read(), active_figures(), _app(), build_comparison(), change_rows(), classify(), clear_result() (+39 more)

### Community 2 - "export_advanced_bills"
Cohesion: 0.25
Nodes (9): export_advanced_bills(), export_advanced_bills_response(), export_bill_list_connections(), generate_advanced_filtered_pdf(), generate_grouped_advanced_pdf(), group_bills(), Group bills by sector/zone/staff. Returns: - sector/zone: list of (group_label,…, Generate a landscape PDF with one section per group showing detailed bill rows. (+1 more)

### Community 3 - "_build_new_connection_detail_report"
Cohesion: 0.18
Nodes (18): _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _load_new_connection_detail_cache(), _ncd_classification(), _ncd_decimal(), _ncd_int(), _ncd_load_file(), _ncd_norm() (+10 more)

### Community 4 - "get_db"
Cohesion: 0.14
Nodes (26): apply_manual_zone_overrides(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data(), get_bill_income_category_summary(), get_bill_list_context() (+18 more)

### Community 5 - "audit_engine.py"
Cohesion: 0.09
Nodes (33): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+25 more)

### Community 6 - "route"
Cohesion: 0.16
Nodes (17): bill_income_category_export_rows(), download_file(), export_bill_income_category_summary(), export_bill_list_sector_category(), export_daily_staff_receive(), export_daily_staff_receive_summary_pdf(), export_dnc_register(), export_sectors_summary() (+9 more)

### Community 7 - "DataFrame"
Cohesion: 0.06
Nodes (60): build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report(), build_income_category_summary() (+52 more)

### Community 8 - "_build_consumer_sector_summary"
Cohesion: 0.13
Nodes (21): build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _domestic_annual_rate_override(), _canonical_consumer_sector_locality(), _clean_rate_type_name(), consumer_sector_remaining_report(), _is_extra_noor_mohalla_main_road_sector(), _is_extra_zain_city_13g_sector() (+13 more)

### Community 9 - "app.py"
Cohesion: 0.07
Nodes (36): _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), export_consumer_detail(), export_new_connection_detail(), file_column_matcher(), file_merger(), fiscal_label_to_calendar_full_label(), fiscal_label_to_calendar_label() (+28 more)

### Community 10 - "_render_page"
Cohesion: 0.24
Nodes (18): main(), apply_filters(), build_sector_summary(), filter_label(), _finalize(), _list_snapshots(), load_dataset(), Parse a money cell tolerantly. Pulls the first number out rather than deleting… (+10 more)

### Community 11 - "wrap_pdf_body_cells"
Cohesion: 0.17
Nodes (16): export_consumer_sector_remaining(), wrap_left(), wrap_left(), export_unpaid_amount_summary(), generate_commercial_pdf(), generate_staff_report_pdf(), numeric(), total_row() (+8 more)

### Community 12 - "handover.py"
Cohesion: 0.16
Nodes (15): _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path(), draw(), Handover Register — independent feature module. Builds a printable employee…, Signature strip drawn as page furniture, for 'every page'. (+7 more)

### Community 13 - "monthly_account_branch.py"
Cohesion: 0.14
Nodes (24): _extract_selection_args(), fmt_amt(), generate_monthly_account_branch_pdf(), is_default_water_row(), load_cached_or_default_data(), monthly_account_branch(), monthly_account_branch_export_csv(), monthly_account_branch_export_excel() (+16 more)

### Community 14 - "check_new_connection_detail.py"
Cohesion: 0.10
Nodes (21): Self-check for the Consumer Report category summary exports. Run: python…, Self-check for the Handover Register join, filters, and snapshot lock. Run:…, read(), Run: python check_new_connection_detail.py [optional-payment-list.csv], main(), Self-check for the category-wise Sector Wise Report and the paid/unpaid…, Check both six-month report views against a supplied Bills CSV. Run:…, contextlib (+13 more)

### Community 15 - "export_bill_list"
Cohesion: 0.18
Nodes (14): bill_list_export_rows(), bill_list_sector_category_export_rows(), amounts(), export_bill_list(), _export_row_selection(), export_season_sector_pitch(), wrap_left(), export_unpaid_amount_section() (+6 more)

### Community 16 - "_txt"
Cohesion: 0.09
Nodes (27): Self-check for the Data Comparison page. Run: python check_data_comparison.py…, build_handover_dataset(), _canonical_labels(), canonicalise_groups(), col_key(), _compose(), _conn_key(), detail_columns() (+19 more)

### Community 17 - "make_story"
Cohesion: 0.13
Nodes (17): _column_extents(), _detail_widths(), _esc(), make_story(), _index_flowables(), The first page: a domestic report and a commercial report, side by side in…, A detail table for the printed register. Two corrections on top of the shared…, Wrap only the long-text columns as Paragraphs. Matches what… (+9 more)

### Community 18 - "arrears_analysis.py"
Cohesion: 0.19
Nodes (18): _app(), arrears_analysis(), _arrears_dir(), get_detail_columns(), _handover_working_csv(), load_working_dataset(), Arrears Analysis Blueprint ========================== Independent module…, Load cached working dataset or fallback to handover dataset if available. (+10 more)

### Community 19 - "_PageMark"
Cohesion: 0.29
Nodes (5): Flowable, _page_furniture(), _PageMark, A zero-height marker that reports the page it lands on. Placed at the head of a…, Page-begin callback. Runs before the frame lays its flowables down, which is…

### Community 20 - "bill_list"
Cohesion: 0.15
Nodes (20): ajax_error(), ajax_ok(), arrear_calculator(), bill_list(), build_dashboard_results(), daily_staff_receive(), get_assignment_conflicts(), index() (+12 more)

### Community 21 - "handover"
Cohesion: 0.19
Nodes (14): _app(), _gunzip(), handover(), _handover_dir(), handover_snapshot(), handover_status(), route, Read an uploaded CSV/XLSX as text so connection numbers keep leading zeros. (+6 more)

### Community 22 - "_build_connection_rate_report"
Cohesion: 0.14
Nodes (21): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _build_rate_lookup(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default() (+13 more)

### Community 23 - "consumer_report"
Cohesion: 0.12
Nodes (16): _classify_connection_status(), _clear_consumer_summary_cache(), consumer_report(), _ensure_connection_rate_report(), _filter_active_rows(), _keep(), _parse_consumer_csv(), Classify both 'Status' column values and 'Consumer Status' into… (+8 more)

### Community 24 - "parse_number"
Cohesion: 0.12
Nodes (17): backfill_bill_arrears(), _bill_list_summary_from_rows(), make_total_row(), _connection_rate_rows_from_payload(), export_connection_rate_report(), pn(), is_large_pdf_text(), merge_sector_list_rows() (+9 more)

### Community 25 - "export_consumer_report"
Cohesion: 0.17
Nodes (11): consumer_report_detail_records(), export_consumer_report(), _is_private_society_summary_row(), _load_consumer_rows_cache(), _load_consumer_summary_cache(), Shared sorting for the Consumer Sector Report (preview, PDF, CSV, Excel).…, Return True for domestic private-society rows shown in their own tab., Return consumer connection records for a specific sector/locality/category with… (+3 more)

### Community 27 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 28 - "export_six_month_pitch"
Cohesion: 0.22
Nodes (11): _closest_staff_key(), export_bill_list_staff(), parse_num(), export_daily_staff_receive_bills_pdf(), export_six_month_pitch(), category_values(), export_table_response(), fmt_staff_name() (+3 more)

### Community 29 - "fmt"
Cohesion: 0.19
Nodes (19): build_connection_summary(), _card_rows_to_df(), commercial_daily_income_export_rows(), append_day_total(), daily_staff_receive_export_response(), daily_staff_receive_export_tables(), download_card(), fmt() (+11 more)

### Community 30 - "Agent Instructions"
Cohesion: 0.18
Nodes (10): Agent Instructions, Auto-Update on Changes, Commands, Development Guidelines, Graph Status, Graphify - Knowledge Graph, Key Architecture Nodes (from last graphify run), Ponytail - Lazy Senior Dev Mode (+2 more)

### Community 31 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list. Fixed column order: SR,…, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 32 - "DataFrame"
Cohesion: 0.18
Nodes (16): build_sections(), add(), detail_rows(), export_handover(), handover_print(), is_commercial(), _numeric_amounts(), DataFrame (+8 more)

### Community 34 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 36 - "check_csv_headers_export.py"
Cohesion: 0.14
Nodes (9): clean_identifier(), fast_upload_number(), format_mobile(), get_filtered_bills(), Fast numeric parser for Bill Reports upload amount columns., Clean and preserve exact identifier strings (connection_no, bill_no, ref_no,…, Runnable self-check for the Advanced Bill Checking CSV headers export. Run:…, test_get_filtered_bills_headers() (+1 more)

### Community 37 - "_build_dnc_register_report"
Cohesion: 0.21
Nodes (12): allowed_file(), _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows() (+4 more)

### Community 38 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

### Community 39 - "_GroupedPdfWrapper"
Cohesion: 0.15
Nodes (10): _calc_col_widths(), generate_single_group_pdf(), generate_zip_of_group_pdfs(), _GroupedPdfWrapper, Return sort key for zone ordering: A=1, B=2, C=3, Commercial=4, unknown=99., Helper to write grouped PDF sections where each staff/group starts on a fresh…, Calculate column widths with compact space for fixed/numeric fields and…, sanitize_filename() (+2 more)

### Community 41 - "arrears_analysis_print"
Cohesion: 0.21
Nodes (12): arrears_analysis_one_page_summary(), arrears_analysis_print(), classify_status(), export_arrears_analysis(), is_zero_summary(), one_page_options(), route, Printable sheet styled for A4 landscape. (+4 more)

### Community 42 - "_bracket_rich_text"
Cohesion: 0.67
Nodes (3): _bracket_rich_text(), Split text into normal and bracket segments for rich text rendering. Returns a…, ParagraphStyle

### Community 44 - "export_zone_report_response"
Cohesion: 0.50
Nodes (5): export_bill_list_zone(), export_zone_report_response(), transform_row(), without_zone(), generate_zone_grouped_pdf()

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `maxDuration`, `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 244 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_GroupedPdfWrapper` connect `_GroupedPdfWrapper` to `app.py`, `export_advanced_bills`, `wrap_pdf_body_cells`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `fmt()` connect `fmt` to `export_advanced_bills`, `get_db`, `_build_dnc_register_report`, `route`, `_GroupedPdfWrapper`, `DataFrame`, `app.py`, `wrap_pdf_body_cells`, `export_bill_list`, `parse_number`, `export_six_month_pitch`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `NumberedCanvas` connect `NumberedCanvas` to `arrears_analysis.py`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **What connects `$schema`, `maxDuration`, `Ponytail - Lazy Senior Dev Mode` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08067375886524823 - nodes in this community are weakly interconnected._
- **Should `get_db` be split into smaller, more focused modules?**
  _Cohesion score 0.13756613756613756 - nodes in this community are weakly interconnected._
- **Should `audit_engine.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08571428571428572 - nodes in this community are weakly interconnected._