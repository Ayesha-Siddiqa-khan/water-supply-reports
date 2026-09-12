# Graph Report - .  (2026-09-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 644 nodes · 1610 edges · 53 communities (43 shown, 10 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 52 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `769016e7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- DataFrame
- data_comparison.py
- arrears_analysis.py
- get_db
- app.py
- audit_engine.py
- summarize_dataframe
- handover.py
- _GroupedPdfWrapper
- _txt
- _render_page
- build_daily_staff_receive_report
- consumer_report
- import_bill_list_dataframe
- parse_number
- build_consumer_sector_remaining_report
- _build_new_connection_detail_report
- export_handover
- _register_table
- index
- allowed_file
- _build_connection_rate_report
- Agent Instructions
- export_consumer_report
- NumberedCanvas
- upload-progress.js
- _is_faulty_commercial_hussain_colony
- _normalize_rate_title
- _key_frame
- vercel.json
- check_handover.py
- Water Supply Report Application
- _numeric_amounts
- Claude Code CLI Prompt: Advanced Bill List Filters and Export
- DataFrame
- Series
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
- `arrears_analysis()` --indirect_call--> `ajax_error()`  [INFERRED]
  arrears_analysis.py → app.py
- `arrears_analysis()` --indirect_call--> `ajax_ok()`  [INFERRED]
  arrears_analysis.py → app.py
- `arrears_analysis()` --calls--> `allowed_file()`  [INFERRED]
  arrears_analysis.py → app.py
- `parse_register()` --calls--> `classify()`  [INFERRED]
  audit_engine.py → data_comparison.py
- `classify()` --indirect_call--> `_status_of()`  [INFERRED]
  data_comparison.py → handover.py

## Import Cycles
- None detected.

## Communities (53 total, 10 thin omitted)

### Community 0 - "DataFrame"
Cohesion: 0.08
Nodes (77): bill_income_category_export_rows(), bill_list_export_rows(), _bracket_rich_text(), build_connection_summary(), build_unpaid_amount_summary(), _card_rows_to_df(), _closest_staff_key(), commercial_daily_income_export_rows() (+69 more)

### Community 1 - "data_comparison.py"
Cohesion: 0.09
Nodes (42): active_figures(), _app(), build_comparison(), change_rows(), classify(), clear_result(), _column(), comparable() (+34 more)

### Community 2 - "arrears_analysis.py"
Cohesion: 0.11
Nodes (37): Any, _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+29 more)

### Community 3 - "get_db"
Cohesion: 0.09
Nodes (38): apply_manual_zone_overrides(), bill_list(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), clear_bill_list_data(), export_advanced_bills(), export_bill_list_zone() (+30 more)

### Community 4 - "app.py"
Cohesion: 0.07
Nodes (28): _build_arrear_export_rows(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), file_column_matcher(), file_merger(), fiscal_label_to_calendar_full_label(), fiscal_label_to_calendar_label(), format_calendar_month() (+20 more)

### Community 5 - "audit_engine.py"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 6 - "summarize_dataframe"
Cohesion: 0.19
Nodes (24): build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_income_category_summary(), build_monthly_rows(), build_private_society_mask() (+16 more)

### Community 7 - "handover.py"
Cohesion: 0.11
Nodes (27): _app(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path(), _gunzip(), handover() (+19 more)

### Community 8 - "_GroupedPdfWrapper"
Cohesion: 0.19
Nodes (11): _calc_col_widths(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), _GroupedPdfWrapper, Return sort key for zone ordering: A=1, B=2, C=3, Commercial=4, unknown=99., Generate a landscape PDF with one section per group showing detailed bill rows., Helper to write grouped PDF sections with smart pagination and staff zone…, Estimated mm needed for a group: heading + sub-lines + table header + body +… (+3 more)

### Community 9 - "_txt"
Cohesion: 0.13
Nodes (19): main(), Self-check for the Data Comparison page.  Run:  python check_data_comparison.py, read(), build_handover_dataset(), _canonical_labels(), canonicalise_groups(), drop_excluded_sectors(), _pick() (+11 more)

### Community 10 - "_render_page"
Cohesion: 0.20
Nodes (22): apply_filters(), build_sector_summary(), col_key(), detail_columns(), filter_label(), _finalize(), is_commercial(), load_dataset() (+14 more)

### Community 11 - "build_daily_staff_receive_report"
Cohesion: 0.13
Nodes (20): build_daily_staff_receive_report(), clean_cell(), clear_unmatched_log(), _deep_normalize_sector(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), get_unmatched_log() (+12 more)

### Community 12 - "consumer_report"
Cohesion: 0.18
Nodes (15): ajax_error(), ajax_ok(), arrear_calculator(), _clear_consumer_summary_cache(), consumer_report(), consumer_sector_remaining_report(), _filter_active_rows(), Display the combined Consumer Sector Remaining Report. Supports two upload… (+7 more)

### Community 13 - "import_bill_list_dataframe"
Cohesion: 0.15
Nodes (15): build_bill_key(), _dedupe_value(), drop_duplicate_bills(), fast_bill_no_key(), fast_upload_number(), fast_upload_text(), import_bill_list_dataframe(), infer_zone() (+7 more)

### Community 14 - "parse_number"
Cohesion: 0.15
Nodes (14): backfill_bill_arrears(), _bill_list_summary_from_rows(), _connection_rate_rows_from_payload(), is_large_pdf_text(), merge_sector_list_rows(), merge_sector_rows(), normalise_sector(), parse_number() (+6 more)

### Community 15 - "build_consumer_sector_remaining_report"
Cohesion: 0.19
Nodes (14): build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _clean_rate_type_name(), _is_extra_noor_mohalla_main_road_sector(), _is_extra_zain_city_13g_sector(), _is_faulty_empty_consumer_sector(), Build combined consumer sector + remaining amount rows. Joins consumer sector… (+6 more)

### Community 16 - "_build_new_connection_detail_report"
Cohesion: 0.21
Nodes (14): _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _load_new_connection_detail_cache(), _ncd_classification(), _ncd_decimal(), _ncd_int(), _ncd_load_file(), _ncd_parse_date() (+6 more)

### Community 17 - "export_handover"
Cohesion: 0.20
Nodes (10): build_sections(), detail_rows(), export_handover(), handover_print(), _page_furniture(), The one date the register carries.      A finalised record is dated when it wa, Page-begin callback.      Runs before the frame lays its flowables down, which, Split the register into printable blocks.      Ordinary sectors come first, se (+2 more)

### Community 18 - "_register_table"
Cohesion: 0.15
Nodes (14): _column_extents(), _detail_widths(), _esc(), _index_flowables(), A detail table for the printed register.      Two corrections on top of the sh, Wrap only the long-text columns as Paragraphs.      Matches what ``wrap_pdf_bo, Longest value per column, used to size the columns and decide wrapping., Share the page across columns according to what they actually hold.      Sizin (+6 more)

### Community 19 - "index"
Cohesion: 0.19
Nodes (13): build_dashboard_results(), daily_staff_receive(), index(), is_ajax(), _load_dashboard_results(), _load_results_cache(), Build the All Received Bills dashboard once and reuse it for the rendered page…, read_and_merge_uploaded_files() (+5 more)

### Community 20 - "allowed_file"
Cohesion: 0.21
Nodes (12): allowed_file(), _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows() (+4 more)

### Community 21 - "_build_connection_rate_report"
Cohesion: 0.23
Nodes (12): _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description(), _connection_rate_report_from_groups() (+4 more)

### Community 22 - "Agent Instructions"
Cohesion: 0.18
Nodes (10): Agent Instructions, Auto-Update on Changes, Commands, Development Guidelines, Graph Status, Graphify - Knowledge Graph, Key Architecture Nodes (from last graphify run), Ponytail - Lazy Senior Dev Mode (+2 more)

### Community 23 - "export_consumer_report"
Cohesion: 0.18
Nodes (11): consumer_report_detail_records(), export_consumer_report(), _is_private_society_summary_row(), _load_consumer_rows_cache(), _load_consumer_summary_cache(), Return consumer connection records for a specific sector/locality/category with…, Load a previously saved consumer summary from disk. Returns (summary, filename,…, Load cached consumer individual connection rows. (+3 more)

### Community 24 - "NumberedCanvas"
Cohesion: 0.22
Nodes (5): Flowable, NumberedCanvas, _PageMark, A zero-height marker that reports the page it lands on.      Placed at the hea, Canvas that stamps "Page X of Y" once the total is known.      ReportLab strea

### Community 25 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 26 - "_is_faulty_commercial_hussain_colony"
Cohesion: 0.28
Nodes (9): _classify_connection_status(), _is_faulty_commercial_hussain_colony(), _normalize_consumer_col(), _parse_consumer_csv(), Map each canonical key to the actual CSV column name that matched., Classify both 'Status' column values and 'Consumer Status' into…, Skip dummy/faulted Commercial Hussain Colony records that do not represent real…, Read uploaded CSV/XLSX and return (rows, errors). Uses flexible column matching… (+1 more)

### Community 27 - "_normalize_rate_title"
Cohesion: 0.33
Nodes (7): _add_rate_alias(), _connection_rate_lookup(), _load_rates_csv(), _normalize_rate_title(), Load rate data from the provided rates CSV or bundled rates.json. RATE SOURCE…, Canonical key for rate matching; tolerates case/spacing drift without changing…, Map known legacy consumer rate labels to the active rate title.

### Community 28 - "_key_frame"
Cohesion: 0.40
Nodes (5): _compose(), _conn_key(), _key_frame(), Series, Alphanumerics only, lower-cased, leading zeros removed.      Connection number

### Community 29 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 30 - "check_handover.py"
Cohesion: 0.67
Nodes (3): main(), Self-check for the Handover Register join, filters, and snapshot lock.  Run:, read()

### Community 31 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

### Community 32 - "_numeric_amounts"
Cohesion: 0.50
Nodes (4): _numeric_amounts(), Write money columns to Excel as numbers, not "13,040" text, so the     arrears, Parse a money cell tolerantly.      Pulls the first number out rather than del, _to_amount()

## Knowledge Gaps
- **16 isolated node(s):** `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status`, `When Working on This Project`, `Auto-Update on Changes` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `data_comparison.py` to `_txt`, `audit_engine.py`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `audit_engine.py` to `data_comparison.py`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `_GroupedPdfWrapper` connect `_GroupedPdfWrapper` to `app.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `ParagraphStyle` (e.g. with `build_arrears_pdf()` and `_report_pdf()`) actually correct?**
  _`ParagraphStyle` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `DataFrame` be split into smaller, more focused modules?**
  _Cohesion score 0.07552973342447027 - nodes in this community are weakly interconnected._
- **Should `data_comparison.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09080841638981174 - nodes in this community are weakly interconnected._