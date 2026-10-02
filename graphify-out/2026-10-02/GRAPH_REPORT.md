# Graph Report - water suppy report  (2026-10-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 710 nodes · 1671 edges · 61 communities (38 shown, 23 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 52 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d7965fa5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- arrears_analysis.py
- data_comparison.py
- check_csv_headers_export.py
- app.py
- get_db
- audit_engine.py
- parse_number
- DataFrame
- _build_consumer_sector_summary
- build_daily_staff_receive_report
- _render_page
- wrap_pdf_body_cells
- handover.py
- build_handover_dataset
- download_card
- route
- main
- handover
- fmt
- export_handover
- allowed_file
- ajax_error
- _build_connection_rate_report
- consumer_report
- generate_daily_staff_receive_pdf
- export_consumer_report
- NumberedCanvas
- upload-progress.js
- export_new_connection_detail
- _normalize_rate_title
- _normalize_consumer_col
- export_arrear_calculator
- export_zone_report_response
- NumberedCanvas
- vercel.json
- drop_duplicate_bills
- merge_sector_list_rows
- parse_received_dates
- Water Supply Report Application
- check_consumer_connections_summary.py
- Series
- DataFrame
- route
- pdf-lib (CDN library)
- SheetJS (CDN library)
- route
- code:block1 (/graphify . --update)
- code:block2 (/graphify query "how does bill upload work")
- code:bash (# Development server)
- code:text (You are working on an existing running application. This app)
- code:bash (claude)

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 39 edges
2. `get_db()` - 27 edges
3. `init_bill_list_db()` - 23 edges
4. `download_card()` - 21 edges
5. `parse_number()` - 21 edges
6. `wrap_pdf_body_cells()` - 20 edges
7. `summarize_dataframe()` - 18 edges
8. `arrears_analysis()` - 17 edges
9. `consumer_report()` - 17 edges
10. `export_six_month_pitch()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `arrears_analysis()` --indirect_call--> `ajax_error()`  [INFERRED]
  arrears_analysis.py → app.py
- `arrears_analysis()` --indirect_call--> `ajax_ok()`  [INFERRED]
  arrears_analysis.py → app.py
- `handover()` --calls--> `allowed_file()`  [INFERRED]
  handover.py → app.py
- `handover()` --calls--> `ajax_error()`  [INFERRED]
  handover.py → app.py
- `handover()` --calls--> `ajax_ok()`  [INFERRED]
  handover.py → app.py

## Import Cycles
- None detected.

## Communities (61 total, 23 thin omitted)

### Community 0 - "arrears_analysis.py"
Cohesion: 0.07
Nodes (59): Any, _app(), arrears_analysis(), arrears_analysis_one_page_summary(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status() (+51 more)

### Community 1 - "data_comparison.py"
Cohesion: 0.08
Nodes (49): main(), Self-check for the Data Comparison page. Run: python check_data_comparison.py…, read(), active_figures(), _app(), build_comparison(), change_rows(), classify() (+41 more)

### Community 2 - "check_csv_headers_export.py"
Cohesion: 0.06
Nodes (27): _calc_col_widths(), clean_identifier(), export_advanced_bills(), export_advanced_bills_response(), fast_upload_number(), format_mobile(), generate_advanced_filtered_pdf(), generate_single_group_pdf() (+19 more)

### Community 3 - "app.py"
Cohesion: 0.09
Nodes (33): build_bill_key(), _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _dedupe_value(), _load_new_connection_detail_cache(), _ncd_classification(), _ncd_decimal(), _ncd_financial_year() (+25 more)

### Community 4 - "get_db"
Cohesion: 0.09
Nodes (34): apply_manual_zone_overrides(), backfill_bill_arrears(), bill_list(), build_unpaid_amount_summary(), clear_bill_list_data(), export_sectors_summary(), export_staff_summary(), export_summary_response() (+26 more)

### Community 5 - "audit_engine.py"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 6 - "parse_number"
Cohesion: 0.12
Nodes (24): bill_list_export_rows(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), _bill_list_summary_from_rows(), export_bill_list(), export_bill_list_staff(), parse_num(), _export_row_selection() (+16 more)

### Community 7 - "DataFrame"
Cohesion: 0.23
Nodes (23): build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_income_category_summary(), build_monthly_rows(), build_private_society_mask() (+15 more)

### Community 8 - "_build_consumer_sector_summary"
Cohesion: 0.13
Nodes (18): build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _clean_rate_type_name(), consumer_sector_remaining_report(), _is_extra_noor_mohalla_main_road_sector(), _is_extra_zain_city_13g_sector(), _is_faulty_empty_consumer_sector() (+10 more)

### Community 9 - "build_daily_staff_receive_report"
Cohesion: 0.13
Nodes (21): build_daily_staff_receive_report(), clean_cell(), clear_unmatched_log(), _closest_staff_key(), _deep_normalize_sector(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule() (+13 more)

### Community 10 - "_render_page"
Cohesion: 0.20
Nodes (21): apply_filters(), build_sector_summary(), col_key(), detail_columns(), detail_rows(), filter_label(), _finalize(), is_commercial() (+13 more)

### Community 11 - "wrap_pdf_body_cells"
Cohesion: 0.17
Nodes (18): _bracket_rich_text(), fmt_staff_name(), generate_commercial_monthly_pdf(), flush_group(), generate_grouped_advanced_pdf(), generate_staff_report_pdf(), numeric(), total_row() (+10 more)

### Community 12 - "handover.py"
Cohesion: 0.15
Nodes (16): _compose(), _conn_key(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path(), handover_snapshot() (+8 more)

### Community 13 - "build_handover_dataset"
Cohesion: 0.14
Nodes (17): build_handover_dataset(), _canonical_labels(), canonicalise_groups(), drop_excluded_sectors(), _numeric_amounts(), _pick(), Collapse whitespace and lower-case — used for every exact-match key., Write money columns to Excel as numbers, not "13,040" text, so the     arrears (+9 more)

### Community 14 - "download_card"
Cohesion: 0.15
Nodes (16): bill_income_category_export_rows(), build_connection_summary(), _card_rows_to_df(), download_card(), export_bill_income_category_summary(), export_dnc_register(), _filter_card_export(), fiscal_label_to_calendar_full_label() (+8 more)

### Community 15 - "route"
Cohesion: 0.12
Nodes (16): _connection_rate_rows_from_payload(), download_file(), export_connection_rate_report(), export_consumer_detail(), export_consumer_sector_remaining(), wrap_left(), file_column_matcher(), file_merger() (+8 more)

### Community 16 - "main"
Cohesion: 0.15
Nodes (15): main(), Self-check for the Handover Register join, filters, and snapshot lock. Run:…, read(), _column_extents(), _detail_widths(), _esc(), A detail table for the printed register.      Two corrections on top of the sh, Wrap only the long-text columns as Paragraphs.      Matches what ``wrap_pdf_bo (+7 more)

### Community 17 - "handover"
Cohesion: 0.17
Nodes (16): _app(), _gunzip(), handover(), _handover_dir(), handover_status(), _list_snapshots(), load_dataset(), Read an uploaded CSV/XLSX as text so connection numbers keep leading zeros. (+8 more)

### Community 18 - "fmt"
Cohesion: 0.18
Nodes (15): bill_list_zone_export_rows(), make_total_row(), commercial_daily_income_export_rows(), append_day_total(), export_unpaid_amount_section(), export_unpaid_amount_summary(), fmt(), generate_unpaid_amount_pdf() (+7 more)

### Community 19 - "export_handover"
Cohesion: 0.15
Nodes (14): build_sections(), export_handover(), handover_print(), _index_flowables(), _page_furniture(), The one date the register carries.      A finalised record is dated when it wa, The first page: a domestic report and a commercial report, side by side     in, The table of contents: sector name on the left, page on the right.      ``offs (+6 more)

### Community 20 - "allowed_file"
Cohesion: 0.18
Nodes (14): allowed_file(), _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows() (+6 more)

### Community 21 - "ajax_error"
Cohesion: 0.24
Nodes (13): ajax_error(), ajax_ok(), arrear_calculator(), build_dashboard_results(), daily_staff_receive(), index(), is_ajax(), _load_dashboard_results() (+5 more)

### Community 22 - "_build_connection_rate_report"
Cohesion: 0.22
Nodes (13): _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description(), _connection_rate_report_from_groups() (+5 more)

### Community 23 - "consumer_report"
Cohesion: 0.17
Nodes (12): _clear_consumer_summary_cache(), consumer_report(), _ensure_connection_rate_report(), _filter_active_rows(), _keep(), Return a copy of `summary` with all rows having zero active connections…, Split a summary dict into (normal, commercial, private_society). COMMERCIAL…, Persist the consumer summary to disk so it survives serverless cold starts.… (+4 more)

### Community 24 - "generate_daily_staff_receive_pdf"
Cohesion: 0.23
Nodes (12): _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), daily_staff_receive_export_response(), daily_staff_receive_export_tables(), export_daily_staff_receive(), export_daily_staff_receive_summary_pdf(), generate_daily_staff_receive_pdf(), generate_daily_staff_receive_summary_pdf() (+4 more)

### Community 25 - "export_consumer_report"
Cohesion: 0.17
Nodes (11): consumer_report_detail_records(), export_consumer_report(), _is_private_society_summary_row(), _load_consumer_rows_cache(), _load_consumer_summary_cache(), Shared sorting for the Consumer Sector Report (preview, PDF, CSV, Excel).…, Return True for domestic private-society rows shown in their own tab., Return consumer connection records for a specific sector/locality/category with… (+3 more)

### Community 26 - "NumberedCanvas"
Cohesion: 0.22
Nodes (5): Flowable, NumberedCanvas, _PageMark, A zero-height marker that reports the page it lands on.      Placed at the hea, Canvas that stamps "Page X of Y" once the total is known.      ReportLab strea

### Community 27 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 28 - "export_new_connection_detail"
Cohesion: 0.31
Nodes (10): export_new_connection_detail(), _ncd_annual_payload(), _ncd_annual_pdf(), _ncd_detail_pdf(), _ncd_export_rows(), _ncd_general_category_table(), _ncd_general_pdf(), _ncd_pdf_col_widths() (+2 more)

### Community 29 - "_normalize_rate_title"
Cohesion: 0.31
Nodes (9): _add_rate_alias(), _build_rate_lookup(), _domestic_annual_rate_override(), _connection_rate_lookup(), _load_rates_csv(), _normalize_rate_title(), Load rate data from the provided rates CSV or bundled rates.json. RATE SOURCE…, Canonical key for rate matching; tolerates case/spacing drift without changing… (+1 more)

### Community 30 - "_normalize_consumer_col"
Cohesion: 0.29
Nodes (7): _classify_connection_status(), _normalize_consumer_col(), _parse_consumer_csv(), Map each canonical key to the actual CSV column name that matched., Classify both 'Status' column values and 'Consumer Status' into…, Read uploaded CSV/XLSX and return (rows, errors). Uses flexible column matching…, _resolve_consumer_columns()

### Community 31 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list. Fixed column order: SR,…, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 32 - "export_zone_report_response"
Cohesion: 0.40
Nodes (6): export_bill_list_zone(), export_table_response(), export_zone_report_response(), transform_row(), without_zone(), generate_zone_grouped_pdf()

### Community 34 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 35 - "drop_duplicate_bills"
Cohesion: 0.50
Nodes (4): drop_duplicate_bills(), normalize_column_name(), normalize_dataframe(), Remove duplicate uploaded bills without collapsing different bills for one…

### Community 36 - "merge_sector_list_rows"
Cohesion: 0.50
Nodes (4): merge_sector_list_rows(), normalise_sector(), Normalise a sector name for grouping: trim, lowercase, collapse spaces., Merge list-of-lists rows by normalised sector. Keeps first locality, sums…

### Community 37 - "parse_received_dates"
Cohesion: 0.50
Nodes (4): parse_received_dates(), Swap day and month of a datetime to fix Excel DD-MM misinterpretation., Parse received dates handling mixed formats and Excel DD-MM swap issues., swap_day_month()

### Community 38 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

## Knowledge Gaps
- **7 isolated node(s):** `maxDuration`, `$schema`, `code:block1 (/graphify . --update)`, `code:block2 (/graphify query "how does bill upload work")`, `code:bash (# Development server)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 225 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `data_comparison.py` to `build_handover_dataset`, `audit_engine.py`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `audit_engine.py` to `data_comparison.py`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **What connects `maxDuration`, `$schema`, `code:block1 (/graphify . --update)` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `arrears_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07270865335381464 - nodes in this community are weakly interconnected._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0784313725490196 - nodes in this community are weakly interconnected._
- **Should `check_csv_headers_export.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06463414634146342 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08636977058029689 - nodes in this community are weakly interconnected._