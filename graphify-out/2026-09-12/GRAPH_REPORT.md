# Graph Report - .  (2026-09-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 642 nodes · 1584 edges · 46 communities (38 shown, 8 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 53 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f218831e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BytesIO
- DataFrame
- get_db
- arrears_analysis.py
- data_comparison.py
- app.py
- audit_engine.py
- build_consumer_sector_remaining_report
- _GroupedPdfWrapper
- _txt
- _render_page
- consumer_report
- _build_connection_rate_report
- handover.py
- parse_number
- NumberedCanvas
- _register_table
- _draw_watermark
- Agent Instructions
- _build_dnc_register_report
- upload-progress.js
- _filter_active_rows
- _numeric_amounts
- export_arrear_calculator
- vercel.json
- check_handover.py
- Water Supply Report Application
- Claude Code CLI Prompt: Advanced Bill List Filters and Export
- pdf-lib (CDN library)
- SheetJS (CDN library)
- code:block1 (/graphify . --update)
- code:block2 (/graphify query "how does bill upload work")
- code:bash (# Development server)
- code:text (You are working on an existing running application. This app)
- code:bash (claude)
- canonicalise_groups

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

## Communities (46 total, 8 thin omitted)

### Community 0 - "BytesIO"
Cohesion: 0.07
Nodes (73): bill_income_category_export_rows(), bill_list_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), _bracket_rich_text(), build_connection_summary(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths() (+65 more)

### Community 1 - "DataFrame"
Cohesion: 0.09
Nodes (49): build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report(), build_income_category_summary() (+41 more)

### Community 2 - "get_db"
Cohesion: 0.07
Nodes (48): apply_manual_zone_overrides(), bill_list(), bill_list_sector_seasonly_export_rows(), build_unpaid_amount_summary(), clean_cell(), clear_bill_list_data(), _deep_normalize_sector(), export_sectors_summary() (+40 more)

### Community 3 - "arrears_analysis.py"
Cohesion: 0.11
Nodes (38): Any, _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+30 more)

### Community 4 - "data_comparison.py"
Cohesion: 0.09
Nodes (42): active_figures(), _app(), build_comparison(), change_rows(), classify(), clear_result(), _column(), comparable() (+34 more)

### Community 5 - "app.py"
Cohesion: 0.08
Nodes (31): _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), download_file(), export_bill_list_zone(), export_daily_staff_receive(), export_daily_staff_receive_summary_pdf(), file_column_matcher(), file_merger() (+23 more)

### Community 6 - "audit_engine.py"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 7 - "build_consumer_sector_remaining_report"
Cohesion: 0.11
Nodes (30): build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _classify_connection_status(), _clean_rate_type_name(), consumer_sector_remaining_report(), export_consumer_report(), _is_extra_noor_mohalla_main_road_sector() (+22 more)

### Community 8 - "_GroupedPdfWrapper"
Cohesion: 0.14
Nodes (17): _calc_col_widths(), export_advanced_bills(), export_advanced_bills_response(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), generate_zip_of_group_pdfs(), group_bills(), _GroupedPdfWrapper (+9 more)

### Community 9 - "_txt"
Cohesion: 0.12
Nodes (20): main(), Self-check for the Data Comparison page.  Run:  python check_data_comparison.py, read(), build_handover_dataset(), _compose(), _conn_key(), drop_excluded_sectors(), _key_frame() (+12 more)

### Community 10 - "_render_page"
Cohesion: 0.14
Nodes (29): apply_filters(), build_sections(), build_sector_summary(), col_key(), detail_columns(), detail_rows(), export_handover(), filter_label() (+21 more)

### Community 11 - "consumer_report"
Cohesion: 0.14
Nodes (22): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), build_dashboard_results(), _clear_consumer_summary_cache(), consumer_report(), daily_staff_receive() (+14 more)

### Community 12 - "_build_connection_rate_report"
Cohesion: 0.15
Nodes (19): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description() (+11 more)

### Community 13 - "handover.py"
Cohesion: 0.16
Nodes (21): _app(), _draw_signature_band(), _gunzip(), handover(), _handover_dir(), handover_status(), _list_snapshots(), load_dataset() (+13 more)

### Community 14 - "parse_number"
Cohesion: 0.15
Nodes (14): backfill_bill_arrears(), _bill_list_summary_from_rows(), _connection_rate_rows_from_payload(), is_large_pdf_text(), merge_sector_list_rows(), merge_sector_rows(), normalise_sector(), parse_number() (+6 more)

### Community 15 - "NumberedCanvas"
Cohesion: 0.16
Nodes (7): Flowable, NumberedCanvas, _page_furniture(), _PageMark, A zero-height marker that reports the page it lands on.      Placed at the hea, Canvas that stamps "Page X of Y" once the total is known.      ReportLab strea, Page-begin callback.      Runs before the frame lays its flowables down, which

### Community 16 - "_register_table"
Cohesion: 0.15
Nodes (14): _column_extents(), _detail_widths(), _esc(), _index_flowables(), A detail table for the printed register.      Two corrections on top of the sh, Wrap only the long-text columns as Paragraphs.      Matches what ``wrap_pdf_bo, Longest value per column, used to size the columns and decide wrapping., Share the page across columns according to what they actually hold.      Sizin (+6 more)

### Community 17 - "_draw_watermark"
Cohesion: 0.29
Nodes (7): _draw_ring_text(), _draw_star(), _draw_watermark(), _emblem_path(), The municipal emblem shipped in static/, or None if it is absent., Set text right around the circle, evenly spaced with no gap.      The legend i, A round official stamp, faint, centred, behind the page content.

### Community 18 - "Agent Instructions"
Cohesion: 0.18
Nodes (10): Agent Instructions, Auto-Update on Changes, Commands, Development Guidelines, Graph Status, Graphify - Knowledge Graph, Key Architecture Nodes (from last graphify run), Ponytail - Lazy Senior Dev Mode (+2 more)

### Community 19 - "_build_dnc_register_report"
Cohesion: 0.24
Nodes (11): _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows(), _dnc_split_sector_locality() (+3 more)

### Community 20 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 21 - "_filter_active_rows"
Cohesion: 0.20
Nodes (10): consumer_report_detail_records(), _filter_active_rows(), _is_private_society_summary_row(), _load_consumer_rows_cache(), Return consumer connection records for a specific sector/locality/category with, Load cached consumer individual connection rows., Return a copy of `summary` with all rows having zero active     connections remo, Return True for domestic private-society rows shown in their own tab. (+2 more)

### Community 22 - "_numeric_amounts"
Cohesion: 0.50
Nodes (4): _numeric_amounts(), Write money columns to Excel as numbers, not "13,040" text, so the     arrears, Parse a money cell tolerantly.      Pulls the first number out rather than del, _to_amount()

### Community 23 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list.      Fixed column order:, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 24 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 25 - "check_handover.py"
Cohesion: 0.67
Nodes (3): main(), Self-check for the Handover Register join, filters, and snapshot lock.  Run:, read()

### Community 26 - "Water Supply Report Application"
Cohesion: 0.50
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

### Community 45 - "canonicalise_groups"
Cohesion: 0.50
Nodes (4): _canonical_labels(), canonicalise_groups(), Map visually identical labels onto one spelling.      Sector and locality name, Collapse duplicate Sector/Locality spellings before anything groups on them.

## Knowledge Gaps
- **16 isolated node(s):** `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status`, `When Working on This Project`, `Auto-Update on Changes` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `data_comparison.py` to `_txt`, `canonicalise_groups`, `audit_engine.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `audit_engine.py` to `data_comparison.py`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `_GroupedPdfWrapper` connect `_GroupedPdfWrapper` to `app.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `ParagraphStyle` (e.g. with `build_arrears_pdf()` and `_report_pdf()`) actually correct?**
  _`ParagraphStyle` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status` to the rest of the system?**
  _170 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `BytesIO` be split into smaller, more focused modules?**
  _Cohesion score 0.07039573820395738 - nodes in this community are weakly interconnected._
- **Should `DataFrame` be split into smaller, more focused modules?**
  _Cohesion score 0.08503401360544217 - nodes in this community are weakly interconnected._