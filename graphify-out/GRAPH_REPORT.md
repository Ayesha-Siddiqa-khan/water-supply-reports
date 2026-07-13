# Graph Report - E:\github\water suppy report\water suppy report  (2026-07-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 340 nodes · 890 edges · 19 communities
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 16 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c26aea96`
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

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 28 edges
2. `get_db()` - 26 edges
3. `init_bill_list_db()` - 22 edges
4. `download_card()` - 21 edges
5. `export_six_month_pitch()` - 18 edges
6. `Base Template` - 16 edges
7. `parse_number()` - 16 edges
8. `build_daily_staff_receive_report()` - 16 edges
9. `summarize_dataframe()` - 16 edges
10. `_GroupedPdfWrapper` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Advanced Bill Filters Feature Prompt` --conceptually_related_to--> `Bill List Export Endpoints (zones/sectors/staff/unpaid/zone/staff/six-month/season)`  [INFERRED]
  instruction.md.md → templates/bill_list.html
- `Advanced Bill Filters Feature Prompt` --references--> `Bills Reports Page`  [EXTRACTED]
  instruction.md.md → templates/bill_list.html
- `Arrear Calculator Page` --semantically_similar_to--> `Consumer Sector Report Page`  [INFERRED] [semantically similar]
  templates/arrear_calculator.html → templates/consumer_report.html
- `File Merger Page` --references--> `Flask route: file_merger`  [EXTRACTED]
  templates/file_merger.html → templates/base.html
- `Arrear Calculator Page` --extends--> `Base Template`  [EXTRACTED]
  templates/arrear_calculator.html → templates/base.html

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Reports-section pages extending base.html with shared sidebar nav** — tpl_index, tpl_bill_list, tpl_daily, tpl_consumer, tpl_consumer_remaining, tpl_arrear, tpl_base [INFERRED]
- **Client-side-only file tools (no server route, use browser CDN libraries)** — tpl_fcm, tpl_merge, ext_sheetjs, ext_pdflib [INFERRED]
- **Report pages with PDF/CSV/XLSX export endpoint families** — tpl_index, tpl_bill_list, tpl_consumer, tpl_consumer_remaining, tpl_daily, tpl_arrear, exp_index, exp_bill_list, exp_consumer, exp_consumer_remaining, exp_daily, exp_arrear [INFERRED]

## Communities (19 total, 0 thin omitted)

### Community 0 - "BytesIO"
Cohesion: 0.08
Nodes (50): bill_list_export_rows(), _bracket_rich_text(), build_connection_summary(), _calc_col_widths(), _card_rows_to_df(), commercial_daily_income_export_rows(), daily_staff_receive_export_response(), daily_staff_receive_export_tables() (+42 more)

### Community 1 - "app.py"
Cohesion: 0.06
Nodes (51): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), clean_cell(), _closest_staff_key() (+43 more)

### Community 2 - "DataFrame"
Cohesion: 0.07
Nodes (53): _bill_list_summary_from_rows(), build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report() (+45 more)

### Community 3 - "consumer_report"
Cohesion: 0.07
Nodes (50): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _classify_connection_status() (+42 more)

### Community 4 - "get_db"
Cohesion: 0.08
Nodes (48): apply_manual_zone_overrides(), backfill_bill_arrears(), bill_list(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data() (+40 more)

### Community 5 - "Base Template"
Cohesion: 0.09
Nodes (32): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database, Advanced Bill Filters Feature Prompt, Portable App README (root), Python Dependencies (requirements.txt), Export Endpoints: export_arrear_calculator (+24 more)

### Community 6 - "upload-progress.js"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 7 - "export_arrear_calculator"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list.      Fixed column orde, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 8 - "export_advanced_bills"
Cohesion: 0.33
Nodes (7): export_advanced_bills(), generate_zip_of_group_pdfs(), group_bills(), Return sort key for zone ordering: A=1, B=2, C=3, Commercial=4, unknown=99., Group bills by sector/zone/staff.      Returns:       - sector/zone: list of, sanitize_filename(), _zone_sort_key()

### Community 9 - "vercel.json"
Cohesion: 0.40
Nodes (4): maxDuration, functions, app.py, $schema

## Knowledge Gaps
- **7 isolated node(s):** `Export Endpoints: export_consumer_report`, `Export Endpoints: export_consumer_sector_remaining`, `Export Endpoints: export_daily_staff_receive`, `Export Endpoints: export_arrear_calculator`, `Export Endpoints: download_file / download_card` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_GroupedPdfWrapper` connect `BytesIO` to `app.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `generate_grouped_advanced_pdf()` connect `BytesIO` to `app.py`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Why does `fmt()` connect `BytesIO` to `export_advanced_bills`, `app.py`, `DataFrame`, `get_db`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **What connects `Export Endpoints: export_consumer_report`, `Export Endpoints: export_consumer_sector_remaining`, `Export Endpoints: export_daily_staff_receive` to the rest of the system?**
  _67 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `BytesIO` be split into smaller, more focused modules?**
  _Cohesion score 0.08469945355191257 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06015037593984962 - nodes in this community are weakly interconnected._
- **Should `DataFrame` be split into smaller, more focused modules?**
  _Cohesion score 0.06894049346879536 - nodes in this community are weakly interconnected._