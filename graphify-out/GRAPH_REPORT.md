# Graph Report - .  (2026-09-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 637 nodes · 1584 edges · 48 communities (35 shown, 13 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 52 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1076093a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BytesIO
- consumer_report
- data_comparison.py
- DataFrame
- arrears_analysis.py
- audit_engine.py
- app.py
- get_db
- handover.py
- generate_grouped_advanced_pdf
- _render_page
- build_daily_staff_receive_report
- _build_new_connection_detail_report
- build_handover_dataset
- main
- index
- parse_number
- NumberedCanvas
- get_filtered_bills
- upload-progress.js
- export_handover
- _key_frame
- vercel.json
- Water Supply Report Application
- load_dataset
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
- `classify()` --indirect_call--> `_type_of()`  [INFERRED]
  data_comparison.py → handover.py
- `arrears_analysis()` --indirect_call--> `ajax_error()`  [INFERRED]
  arrears_analysis.py → app.py
- `arrears_analysis()` --indirect_call--> `ajax_ok()`  [INFERRED]
  arrears_analysis.py → app.py
- `arrears_analysis()` --calls--> `allowed_file()`  [INFERRED]
  arrears_analysis.py → app.py

## Import Cycles
- None detected.

## Communities (48 total, 13 thin omitted)

### Community 0 - "BytesIO"
Cohesion: 0.07
Nodes (76): bill_income_category_export_rows(), bill_list_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), _bracket_rich_text(), build_connection_summary(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths() (+68 more)

### Community 1 - "consumer_report"
Cohesion: 0.05
Nodes (66): _add_rate_alias(), allowed_file(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality() (+58 more)

### Community 2 - "data_comparison.py"
Cohesion: 0.08
Nodes (49): main(), Self-check for the Data Comparison page. Run: python check_data_comparison.py…, read(), active_figures(), _app(), build_comparison(), change_rows(), classify() (+41 more)

### Community 3 - "DataFrame"
Cohesion: 0.08
Nodes (50): _build_arrear_export_rows(), build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_income_category_summary() (+42 more)

### Community 4 - "arrears_analysis.py"
Cohesion: 0.11
Nodes (37): Any, _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+29 more)

### Community 5 - "audit_engine.py"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 6 - "app.py"
Cohesion: 0.09
Nodes (24): _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows(), _dnc_split_sector_locality() (+16 more)

### Community 7 - "get_db"
Cohesion: 0.11
Nodes (29): apply_manual_zone_overrides(), bill_list(), bill_list_sector_seasonly_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data(), export_sectors_summary(), export_staff_summary(), export_zones_summary() (+21 more)

### Community 8 - "handover.py"
Cohesion: 0.12
Nodes (25): _app(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path(), _gunzip(), handover() (+17 more)

### Community 9 - "generate_grouped_advanced_pdf"
Cohesion: 0.16
Nodes (15): _calc_col_widths(), export_advanced_bills(), export_advanced_bills_response(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), generate_zip_of_group_pdfs(), group_bills(), _GroupedPdfWrapper (+7 more)

### Community 10 - "_render_page"
Cohesion: 0.20
Nodes (21): apply_filters(), build_sector_summary(), col_key(), detail_columns(), detail_rows(), filter_label(), _finalize(), is_commercial() (+13 more)

### Community 11 - "build_daily_staff_receive_report"
Cohesion: 0.14
Nodes (18): build_daily_staff_receive_report(), clean_cell(), clear_unmatched_log(), _deep_normalize_sector(), get_auto_staff_override(), get_staff_by_connection_rule(), get_unmatched_log(), infer_zone() (+10 more)

### Community 12 - "_build_new_connection_detail_report"
Cohesion: 0.15
Nodes (18): _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _load_new_connection_detail_cache(), _ncd_classification(), _ncd_decimal(), _ncd_financial_year(), _ncd_int(), _ncd_load_file() (+10 more)

### Community 13 - "build_handover_dataset"
Cohesion: 0.15
Nodes (17): build_handover_dataset(), _canonical_labels(), canonicalise_groups(), drop_excluded_sectors(), _numeric_amounts(), Collapse whitespace and lower-case — used for every exact-match key., Commercial when the rate type says so — including the ``COMERCIAL``     spellin, Write money columns to Excel as numbers, not "13,040" text, so the     arrears (+9 more)

### Community 14 - "main"
Cohesion: 0.15
Nodes (15): main(), Self-check for the Handover Register join, filters, and snapshot lock. Run:…, read(), _column_extents(), _detail_widths(), _esc(), A detail table for the printed register.      Two corrections on top of the sh, Wrap only the long-text columns as Paragraphs.      Matches what ``wrap_pdf_bo (+7 more)

### Community 15 - "index"
Cohesion: 0.21
Nodes (15): ajax_error(), ajax_ok(), arrear_calculator(), build_dashboard_results(), daily_staff_receive(), index(), is_ajax(), _load_dashboard_results() (+7 more)

### Community 16 - "parse_number"
Cohesion: 0.15
Nodes (14): backfill_bill_arrears(), _bill_list_summary_from_rows(), _connection_rate_rows_from_payload(), is_large_pdf_text(), merge_sector_list_rows(), merge_sector_rows(), normalise_sector(), parse_number() (+6 more)

### Community 17 - "NumberedCanvas"
Cohesion: 0.16
Nodes (7): Flowable, NumberedCanvas, _page_furniture(), _PageMark, A zero-height marker that reports the page it lands on.      Placed at the hea, Canvas that stamps "Page X of Y" once the total is known.      ReportLab strea, Page-begin callback.      Runs before the frame lays its flowables down, which

### Community 18 - "get_filtered_bills"
Cohesion: 0.17
Nodes (8): clean_identifier(), fast_upload_number(), format_mobile(), get_filtered_bills(), Fast numeric parser for Bill Reports upload amount columns., Clean and preserve exact identifier strings (connection_no, bill_no, ref_no, etc, Runnable self-check for the Advanced Bill Checking CSV headers export. Run: .ven, test_get_filtered_bills_headers()

### Community 19 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 20 - "export_handover"
Cohesion: 0.25
Nodes (9): build_sections(), export_handover(), handover_print(), _index_flowables(), The one date the register carries.      A finalised record is dated when it wa, The table of contents: sector name on the left, page on the right.      ``offs, Split the register into printable blocks.      Ordinary sectors come first, se, report_date() (+1 more)

### Community 21 - "_key_frame"
Cohesion: 0.40
Nodes (5): _compose(), _conn_key(), _key_frame(), Series, Alphanumerics only, lower-cased, leading zeros removed.      Connection number

### Community 22 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 23 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

### Community 24 - "load_dataset"
Cohesion: 0.50
Nodes (4): _list_snapshots(), load_dataset(), Return (rows, meta). Snapshots read their own frozen copy., _snapshot_dir()

## Knowledge Gaps
- **7 isolated node(s):** `$schema`, `maxDuration`, `code:block1 (/graphify . --update)`, `code:block2 (/graphify query "how does bill upload work")`, `code:bash (# Development server)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `data_comparison.py` to `build_handover_dataset`, `audit_engine.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `audit_engine.py` to `data_comparison.py`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `ParagraphStyle` (e.g. with `build_arrears_pdf()` and `_report_pdf()`) actually correct?**
  _`ParagraphStyle` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Sector-wise auditor for the DNS Register connection CSVs. Pure logic, no Flask.…`, `4,800' -> 4800.0, '' -> 0.0, garbage -> None.`, `4,800 / 2,400' -> (4800.0, 2400.0). Demand / collection in one cell.` to the rest of the system?**
  _161 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `BytesIO` be split into smaller, more focused modules?**
  _Cohesion score 0.0673274094326726 - nodes in this community are weakly interconnected._
- **Should `consumer_report` be split into smaller, more focused modules?**
  _Cohesion score 0.05034965034965035 - nodes in this community are weakly interconnected._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07764705882352942 - nodes in this community are weakly interconnected._