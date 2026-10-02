# Graph Report - water suppy report  (2026-10-02)

## Corpus Check
- 40 files · ~154,122 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: .bat 2, (none) 1, .err 1)

## Summary
- 736 nodes · 1789 edges · 42 communities (36 shown, 6 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `00792f89`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- compute_category_arrears_summary
- data_comparison.py
- check_csv_headers_export.py
- _build_new_connection_detail_report
- get_db
- audit_engine.py
- export_zone_report_response
- DataFrame
- consumer_sector_remaining_report
- app.py
- _render_page
- fmt
- handover.py
- _txt
- check_six_month_connections.py
- route
- make_story
- export_handover
- arrears_analysis.py
- _PageMark
- _build_consumer_sector_summary
- ajax_error
- _build_connection_rate_report
- consumer_report
- parse_number
- _is_faulty_commercial_hussain_colony
- NumberedCanvas
- upload-progress.js
- export_six_month_pitch
- match_staff_assignment
- Agent Instructions
- export_arrear_calculator
- arrears_analysis_print
- NumberedCanvas
- vercel.json
- Claude Code CLI Prompt: Advanced Bill List Filters and Export
- _filter_rows_by_selection
- _parse_consumer_csv
- Water Supply Report Application
- pdf-lib (CDN library)
- SheetJS (CDN library)

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 39 edges
2. `get_db()` - 28 edges
3. `init_bill_list_db()` - 24 edges
4. `parse_number()` - 21 edges
5. `download_card()` - 21 edges
6. `wrap_pdf_body_cells()` - 20 edges
7. `export_six_month_pitch()` - 20 edges
8. `summarize_dataframe()` - 18 edges
9. `arrears_analysis()` - 18 edges
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

## Communities (42 total, 6 thin omitted)

### Community 0 - "compute_category_arrears_summary"
Cohesion: 0.16
Nodes (22): Any, build_arrears_pdf(), compute_arrears_analysis(), compute_category_arrears_summary(), _detect_column(), format_pkr(), get_one_page_summary_rows(), inspect_dataframe_columns() (+14 more)

### Community 1 - "data_comparison.py"
Cohesion: 0.08
Nodes (46): main(), Self-check for the Data Comparison page. Run: python check_data_comparison.py…, read(), active_figures(), _app(), build_comparison(), change_rows(), clear_result() (+38 more)

### Community 2 - "check_csv_headers_export.py"
Cohesion: 0.09
Nodes (20): _calc_col_widths(), export_advanced_bills(), export_advanced_bills_response(), generate_advanced_filtered_pdf(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), generate_zip_of_group_pdfs(), group_bills() (+12 more)

### Community 3 - "_build_new_connection_detail_report"
Cohesion: 0.07
Nodes (40): allowed_file(), _build_dnc_register_report(), _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification() (+32 more)

### Community 4 - "get_db"
Cohesion: 0.09
Nodes (38): bill_list(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_unpaid_amount_summary(), clean_identifier(), clear_bill_list_data(), fast_bill_no_key() (+30 more)

### Community 5 - "audit_engine.py"
Cohesion: 0.08
Nodes (34): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+26 more)

### Community 6 - "export_zone_report_response"
Cohesion: 0.50
Nodes (5): export_bill_list_zone(), export_zone_report_response(), transform_row(), without_zone(), generate_zone_grouped_pdf()

### Community 7 - "DataFrame"
Cohesion: 0.15
Nodes (31): build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report(), build_income_category_summary(), build_monthly_rows() (+23 more)

### Community 8 - "consumer_sector_remaining_report"
Cohesion: 0.17
Nodes (16): build_consumer_sector_remaining_report(), _canonical_consumer_sector_locality(), consumer_sector_remaining_report(), _is_extra_noor_mohalla_main_road_sector(), _is_extra_zain_city_13g_sector(), _is_faulty_empty_consumer_sector(), _normalize_consumer_col(), _normalize_sector_key() (+8 more)

### Community 9 - "app.py"
Cohesion: 0.08
Nodes (32): apply_manual_zone_overrides(), bill_income_category_export_rows(), build_bill_key(), build_connection_summary(), _card_rows_to_df(), _dedupe_value(), download_card(), drop_duplicate_bills() (+24 more)

### Community 10 - "_render_page"
Cohesion: 0.16
Nodes (29): main(), apply_filters(), build_sections(), add(), build_sector_summary(), col_key(), detail_columns(), detail_rows() (+21 more)

### Community 11 - "fmt"
Cohesion: 0.10
Nodes (37): bill_list_export_rows(), _bracket_rich_text(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), commercial_daily_income_export_rows(), append_day_total(), daily_staff_receive_export_response(), daily_staff_receive_export_tables() (+29 more)

### Community 12 - "handover.py"
Cohesion: 0.11
Nodes (27): _app(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path(), _gunzip(), handover() (+19 more)

### Community 13 - "_txt"
Cohesion: 0.12
Nodes (24): classify(), Reduce an export to the fields this page compares. A connection counts as…, build_handover_dataset(), _canonical_labels(), canonicalise_groups(), _compose(), _conn_key(), drop_excluded_sectors() (+16 more)

### Community 14 - "check_six_month_connections.py"
Cohesion: 0.09
Nodes (16): Self-check for the Consumer Report category summary exports. Run: python…, Self-check for the Handover Register join, filters, and snapshot lock. Run:…, read(), Check both six-month report views against a supplied Bills CSV. Run:…, contextlib, csv, io, json (+8 more)

### Community 15 - "route"
Cohesion: 0.14
Nodes (16): download_file(), export_consumer_detail(), export_daily_staff_receive(), export_daily_staff_receive_summary_pdf(), export_sectors_summary(), export_staff_summary(), export_summary_response(), export_zones_summary() (+8 more)

### Community 16 - "make_story"
Cohesion: 0.15
Nodes (15): _column_extents(), _detail_widths(), _esc(), make_story(), The first page: a domestic report and a commercial report, side by side in…, A detail table for the printed register. Two corrections on top of the shared…, Wrap only the long-text columns as Paragraphs. Matches what…, Longest value per column, used to size the columns and decide wrapping. (+7 more)

### Community 17 - "export_handover"
Cohesion: 0.17
Nodes (13): export_handover(), handover_print(), handover_snapshot(), _index_flowables(), _numeric_amounts(), route, The one date the register carries. A finalised record is dated when it was…, Write money columns to Excel as numbers, not "13,040" text, so the arrears… (+5 more)

### Community 18 - "arrears_analysis.py"
Cohesion: 0.16
Nodes (20): _app(), arrears_analysis(), _arrears_dir(), get_detail_columns(), _handover_working_csv(), load_working_dataset(), Arrears Analysis Blueprint ========================== Independent module…, Load cached working dataset or fallback to handover dataset if available. (+12 more)

### Community 19 - "_PageMark"
Cohesion: 0.29
Nodes (5): Flowable, _page_furniture(), _PageMark, A zero-height marker that reports the page it lands on. Placed at the head of a…, Page-begin callback. Runs before the frame lays its flowables down, which is…

### Community 20 - "_build_consumer_sector_summary"
Cohesion: 0.18
Nodes (13): _add_rate_alias(), _build_consumer_sector_summary(), _build_rate_lookup(), _domestic_annual_rate_override(), _clean_rate_type_name(), _connection_rate_lookup(), _load_rates_csv(), _normalize_rate_title() (+5 more)

### Community 21 - "ajax_error"
Cohesion: 0.21
Nodes (15): ajax_error(), ajax_ok(), arrear_calculator(), build_dashboard_results(), daily_staff_receive(), index(), is_ajax(), _load_dashboard_results() (+7 more)

### Community 22 - "_build_connection_rate_report"
Cohesion: 0.25
Nodes (11): _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description(), _connection_rate_report_from_groups() (+3 more)

### Community 23 - "consumer_report"
Cohesion: 0.17
Nodes (12): _clear_consumer_summary_cache(), consumer_report(), _ensure_connection_rate_report(), _filter_active_rows(), _keep(), Return a copy of `summary` with all rows having zero active connections…, Split a summary dict into (normal, commercial, private_society). COMMERCIAL…, Persist the consumer summary to disk so it survives serverless cold starts.… (+4 more)

### Community 24 - "parse_number"
Cohesion: 0.11
Nodes (19): backfill_bill_arrears(), _bill_list_summary_from_rows(), make_total_row(), _connection_rate_rows_from_payload(), export_connection_rate_report(), pn(), generate_connection_rate_pdf(), is_large_pdf_text() (+11 more)

### Community 25 - "_is_faulty_commercial_hussain_colony"
Cohesion: 0.15
Nodes (13): consumer_report_detail_records(), export_consumer_report(), _is_faulty_commercial_hussain_colony(), _is_private_society_summary_row(), _load_consumer_rows_cache(), _load_consumer_summary_cache(), Skip dummy/faulted Commercial Hussain Colony records that do not represent real…, Shared sorting for the Consumer Sector Report (preview, PDF, CSV, Excel).… (+5 more)

### Community 27 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 28 - "export_six_month_pitch"
Cohesion: 0.15
Nodes (18): _closest_staff_key(), export_bill_list_staff(), parse_num(), export_six_month_pitch(), wrap_left(), export_table_response(), fmt_staff_name(), fmt_staff_name_html() (+10 more)

### Community 29 - "match_staff_assignment"
Cohesion: 0.27
Nodes (10): clean_cell(), _deep_normalize_sector(), _keyword_set(), load_alias_rules(), match_by_alias(), match_key(), match_staff_assignment(), Aggressively normalize a sector/locality name for robust matching. (+2 more)

### Community 30 - "Agent Instructions"
Cohesion: 0.18
Nodes (10): Agent Instructions, Auto-Update on Changes, Commands, Development Guidelines, Graph Status, Graphify - Knowledge Graph, Key Architecture Nodes (from last graphify run), Ponytail - Lazy Senior Dev Mode (+2 more)

### Community 31 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list. Fixed column order: SR,…, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 32 - "arrears_analysis_print"
Cohesion: 0.19
Nodes (14): arrears_analysis_one_page_summary(), arrears_analysis_print(), classify_status(), export_arrears_analysis(), is_zero_summary(), one_page_options(), route, Printable sheet styled for A4 landscape. (+6 more)

### Community 34 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 36 - "_filter_rows_by_selection"
Cohesion: 0.28
Nodes (9): _export_row_selection(), export_season_sector_pitch(), wrap_left(), export_unpaid_amount_section(), _filter_rows_by_selection(), Read bill-list row checkbox selection from export query params., Keep only bill-list rows selected by the page checkboxes before exporting., _selection_has_filter() (+1 more)

### Community 37 - "_parse_consumer_csv"
Cohesion: 0.40
Nodes (4): _classify_connection_status(), _parse_consumer_csv(), Read uploaded CSV/XLSX and return (rows, errors). Uses flexible column matching…, Classify both 'Status' column values and 'Consumer Status' into…

### Community 38 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

## Knowledge Gaps
- **11 isolated node(s):** `$schema`, `maxDuration`, `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 232 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_GroupedPdfWrapper` connect `check_csv_headers_export.py` to `app.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Why does `NumberedCanvas` connect `NumberedCanvas` to `arrears_analysis.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `NumberedCanvas` connect `NumberedCanvas` to `handover.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **What connects `$schema`, `maxDuration`, `Ponytail - Lazy Senior Dev Mode` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07712765957446809 - nodes in this community are weakly interconnected._
- **Should `check_csv_headers_export.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08522727272727272 - nodes in this community are weakly interconnected._
- **Should `_build_new_connection_detail_report` be split into smaller, more focused modules?**
  _Cohesion score 0.06923076923076923 - nodes in this community are weakly interconnected._