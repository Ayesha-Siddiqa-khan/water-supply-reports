# Graph Report - water suppy report  (2026-09-27)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 693 nodes · 1612 edges · 57 communities (34 shown, 23 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 53 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5896fbe2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _build_consumer_sector_summary
- data_comparison.py
- DataFrame
- arrears_analysis.py
- check_csv_headers_export.py
- app.py
- audit_engine.py
- consumer_report
- handover.py
- get_db
- _render_page
- _register_table
- route
- classify
- match_staff_assignment
- export_consumer_report
- fmt
- wrap_pdf_body_cells
- parse_number
- _build_new_connection_detail_report
- _build_dnc_register_report
- NumberedCanvas
- upload-progress.js
- generate_card_pdf
- export_new_connection_detail
- export_bill_list
- generate_daily_staff_receive_pdf
- export_six_month_pitch
- main
- export_arrear_calculator
- export_handover
- _key_frame
- vercel.json
- Water Supply Report Application
- check_consumer_connections_summary.py
- DataFrame
- route
- Series
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
4. `parse_number()` - 21 edges
5. `download_card()` - 21 edges
6. `wrap_pdf_body_cells()` - 20 edges
7. `summarize_dataframe()` - 18 edges
8. `_build_consumer_sector_summary()` - 17 edges
9. `export_six_month_pitch()` - 17 edges
10. `consumer_report()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `arrears_analysis()` --indirect_call--> `ajax_error()`  [INFERRED]
  arrears_analysis.py → app.py
- `handover()` --calls--> `ajax_error()`  [INFERRED]
  handover.py → app.py
- `arrears_analysis()` --indirect_call--> `ajax_ok()`  [INFERRED]
  arrears_analysis.py → app.py
- `handover()` --calls--> `ajax_ok()`  [INFERRED]
  handover.py → app.py
- `arrears_analysis()` --calls--> `allowed_file()`  [INFERRED]
  arrears_analysis.py → app.py

## Import Cycles
- None detected.

## Communities (57 total, 23 thin omitted)

### Community 0 - "_build_consumer_sector_summary"
Cohesion: 0.07
Nodes (45): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _build_rate_lookup(), _domestic_annual_rate_override() (+37 more)

### Community 1 - "data_comparison.py"
Cohesion: 0.08
Nodes (44): main(), Self-check for the Data Comparison page. Run: python check_data_comparison.py…, read(), active_figures(), _app(), build_comparison(), change_rows(), clear_result() (+36 more)

### Community 2 - "DataFrame"
Cohesion: 0.10
Nodes (43): build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report(), build_income_category_summary() (+35 more)

### Community 3 - "arrears_analysis.py"
Cohesion: 0.11
Nodes (37): Any, _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+29 more)

### Community 4 - "check_csv_headers_export.py"
Cohesion: 0.06
Nodes (28): _calc_col_widths(), clean_identifier(), export_advanced_bills(), export_advanced_bills_response(), fast_upload_number(), format_mobile(), generate_advanced_filtered_pdf(), generate_single_group_pdf() (+20 more)

### Community 5 - "app.py"
Cohesion: 0.07
Nodes (33): build_connection_summary(), _card_rows_to_df(), download_card(), fiscal_label_to_calendar_full_label(), fiscal_label_to_calendar_label(), format_calendar_month(), generate_commercial_pdf(), _get_card_col_map() (+25 more)

### Community 6 - "audit_engine.py"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 7 - "consumer_report"
Cohesion: 0.10
Nodes (30): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), bill_list(), build_dashboard_results(), _clear_consumer_summary_cache(), consumer_report() (+22 more)

### Community 8 - "handover.py"
Cohesion: 0.13
Nodes (26): _app(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path(), _gunzip(), handover() (+18 more)

### Community 9 - "get_db"
Cohesion: 0.15
Nodes (25): apply_manual_zone_overrides(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), clear_bill_list_data(), get_bill_income_category_summary(), get_bill_list_context(), get_db() (+17 more)

### Community 10 - "_render_page"
Cohesion: 0.17
Nodes (24): apply_filters(), build_sections(), build_sector_summary(), col_key(), detail_columns(), filter_label(), _finalize(), handover_print() (+16 more)

### Community 11 - "_register_table"
Cohesion: 0.13
Nodes (19): _bracket_rich_text(), Split text into normal and bracket segments for rich text rendering. Returns a…, _column_extents(), _detail_widths(), _esc(), _index_flowables(), The first page: a domestic report and a commercial report, side by side     in, A detail table for the printed register.      Two corrections on top of the sh (+11 more)

### Community 12 - "route"
Cohesion: 0.12
Nodes (19): _connection_rate_rows_from_payload(), download_file(), export_connection_rate_report(), export_consumer_detail(), export_daily_staff_receive(), export_daily_staff_receive_summary_pdf(), export_sectors_summary(), export_staff_summary() (+11 more)

### Community 13 - "classify"
Cohesion: 0.16
Nodes (18): classify(), Reduce an export to the fields this page compares. A connection counts as…, build_handover_dataset(), _canonical_labels(), canonicalise_groups(), drop_excluded_sectors(), _pick(), Collapse whitespace and lower-case — used for every exact-match key. (+10 more)

### Community 14 - "match_staff_assignment"
Cohesion: 0.15
Nodes (17): clean_cell(), _deep_normalize_sector(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), _keyword_set(), _levenshtein(), load_alias_rules() (+9 more)

### Community 15 - "export_consumer_report"
Cohesion: 0.12
Nodes (15): consumer_report_detail_records(), export_consumer_report(), _filter_active_rows(), _is_private_society_summary_row(), _load_consumer_rows_cache(), _load_consumer_summary_cache(), Shared sorting for the Consumer Sector Report (preview, PDF, CSV, Excel).…, Return a copy of `summary` with all rows having zero active connections… (+7 more)

### Community 16 - "fmt"
Cohesion: 0.16
Nodes (15): bill_income_category_export_rows(), build_unpaid_amount_summary(), commercial_daily_income_export_rows(), append_day_total(), export_unpaid_amount_section(), export_unpaid_amount_summary(), fmt(), generate_unpaid_amount_pdf() (+7 more)

### Community 17 - "wrap_pdf_body_cells"
Cohesion: 0.20
Nodes (15): export_consumer_sector_remaining(), wrap_left(), generate_commercial_monthly_pdf(), flush_group(), generate_staff_report_pdf(), numeric(), total_row(), wrap_sum_left() (+7 more)

### Community 18 - "parse_number"
Cohesion: 0.14
Nodes (15): backfill_bill_arrears(), _bill_list_summary_from_rows(), make_total_row(), export_bill_list_staff(), parse_num(), is_large_pdf_text(), merge_sector_list_rows(), merge_sector_rows() (+7 more)

### Community 19 - "_build_new_connection_detail_report"
Cohesion: 0.21
Nodes (14): _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _load_new_connection_detail_cache(), _ncd_classification(), _ncd_decimal(), _ncd_int(), _ncd_load_file(), _ncd_parse_date() (+6 more)

### Community 20 - "_build_dnc_register_report"
Cohesion: 0.21
Nodes (12): _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows(), _dnc_split_sector_locality() (+4 more)

### Community 21 - "NumberedCanvas"
Cohesion: 0.20
Nodes (5): Flowable, NumberedCanvas, _PageMark, A zero-height marker that reports the page it lands on.      Placed at the hea, Canvas that stamps "Page X of Y" once the total is known.      ReportLab strea

### Community 22 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 23 - "generate_card_pdf"
Cohesion: 0.22
Nodes (10): export_bill_income_category_summary(), export_bill_list_zone(), export_table_response(), export_zone_report_response(), transform_row(), without_zone(), _filter_card_export(), generate_card_pdf() (+2 more)

### Community 24 - "export_new_connection_detail"
Cohesion: 0.31
Nodes (10): export_new_connection_detail(), _ncd_annual_payload(), _ncd_annual_pdf(), _ncd_detail_pdf(), _ncd_export_rows(), _ncd_general_category_table(), _ncd_general_pdf(), _ncd_pdf_col_widths() (+2 more)

### Community 25 - "export_bill_list"
Cohesion: 0.28
Nodes (9): bill_list_export_rows(), export_bill_list(), _export_row_selection(), export_season_sector_pitch(), wrap_left(), _filter_rows_by_selection(), Read bill-list row checkbox selection from export query params., Keep only bill-list rows selected by the page checkboxes before exporting. (+1 more)

### Community 26 - "generate_daily_staff_receive_pdf"
Cohesion: 0.39
Nodes (8): _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), daily_staff_receive_export_response(), daily_staff_receive_export_tables(), generate_daily_staff_receive_pdf(), generate_daily_staff_receive_summary_pdf(), parse_export_cols(), Calculate column widths for the daily staff receive summary table.

### Community 27 - "export_six_month_pitch"
Cohesion: 0.29
Nodes (8): _closest_staff_key(), export_six_month_pitch(), pn(), wrap_left(), fmt_staff_name(), generate_grouped_advanced_pdf(), Return display name: paired staff on separate lines, else as-is., Generate a landscape PDF with one section per group showing detailed bill rows.

### Community 28 - "main"
Cohesion: 0.29
Nodes (7): main(), Self-check for the Handover Register join, filters, and snapshot lock. Run:…, read(), _numeric_amounts(), Write money columns to Excel as numbers, not "13,040" text, so the     arrears, Parse a money cell tolerantly.      Pulls the first number out rather than del, _to_amount()

### Community 29 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list. Fixed column order: SR,…, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 30 - "export_handover"
Cohesion: 0.29
Nodes (7): detail_rows(), export_handover(), _page_furniture(), The one date the register carries.      A finalised record is dated when it wa, Page-begin callback.      Runs before the frame lays its flowables down, which, report_date(), _signature_band_height()

### Community 31 - "_key_frame"
Cohesion: 0.40
Nodes (5): _compose(), _conn_key(), _key_frame(), Series, Alphanumerics only, lower-cased, leading zeros removed.      Connection number

### Community 32 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 33 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

## Knowledge Gaps
- **7 isolated node(s):** `maxDuration`, `$schema`, `code:block1 (/graphify . --update)`, `code:block2 (/graphify query "how does bill upload work")`, `code:bash (# Development server)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 226 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `classify` to `data_comparison.py`, `audit_engine.py`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `audit_engine.py` to `classify`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **What connects `maxDuration`, `$schema`, `code:block1 (/graphify . --update)` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `_build_consumer_sector_summary` be split into smaller, more focused modules?**
  _Cohesion score 0.0673758865248227 - nodes in this community are weakly interconnected._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0821256038647343 - nodes in this community are weakly interconnected._
- **Should `DataFrame` be split into smaller, more focused modules?**
  _Cohesion score 0.09745293466223699 - nodes in this community are weakly interconnected._
- **Should `arrears_analysis.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11149825783972125 - nodes in this community are weakly interconnected._