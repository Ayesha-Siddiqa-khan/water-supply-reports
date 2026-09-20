# Graph Report - .  (2026-09-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 640 nodes · 1587 edges · 51 communities (37 shown, 14 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 52 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e222ebcb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BytesIO
- fmt
- data_comparison.py
- DataFrame
- arrears_analysis.py
- app.py
- audit_engine.py
- build_consumer_sector_remaining_report
- _render_page
- handover.py
- match_staff_assignment
- build_handover_dataset
- main
- index
- NumberedCanvas
- get_filtered_bills
- allowed_file
- consumer_report
- export_consumer_report
- upload-progress.js
- load_dataset
- _normalize_rate_title
- export_arrear_calculator
- _build_connection_rate_report_from_summary
- export_handover
- vercel.json
- Water Supply Report Application
- check_consumer_connections_summary.py
- DataFrame
- route
- Series
- route
- errorhandler
- pdf-lib (CDN library)
- SheetJS (CDN library)
- route
- code:block1 (/graphify . --update)
- code:block2 (/graphify query "how does bill upload work")
- code:bash (# Development server)
- code:text (You are working on an existing running application. This app)
- code:bash (claude)

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 33 edges
2. `get_db()` - 27 edges
3. `init_bill_list_db()` - 23 edges
4. `download_card()` - 22 edges
5. `summarize_dataframe()` - 18 edges
6. `export_six_month_pitch()` - 18 edges
7. `_render_page()` - 17 edges
8. `parse_number()` - 16 edges
9. `build_daily_staff_receive_report()` - 16 edges
10. `consumer_report()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `parse_register()` --calls--> `classify()`  [INFERRED]
  audit_engine.py → data_comparison.py
- `arrears_analysis()` --indirect_call--> `ajax_error()`  [INFERRED]
  arrears_analysis.py → app.py
- `arrears_analysis()` --indirect_call--> `ajax_ok()`  [INFERRED]
  arrears_analysis.py → app.py
- `arrears_analysis()` --calls--> `allowed_file()`  [INFERRED]
  arrears_analysis.py → app.py
- `handover()` --calls--> `ajax_error()`  [INFERRED]
  handover.py → app.py

## Import Cycles
- None detected.

## Communities (51 total, 14 thin omitted)

### Community 0 - "BytesIO"
Cohesion: 0.06
Nodes (72): _bracket_rich_text(), _calc_col_widths(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), _card_rows_to_df(), commercial_daily_income_export_rows(), daily_staff_receive_export_response(), daily_staff_receive_export_tables() (+64 more)

### Community 1 - "fmt"
Cohesion: 0.06
Nodes (67): backfill_bill_arrears(), bill_income_category_export_rows(), bill_list(), bill_list_export_rows(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), _bill_list_summary_from_rows(), bill_list_zone_export_rows() (+59 more)

### Community 2 - "data_comparison.py"
Cohesion: 0.08
Nodes (49): main(), Self-check for the Data Comparison page. Run: python check_data_comparison.py…, read(), active_figures(), _app(), build_comparison(), change_rows(), classify() (+41 more)

### Community 3 - "DataFrame"
Cohesion: 0.10
Nodes (43): build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report(), build_income_category_summary() (+35 more)

### Community 4 - "arrears_analysis.py"
Cohesion: 0.11
Nodes (37): Any, _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+29 more)

### Community 5 - "app.py"
Cohesion: 0.09
Nodes (31): _annualize_connection_rate(), apply_manual_zone_overrides(), _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _connection_rate_default(), _connection_report_annual_rate(), file_column_matcher(), file_merger() (+23 more)

### Community 6 - "audit_engine.py"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 7 - "build_consumer_sector_remaining_report"
Cohesion: 0.14
Nodes (26): _build_connection_rate_report(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _classify_connection_status(), _clean_rate_type_name(), consumer_sector_remaining_report(), _is_extra_noor_mohalla_main_road_sector() (+18 more)

### Community 8 - "_render_page"
Cohesion: 0.17
Nodes (24): apply_filters(), build_sections(), build_sector_summary(), col_key(), detail_columns(), filter_label(), _finalize(), handover_print() (+16 more)

### Community 9 - "handover.py"
Cohesion: 0.14
Nodes (22): _app(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path(), _gunzip(), handover() (+14 more)

### Community 10 - "match_staff_assignment"
Cohesion: 0.14
Nodes (18): clean_cell(), _closest_staff_key(), _deep_normalize_sector(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), _keyword_set(), _levenshtein() (+10 more)

### Community 11 - "build_handover_dataset"
Cohesion: 0.13
Nodes (18): build_handover_dataset(), _canonical_labels(), canonicalise_groups(), _compose(), _conn_key(), drop_excluded_sectors(), _key_frame(), _pick() (+10 more)

### Community 12 - "main"
Cohesion: 0.15
Nodes (15): main(), Self-check for the Handover Register join, filters, and snapshot lock. Run:…, read(), _column_extents(), _detail_widths(), _esc(), A detail table for the printed register.      Two corrections on top of the sh, Wrap only the long-text columns as Paragraphs.      Matches what ``wrap_pdf_bo (+7 more)

### Community 13 - "index"
Cohesion: 0.21
Nodes (15): ajax_error(), ajax_ok(), arrear_calculator(), build_dashboard_results(), daily_staff_receive(), index(), is_ajax(), _load_dashboard_results() (+7 more)

### Community 14 - "NumberedCanvas"
Cohesion: 0.16
Nodes (7): Flowable, NumberedCanvas, _page_furniture(), _PageMark, A zero-height marker that reports the page it lands on.      Placed at the hea, Canvas that stamps "Page X of Y" once the total is known.      ReportLab strea, Page-begin callback.      Runs before the frame lays its flowables down, which

### Community 15 - "get_filtered_bills"
Cohesion: 0.17
Nodes (8): clean_identifier(), fast_upload_number(), format_mobile(), get_filtered_bills(), Fast numeric parser for Bill Reports upload amount columns., Clean and preserve exact identifier strings (connection_no, bill_no, ref_no, etc, Runnable self-check for the Advanced Bill Checking CSV headers export. Run: .ven, test_get_filtered_bills_headers()

### Community 16 - "allowed_file"
Cohesion: 0.21
Nodes (12): allowed_file(), _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows() (+4 more)

### Community 17 - "consumer_report"
Cohesion: 0.20
Nodes (11): _clear_consumer_summary_cache(), consumer_report(), _ensure_connection_rate_report(), _filter_active_rows(), Return a copy of `summary` with all rows having zero active     connections remo, Split a summary dict into (normal, commercial, private_society).      COMMERCIAL, Persist the consumer summary to disk so it survives serverless cold starts., Persist consumer individual connection rows (compressed gzip) for drilldown. (+3 more)

### Community 18 - "export_consumer_report"
Cohesion: 0.18
Nodes (11): consumer_report_detail_records(), export_consumer_report(), _is_private_society_summary_row(), _load_consumer_rows_cache(), _load_consumer_summary_cache(), Shared sorting for the Consumer Sector Report (preview, PDF, CSV, Excel).      A, Return True for domestic private-society rows shown in their own tab., Return consumer connection records for a specific sector/locality/category with (+3 more)

### Community 19 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 20 - "load_dataset"
Cohesion: 0.25
Nodes (8): _list_snapshots(), load_dataset(), _numeric_amounts(), Write money columns to Excel as numbers, not "13,040" text, so the     arrears, Parse a money cell tolerantly.      Pulls the first number out rather than del, Return (rows, meta). Snapshots read their own frozen copy., _snapshot_dir(), _to_amount()

### Community 21 - "_normalize_rate_title"
Cohesion: 0.33
Nodes (7): _add_rate_alias(), _connection_rate_lookup(), _load_rates_csv(), _normalize_rate_title(), Load rate data from the provided rates CSV or bundled rates.json.      RATE SOUR, Canonical key for rate matching; tolerates case/spacing drift without changing d, Map known legacy consumer rate labels to the active rate title.

### Community 22 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list.      Fixed column order:, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 23 - "_build_connection_rate_report_from_summary"
Cohesion: 0.29
Nodes (7): _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_description(), _connection_rate_report_from_groups(), _norm_report_text(), Fallback for already-cached Consumer Report data without raw upload rows.

### Community 24 - "export_handover"
Cohesion: 0.29
Nodes (7): detail_rows(), export_handover(), _index_flowables(), The one date the register carries.      A finalised record is dated when it wa, The table of contents: sector name on the left, page on the right.      ``offs, report_date(), _signature_band_height()

### Community 25 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 26 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

## Knowledge Gaps
- **7 isolated node(s):** `$schema`, `maxDuration`, `code:block1 (/graphify . --update)`, `code:block2 (/graphify query "how does bill upload work")`, `code:bash (# Development server)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `data_comparison.py` to `build_handover_dataset`, `audit_engine.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `audit_engine.py` to `data_comparison.py`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `ParagraphStyle` (e.g. with `build_arrears_pdf()` and `_report_pdf()`) actually correct?**
  _`ParagraphStyle` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Sector-wise auditor for the DNS Register connection CSVs. Pure logic, no Flask.…`, `4,800' -> 4800.0, '' -> 0.0, garbage -> None.`, `4,800 / 2,400' -> (4800.0, 2400.0). Demand / collection in one cell.` to the rest of the system?**
  _162 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `BytesIO` be split into smaller, more focused modules?**
  _Cohesion score 0.05506329113924051 - nodes in this community are weakly interconnected._
- **Should `fmt` be split into smaller, more focused modules?**
  _Cohesion score 0.05698778833107191 - nodes in this community are weakly interconnected._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0784313725490196 - nodes in this community are weakly interconnected._