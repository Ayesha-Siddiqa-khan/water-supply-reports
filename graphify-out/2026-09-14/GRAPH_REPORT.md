# Graph Report - .  (2026-09-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 626 nodes · 1571 edges · 50 communities (38 shown, 12 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 52 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `64534cc8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BytesIO
- DataFrame
- data_comparison.py
- arrears_analysis.py
- app.py
- audit_engine.py
- _render_page
- get_db
- build_consumer_sector_remaining_report
- build_handover_dataset
- handover.py
- _build_new_connection_detail_report
- _build_connection_rate_report
- consumer_sector_remaining_report
- main
- handover
- parse_number
- NumberedCanvas
- consumer_report
- export_consumer_report
- export_advanced_bills
- upload-progress.js
- match_staff_assignment
- _normalize_staff_name
- export_arrear_calculator
- vercel.json
- Water Supply Report Application
- _numeric_amounts
- normalize_sector_key
- route
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
- `classify()` --indirect_call--> `_status_of()`  [INFERRED]
  data_comparison.py → handover.py
- `classify()` --indirect_call--> `_type_of()`  [INFERRED]
  data_comparison.py → handover.py
- `arrears_analysis()` --calls--> `allowed_file()`  [INFERRED]
  arrears_analysis.py → app.py
- `handover()` --calls--> `allowed_file()`  [INFERRED]
  handover.py → app.py

## Import Cycles
- None detected.

## Communities (50 total, 12 thin omitted)

### Community 0 - "BytesIO"
Cohesion: 0.06
Nodes (81): bill_income_category_export_rows(), bill_list_export_rows(), _bracket_rich_text(), build_connection_summary(), _calc_col_widths(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), commercial_daily_income_export_rows() (+73 more)

### Community 1 - "DataFrame"
Cohesion: 0.08
Nodes (49): build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report(), build_dashboard_results() (+41 more)

### Community 2 - "data_comparison.py"
Cohesion: 0.08
Nodes (46): main(), Self-check for the Data Comparison page. Run: python check_data_comparison.py…, read(), active_figures(), _app(), build_comparison(), change_rows(), classify() (+38 more)

### Community 3 - "arrears_analysis.py"
Cohesion: 0.11
Nodes (37): Any, _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+29 more)

### Community 4 - "app.py"
Cohesion: 0.09
Nodes (27): apply_manual_zone_overrides(), bill_list(), _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register() (+19 more)

### Community 5 - "audit_engine.py"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 6 - "_render_page"
Cohesion: 0.17
Nodes (24): apply_filters(), build_sections(), build_sector_summary(), col_key(), detail_columns(), filter_label(), _finalize(), handover_print() (+16 more)

### Community 7 - "get_db"
Cohesion: 0.20
Nodes (23): bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data(), export_six_month_pitch(), fmt_staff_name(), get_bill_income_category_summary() (+15 more)

### Community 8 - "build_consumer_sector_remaining_report"
Cohesion: 0.13
Nodes (23): build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _classify_connection_status(), _clean_rate_type_name(), _is_extra_noor_mohalla_main_road_sector(), _is_extra_zain_city_13g_sector(), _is_faulty_commercial_hussain_colony() (+15 more)

### Community 9 - "build_handover_dataset"
Cohesion: 0.12
Nodes (21): build_handover_dataset(), _canonical_labels(), canonicalise_groups(), _compose(), _conn_key(), drop_excluded_sectors(), _key_frame(), _pick() (+13 more)

### Community 10 - "handover.py"
Cohesion: 0.14
Nodes (19): detail_rows(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path(), export_handover(), _index_flowables() (+11 more)

### Community 11 - "_build_new_connection_detail_report"
Cohesion: 0.15
Nodes (18): _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _load_new_connection_detail_cache(), _ncd_classification(), _ncd_decimal(), _ncd_financial_year(), _ncd_int(), _ncd_load_file() (+10 more)

### Community 12 - "_build_connection_rate_report"
Cohesion: 0.18
Nodes (16): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description() (+8 more)

### Community 13 - "consumer_sector_remaining_report"
Cohesion: 0.20
Nodes (16): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), consumer_sector_remaining_report(), daily_staff_receive(), index(), is_ajax() (+8 more)

### Community 14 - "main"
Cohesion: 0.15
Nodes (15): main(), Self-check for the Handover Register join, filters, and snapshot lock. Run:…, read(), _column_extents(), _detail_widths(), _esc(), A detail table for the printed register.      Two corrections on top of the sh, Wrap only the long-text columns as Paragraphs.      Matches what ``wrap_pdf_bo (+7 more)

### Community 15 - "handover"
Cohesion: 0.17
Nodes (16): _app(), _gunzip(), handover(), _handover_dir(), handover_status(), _list_snapshots(), load_dataset(), Read an uploaded CSV/XLSX as text so connection numbers keep leading zeros. (+8 more)

### Community 16 - "parse_number"
Cohesion: 0.15
Nodes (14): backfill_bill_arrears(), _bill_list_summary_from_rows(), _connection_rate_rows_from_payload(), is_large_pdf_text(), merge_sector_list_rows(), merge_sector_rows(), normalise_sector(), parse_number() (+6 more)

### Community 17 - "NumberedCanvas"
Cohesion: 0.16
Nodes (7): Flowable, NumberedCanvas, _page_furniture(), _PageMark, A zero-height marker that reports the page it lands on.      Placed at the hea, Canvas that stamps "Page X of Y" once the total is known.      ReportLab strea, Page-begin callback.      Runs before the frame lays its flowables down, which

### Community 18 - "consumer_report"
Cohesion: 0.17
Nodes (13): _clear_consumer_summary_cache(), consumer_report(), _ensure_connection_rate_report(), _filter_active_rows(), _load_rates_csv(), Return a copy of `summary` with all rows having zero active     connections remo, Split a summary dict into (normal, commercial, private_society).      COMMERCIAL, Load rate data from the provided rates CSV or bundled rates.json.      RATE SOUR (+5 more)

### Community 19 - "export_consumer_report"
Cohesion: 0.18
Nodes (11): consumer_report_detail_records(), export_consumer_report(), _is_private_society_summary_row(), _load_consumer_rows_cache(), _load_consumer_summary_cache(), Return True for domestic private-society rows shown in their own tab., Return consumer connection records for a specific sector/locality/category with, Load a previously saved consumer summary from disk. Returns (summary, filename, (+3 more)

### Community 20 - "export_advanced_bills"
Cohesion: 0.20
Nodes (11): export_advanced_bills(), format_mobile(), generate_zip_of_group_pdfs(), get_filtered_bills(), group_bills(), map_bills_to_staff(), Add a 'staff_name' key to each bill based on staff_assignments (locality > secto, Return sort key for zone ordering: A=1, B=2, C=3, Commercial=4, unknown=99. (+3 more)

### Community 21 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 22 - "match_staff_assignment"
Cohesion: 0.27
Nodes (10): clean_cell(), _deep_normalize_sector(), _keyword_set(), load_alias_rules(), match_by_alias(), match_key(), match_staff_assignment(), Aggressively normalize a sector/locality name for robust matching. (+2 more)

### Community 23 - "_normalize_staff_name"
Cohesion: 0.29
Nodes (8): _closest_staff_key(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), _levenshtein(), _normalize_sector_locality(), _normalize_staff_name(), Like fmt_staff_name but returns HTML with <br> for display.

### Community 24 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list.      Fixed column order:, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 25 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 26 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

### Community 27 - "_numeric_amounts"
Cohesion: 0.50
Nodes (4): _numeric_amounts(), Write money columns to Excel as numbers, not "13,040" text, so the     arrears, Parse a money cell tolerantly.      Pulls the first number out rather than del, _to_amount()

## Knowledge Gaps
- **7 isolated node(s):** `$schema`, `maxDuration`, `code:block1 (/graphify . --update)`, `code:block2 (/graphify query "how does bill upload work")`, `code:bash (# Development server)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `data_comparison.py` to `build_handover_dataset`, `audit_engine.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `audit_engine.py` to `data_comparison.py`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `ParagraphStyle` (e.g. with `build_arrears_pdf()` and `_report_pdf()`) actually correct?**
  _`ParagraphStyle` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Sector-wise auditor for the DNS Register connection CSVs. Pure logic, no Flask.…`, `4,800' -> 4800.0, '' -> 0.0, garbage -> None.`, `4,800 / 2,400' -> (4800.0, 2400.0). Demand / collection in one cell.` to the rest of the system?**
  _159 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `BytesIO` be split into smaller, more focused modules?**
  _Cohesion score 0.05541368743615935 - nodes in this community are weakly interconnected._
- **Should `DataFrame` be split into smaller, more focused modules?**
  _Cohesion score 0.08418367346938775 - nodes in this community are weakly interconnected._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08244680851063829 - nodes in this community are weakly interconnected._