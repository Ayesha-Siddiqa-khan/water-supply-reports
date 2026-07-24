# Graph Report - water suppy report  (2026-07-24)

## Corpus Check
- 29 files · ~91,642 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 392 nodes · 1006 edges · 29 communities (26 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2d3a1ddc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- BytesIO
- app.py
- DataFrame
- consumer_report
- get_db
- Base Template
- upload-progress.js
- export_arrear_calculator
- export_advanced_bills
- vercel.json
- Agent Instructions
- Claude Code CLI Prompt: Advanced Bill List Filters and Export
- Advanced Bill Filters Feature Prompt
- match_staff_assignment
- consumer_report_script_1.js
- _build_connection_rate_report
- export_consumer_report
- _normalize_rate_title
- export_arrear_calculator
- _normalize_consumer_col

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 31 edges
2. `get_db()` - 26 edges
3. `init_bill_list_db()` - 22 edges
4. `download_card()` - 21 edges
5. `export_six_month_pitch()` - 18 edges
6. `summarize_dataframe()` - 17 edges
7. `parse_number()` - 16 edges
8. `build_daily_staff_receive_report()` - 16 edges
9. `Base Template` - 16 edges
10. `_GroupedPdfWrapper` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Arrear Calculator Page` --semantically_similar_to--> `Consumer Sector Report Page`  [INFERRED] [semantically similar]
  templates/arrear_calculator.html → templates/consumer_report.html
- `File Merger Page` --references--> `Flask route: file_merger`  [EXTRACTED]
  templates/file_merger.html → templates/base.html
- `Arrear Calculator Page` --extends--> `Base Template`  [EXTRACTED]
  templates/arrear_calculator.html → templates/base.html
- `Bills Reports Page` --extends--> `Base Template`  [EXTRACTED]
  templates/bill_list.html → templates/base.html
- `Consumer Sector Report Page` --extends--> `Base Template`  [EXTRACTED]
  templates/consumer_report.html → templates/base.html

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Reports-section pages extending base.html with shared sidebar nav** — tpl_index, tpl_bill_list, tpl_daily, tpl_consumer, tpl_consumer_remaining, tpl_arrear, tpl_base [INFERRED]
- **Client-side-only file tools (no server route, use browser CDN libraries)** — tpl_fcm, tpl_merge, ext_sheetjs, ext_pdflib [INFERRED]
- **Report pages with PDF/CSV/XLSX export endpoint families** — tpl_index, tpl_bill_list, tpl_consumer, tpl_consumer_remaining, tpl_daily, tpl_arrear, exp_index, exp_bill_list, exp_consumer, exp_consumer_remaining, exp_daily, exp_arrear [INFERRED]

## Communities (29 total, 3 thin omitted)

### Community 0 - "BytesIO"
Cohesion: 0.07
Nodes (65): bill_list_export_rows(), _bracket_rich_text(), build_connection_summary(), _calc_col_widths(), _card_rows_to_df(), commercial_daily_income_export_rows(), daily_staff_receive_export_response(), daily_staff_receive_export_tables() (+57 more)

### Community 1 - "app.py"
Cohesion: 0.07
Nodes (52): apply_manual_zone_overrides(), bill_list(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data(), _closest_staff_key() (+44 more)

### Community 2 - "DataFrame"
Cohesion: 0.10
Nodes (41): build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_dashboard_results(), build_monthly_rows() (+33 more)

### Community 3 - "consumer_report"
Cohesion: 0.10
Nodes (15): _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), download_file(), export_daily_staff_receive(), export_daily_staff_receive_summary_pdf(), file_column_matcher(), fiscal_label_to_calendar_full_label(), fiscal_label_to_calendar_label() (+7 more)

### Community 4 - "get_db"
Cohesion: 0.29
Nodes (10): _build_new_connection_detail_report(), _ncd_classification(), _ncd_decimal(), _ncd_int(), _ncd_load_file(), _ncd_parse_date(), _ncd_recalculate(), _ncd_year_from_source() (+2 more)

### Community 5 - "Base Template"
Cohesion: 0.09
Nodes (31): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database, Portable App README (root), Python Dependencies (requirements.txt), Export Endpoints: export_arrear_calculator, Bill List Export Endpoints (zones/sectors/staff/unpaid/zone/staff/six-month/season) (+23 more)

### Community 6 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 7 - "export_arrear_calculator"
Cohesion: 0.06
Nodes (53): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _classify_connection_status() (+45 more)

### Community 8 - "export_advanced_bills"
Cohesion: 0.27
Nodes (10): clean_cell(), _deep_normalize_sector(), _keyword_set(), _levenshtein(), load_alias_rules(), match_by_alias(), match_key(), match_staff_assignment() (+2 more)

### Community 9 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

### Community 19 - "Agent Instructions"
Cohesion: 0.18
Nodes (10): Agent Instructions, Auto-Update on Changes, Commands, Development Guidelines, Graph Status, Graphify - Knowledge Graph, Key Architecture Nodes (from last graphify run), Ponytail - Lazy Senior Dev Mode (+2 more)

### Community 22 - "match_staff_assignment"
Cohesion: 0.15
Nodes (14): backfill_bill_arrears(), _bill_list_summary_from_rows(), _connection_rate_rows_from_payload(), is_large_pdf_text(), merge_sector_list_rows(), merge_sector_rows(), normalise_sector(), parse_number() (+6 more)

### Community 23 - "consumer_report_script_1.js"
Cohesion: 0.40
Nodes (6): fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), _normalize_sector_locality(), _normalize_staff_name(), Like fmt_staff_name but returns HTML with <br> for display.

### Community 24 - "_build_connection_rate_report"
Cohesion: 0.16
Nodes (18): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description() (+10 more)

### Community 25 - "export_consumer_report"
Cohesion: 0.40
Nodes (5): build_daily_staff_receive_report(), clear_unmatched_log(), get_unmatched_log(), infer_zone(), load_staff_assignment_rows()

### Community 26 - "_normalize_rate_title"
Cohesion: 0.67
Nodes (4): _clear_new_connection_detail_cache(), _load_new_connection_detail_cache(), new_connection_detail(), _save_new_connection_detail_cache()

### Community 27 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list.      Fixed column orde, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

## Knowledge Gaps
- **18 isolated node(s):** `$schema`, `maxDuration`, `Ponytail - Lazy Senior Dev Mode`, `Project Overview`, `Graph Status` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_GroupedPdfWrapper` connect `BytesIO` to `consumer_report`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `generate_grouped_advanced_pdf()` connect `BytesIO` to `consumer_report`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `_get_season_bill_ids()` connect `app.py` to `consumer_report`, `export_arrear_calculator`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **What connects `Aggressively normalize a sector/locality name for robust matching.`, `Extract significant keywords from a sector/locality name.`, `Return display name: paired staff on separate lines, else as-is.` to the rest of the system?**
  _84 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `BytesIO` be split into smaller, more focused modules?**
  _Cohesion score 0.06596491228070175 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07088989441930618 - nodes in this community are weakly interconnected._
- **Should `DataFrame` be split into smaller, more focused modules?**
  _Cohesion score 0.10121951219512196 - nodes in this community are weakly interconnected._