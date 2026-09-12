# Graph Report - water suppy report  (2026-09-12)

## Corpus Check
- 36 files · ~146,796 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 633 nodes · 1625 edges · 47 communities (39 shown, 8 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 53 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `470b839a`
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
- BytesIO
- classify
- build_daily_staff_receive_report
- index
- _normalize_staff_name
- bill_list_sector_seasonly_export_rows
- NumberedCanvas
- _register_table
- bill_list_zone_export_rows
- main
- DataFrame
- handover
- upload-progress.js
- export_consumer_report
- normalize_sector_key
- _build_connection_rate_report
- vercel.json
- Water Supply Report Application
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
7. `consumer_report()` - 17 edges
8. `_render_page()` - 17 edges
9. `parse_number()` - 16 edges
10. `build_daily_staff_receive_report()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `arrears_analysis()` --calls--> `allowed_file()`  [INFERRED]
  arrears_analysis.py → app.py
- `handover()` --calls--> `allowed_file()`  [INFERRED]
  handover.py → app.py
- `handover()` --calls--> `is_ajax()`  [INFERRED]
  handover.py → app.py
- `arrears_analysis()` --indirect_call--> `ajax_ok()`  [INFERRED]
  arrears_analysis.py → app.py
- `handover()` --calls--> `ajax_ok()`  [INFERRED]
  handover.py → app.py

## Import Cycles
- None detected.

## Communities (47 total, 8 thin omitted)

### Community 0 - "data_comparison.py"
Cohesion: 0.10
Nodes (39): active_figures(), _app(), build_comparison(), change_rows(), clear_result(), _column(), comparable(), _consumer_active() (+31 more)

### Community 1 - "DataFrame"
Cohesion: 0.09
Nodes (45): build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_income_category_summary(), build_monthly_rows() (+37 more)

### Community 2 - "arrears_analysis.py"
Cohesion: 0.11
Nodes (38): Any, _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+30 more)

### Community 3 - "app.py"
Cohesion: 0.10
Nodes (33): allowed_file(), _build_dnc_register_report(), _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification() (+25 more)

### Community 4 - "get_db"
Cohesion: 0.21
Nodes (18): apply_manual_zone_overrides(), bill_list(), bill_list_staff_export_rows(), clear_bill_list_data(), format_mobile(), get_assignment_conflicts(), get_bill_list_context(), get_db() (+10 more)

### Community 5 - "audit_engine.py"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 6 - "consumer_sector_remaining_report"
Cohesion: 0.13
Nodes (25): build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _classify_connection_status(), _clean_rate_type_name(), consumer_sector_remaining_report(), _is_extra_noor_mohalla_main_road_sector(), _is_extra_zain_city_13g_sector() (+17 more)

### Community 7 - "handover.py"
Cohesion: 0.13
Nodes (18): _compose(), _conn_key(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path(), _key_frame() (+10 more)

### Community 8 - "consumer_report"
Cohesion: 0.17
Nodes (13): _clear_consumer_summary_cache(), consumer_report(), _ensure_connection_rate_report(), _filter_active_rows(), _load_rates_csv(), Load rate data from the provided rates CSV or bundled rates.json. RATE SOURCE…, Persist the consumer summary to disk so it survives serverless cold starts.…, Persist consumer individual connection rows (compressed gzip) for drilldown. (+5 more)

### Community 9 - "_render_page"
Cohesion: 0.22
Nodes (13): col_key(), detail_columns(), filter_label(), _finalize(), handover_snapshot(), All available detail columns, with the default register set pre-ticked., Watermark text and on/off state, read from the request. ``wmset`` plays the…, Signature fields and placement, read from the request. ``sigset`` marks a form… (+5 more)

### Community 10 - "match_staff_assignment"
Cohesion: 0.24
Nodes (11): clean_cell(), _deep_normalize_sector(), _keyword_set(), _levenshtein(), load_alias_rules(), match_by_alias(), match_key(), match_staff_assignment() (+3 more)

### Community 11 - "_GroupedPdfWrapper"
Cohesion: 0.14
Nodes (17): _calc_col_widths(), export_advanced_bills(), export_advanced_bills_response(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), generate_zip_of_group_pdfs(), group_bills(), _GroupedPdfWrapper (+9 more)

### Community 12 - "BytesIO"
Cohesion: 0.05
Nodes (94): bill_income_category_export_rows(), bill_list_export_rows(), _bracket_rich_text(), _build_arrear_export_rows(), build_connection_summary(), build_unpaid_amount_summary(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths() (+86 more)

### Community 13 - "classify"
Cohesion: 0.14
Nodes (21): main(), Self-check for the Data Comparison page. Run: python check_data_comparison.py…, read(), classify(), _key(), Connection Number reduced to a comparable form. Leading zeros are KEPT. The…, Reduce an export to the fields this page compares. A connection counts as…, build_handover_dataset() (+13 more)

### Community 14 - "build_daily_staff_receive_report"
Cohesion: 0.12
Nodes (19): backfill_bill_arrears(), _bill_list_summary_from_rows(), build_daily_staff_receive_report(), clear_unmatched_log(), _connection_rate_rows_from_payload(), get_unmatched_log(), infer_zone(), is_large_pdf_text() (+11 more)

### Community 15 - "index"
Cohesion: 0.19
Nodes (16): ajax_error(), ajax_ok(), arrear_calculator(), build_dashboard_results(), daily_staff_receive(), index(), is_ajax(), _load_dashboard_results() (+8 more)

### Community 16 - "_normalize_staff_name"
Cohesion: 0.40
Nodes (6): fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), _normalize_sector_locality(), _normalize_staff_name(), Like fmt_staff_name but returns HTML with <br> for display.

### Community 17 - "bill_list_sector_seasonly_export_rows"
Cohesion: 0.40
Nodes (5): bill_list_sector_seasonly_export_rows(), _get_season_bill_ids(), Return set of bill IDs whose due date falls in the given season. season: 'jan-…, Return set of bill IDs whose due date falls in the given season and year.…, Build sector-wise six-month season report rows. Returns (headers, detail_rows,…

### Community 18 - "NumberedCanvas"
Cohesion: 0.16
Nodes (7): Flowable, NumberedCanvas, _page_furniture(), _PageMark, A zero-height marker that reports the page it lands on. Placed at the head of a…, Canvas that stamps "Page X of Y" once the total is known. ReportLab streams…, Page-begin callback. Runs before the frame lays its flowables down, which is…

### Community 19 - "_register_table"
Cohesion: 0.15
Nodes (14): _column_extents(), _detail_widths(), _esc(), _index_flowables(), A detail table for the printed register. Two corrections on top of the shared…, Wrap only the long-text columns as Paragraphs. Matches what…, Longest value per column, used to size the columns and decide wrapping., Share the page across columns according to what they actually hold. Sizing off… (+6 more)

### Community 20 - "bill_list_zone_export_rows"
Cohesion: 0.50
Nodes (5): bill_list_zone_export_rows(), export_bill_list_zone(), export_zone_report_response(), get_zone_summary_data(), zone_sort_expr()

### Community 21 - "main"
Cohesion: 0.25
Nodes (8): main(), Self-check for the Handover Register join, filters, and snapshot lock. Run:…, read(), apply_filters(), _pick(), Parse a money cell tolerantly. Pulls the first number out rather than deleting…, First column whose normalised name matches one of *candidates*., _to_amount()

### Community 22 - "DataFrame"
Cohesion: 0.21
Nodes (17): build_sections(), build_sector_summary(), detail_rows(), export_handover(), handover_print(), is_commercial(), _numeric_amounts(), DataFrame (+9 more)

### Community 23 - "handover"
Cohesion: 0.17
Nodes (16): _app(), _gunzip(), handover(), _handover_dir(), handover_status(), _list_snapshots(), load_dataset(), Read an uploaded CSV/XLSX as text so connection numbers keep leading zeros. (+8 more)

### Community 24 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 25 - "export_consumer_report"
Cohesion: 0.18
Nodes (11): consumer_report_detail_records(), export_consumer_report(), _is_private_society_summary_row(), _load_consumer_rows_cache(), _load_consumer_summary_cache(), Return consumer connection records for a specific sector/locality/category with…, Load a previously saved consumer summary from disk. Returns (summary, filename,…, Load cached consumer individual connection rows. (+3 more)

### Community 29 - "_build_connection_rate_report"
Cohesion: 0.18
Nodes (16): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description() (+8 more)

### Community 31 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 33 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

## Knowledge Gaps
- **7 isolated node(s):** `$schema`, `maxDuration`, `code:block1 (/graphify . --update)`, `code:block2 (/graphify query "how does bill upload work")`, `code:bash (# Development server)` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `classify` to `data_comparison.py`, `main`, `audit_engine.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `audit_engine.py` to `classify`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `_GroupedPdfWrapper` connect `_GroupedPdfWrapper` to `app.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `ParagraphStyle` (e.g. with `build_arrears_pdf()` and `_report_pdf()`) actually correct?**
  _`ParagraphStyle` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `maxDuration`, `code:block1 (/graphify . --update)` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09615384615384616 - nodes in this community are weakly interconnected._
- **Should `DataFrame` be split into smaller, more focused modules?**
  _Cohesion score 0.09292929292929293 - nodes in this community are weakly interconnected._