# Graph Report - .  (2026-07-25)

## Corpus Check
- Large corpus: 81 files · ~1,271,905 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 499 nodes · 1047 edges · 43 communities (33 shown, 10 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Audit & Bill Export Rows|Audit & Bill Export Rows]]
- [[_COMMUNITY_Report Builders & Upload Plumbing|Report Builders & Upload Plumbing]]
- [[_COMMUNITY_Bill List & Zone Management|Bill List & Zone Management]]
- [[_COMMUNITY_Grouped PDF Generation|Grouped PDF Generation]]
- [[_COMMUNITY_Staff Assignment & Daily Receiving|Staff Assignment & Daily Receiving]]
- [[_COMMUNITY_App Core & Caching|App Core & Caching]]
- [[_COMMUNITY_Commercial Budget Debug Scripts|Commercial Budget Debug Scripts]]
- [[_COMMUNITY_Data Audit Engine|Data Audit Engine]]
- [[_COMMUNITY_Commercial & Private Society Masks|Commercial & Private Society Masks]]
- [[_COMMUNITY_Connection Rate Lookup|Connection Rate Lookup]]
- [[_COMMUNITY_Commercial Locality Debug|Commercial Locality Debug]]
- [[_COMMUNITY_Commercial Budget Tests|Commercial Budget Tests]]
- [[_COMMUNITY_New Connection Detail Report|New Connection Detail Report]]
- [[_COMMUNITY_CSV Parsing Debug|CSV Parsing Debug]]
- [[_COMMUNITY_Rate Match Tests|Rate Match Tests]]
- [[_COMMUNITY_Dataframe Import & Dedupe|Dataframe Import & Dedupe]]
- [[_COMMUNITY_DNC Register|DNC Register]]
- [[_COMMUNITY_Upload Progress UI|Upload Progress UI]]
- [[_COMMUNITY_New Connection PDF Export|New Connection PDF Export]]
- [[_COMMUNITY_Arrear Calculator Export|Arrear Calculator Export]]
- [[_COMMUNITY_Commercial CSV Debug|Commercial CSV Debug]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 35 edges
2. `get_db()` - 27 edges
3. `init_bill_list_db()` - 23 edges
4. `download_card()` - 20 edges
5. `parse_number()` - 16 edges
6. `summarize_dataframe()` - 16 edges
7. `index()` - 16 edges
8. `_GroupedPdfWrapper` - 15 edges
9. `export_six_month_pitch()` - 15 edges
10. `consumer_report()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `fmt_staff_name()` --calls--> `_normalize_staff_name()`  [EXTRACTED]
  app.py → app.py  _Bridges community 4 → community 2_
- `daily_staff_receive_export_tables()` --calls--> `fmt_staff_name()`  [EXTRACTED]
  app.py → app.py  _Bridges community 2 → community 0_
- `bill_list()` --calls--> `allowed_file()`  [EXTRACTED]
  app.py → app.py  _Bridges community 1 → community 2_
- `dnc_register()` --calls--> `allowed_file()`  [EXTRACTED]
  app.py → app.py  _Bridges community 1 → community 16_
- `_build_new_connection_detail_report()` --calls--> `allowed_file()`  [EXTRACTED]
  app.py → app.py  _Bridges community 1 → community 12_

## Hyperedges (group relationships)
- **Reports-section pages extending base.html with shared sidebar nav** — tpl_index, tpl_bill_list, tpl_daily, tpl_consumer, tpl_consumer_remaining, tpl_arrear, tpl_base [INFERRED]
- **Client-side-only file tools (no server route, use browser CDN libraries)** — tpl_fcm, tpl_merge, ext_sheetjs, ext_pdflib [INFERRED]
- **Report pages with PDF/CSV/XLSX export endpoint families** — tpl_index, tpl_bill_list, tpl_consumer, tpl_consumer_remaining, tpl_daily, tpl_arrear, exp_index, exp_bill_list, exp_consumer, exp_consumer_remaining, exp_daily, exp_arrear [INFERRED]

## Communities (43 total, 10 thin omitted)

### Community 0 - "Audit & Bill Export Rows"
Cohesion: 0.05
Nodes (61): _audit_cell(), _audit_col_widths(), _audit_pdf(), _audit_report_rows(), _audit_structural_rows(), bill_income_category_export_rows(), bill_list_export_rows(), _bill_list_summary_from_rows() (+53 more)

### Community 1 - "Report Builders & Upload Plumbing"
Cohesion: 0.06
Nodes (57): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), _build_connection_rate_report(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), build_dashboard_results() (+49 more)

### Community 2 - "Bill List & Zone Management"
Cohesion: 0.08
Nodes (48): apply_manual_zone_overrides(), backfill_bill_arrears(), bill_list(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data() (+40 more)

### Community 3 - "Grouped PDF Generation"
Cohesion: 0.14
Nodes (17): _calc_col_widths(), export_advanced_bills(), export_advanced_bills_response(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), generate_zip_of_group_pdfs(), group_bills(), _GroupedPdfWrapper (+9 more)

### Community 4 - "Staff Assignment & Daily Receiving"
Cohesion: 0.09
Nodes (28): build_daily_staff_receive_report(), clean_cell(), clear_unmatched_log(), _closest_staff_key(), _deep_normalize_sector(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule() (+20 more)

### Community 5 - "App Core & Caching"
Cohesion: 0.11
Nodes (14): build_bill_key(), build_receipt_monthly_rows(), clean_amount_value(), _dedupe_value(), export_bill_list_zone(), export_table_response(), export_zone_report_response(), file_merger() (+6 more)

### Community 6 - "Commercial Budget Debug Scripts"
Cohesion: 0.09
Nodes (19): annual, bakeriesStats, commercialSectors, csv, fields, fs, headers, lines (+11 more)

### Community 7 - "Data Audit Engine"
Cohesion: 0.13
Nodes (22): _blank_totals(), build_audit_report(), _corrections_for(), _default_classify(), _hidden_arrear(), load_folder(), _money(), _pair() (+14 more)

### Community 8 - "Commercial & Private Society Masks"
Cohesion: 0.16
Nodes (22): build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_income_category_summary(), build_monthly_rows(), build_private_society_mask() (+14 more)

### Community 9 - "Connection Rate Lookup"
Cohesion: 0.12
Nodes (18): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description(), _connection_rate_lookup() (+10 more)

### Community 10 - "Commercial Locality Debug"
Cohesion: 0.11
Nodes (14): budget, commLocalities, csv, fields, fs, lines, locality, period (+6 more)

### Community 11 - "Commercial Budget Tests"
Cohesion: 0.12
Nodes (13): budget, commercialLocalityMap, csv, fields, fs, line, lines, period (+5 more)

### Community 12 - "New Connection Detail Report"
Cohesion: 0.17
Nodes (16): _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _load_new_connection_detail_cache(), _ncd_classification(), _ncd_decimal(), _ncd_financial_year(), _ncd_int(), _ncd_load_file() (+8 more)

### Community 13 - "CSV Parsing Debug"
Cohesion: 0.12
Nodes (14): consumerStatusIdx, csv, fields, fs, headers, lines, localityIdx, rates (+6 more)

### Community 14 - "Rate Match Tests"
Cohesion: 0.14
Nodes (12): csv, fields, fs, line, lines, period, rateLookup, rates (+4 more)

### Community 15 - "Dataframe Import & Dedupe"
Cohesion: 0.18
Nodes (12): drop_duplicate_bills(), fast_bill_no_key(), fast_upload_number(), fast_upload_text(), import_bill_list_dataframe(), infer_zone(), normalize_column_name(), normalize_dataframe() (+4 more)

### Community 16 - "DNC Register"
Cohesion: 0.24
Nodes (11): _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), dnc_register(), _dnc_report_rows(), _dnc_split_sector_locality() (+3 more)

### Community 17 - "Upload Progress UI"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 18 - "New Connection PDF Export"
Cohesion: 0.31
Nodes (10): export_new_connection_detail(), _ncd_annual_payload(), _ncd_annual_pdf(), _ncd_detail_pdf(), _ncd_export_rows(), _ncd_general_category_table(), _ncd_general_pdf(), _ncd_pdf_col_widths() (+2 more)

### Community 19 - "Arrear Calculator Export"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list.      Fixed column orde, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 20 - "Commercial CSV Debug"
Cohesion: 0.33
Nodes (4): fields, fs, headers, lines

### Community 21 - "Community 21"
Cohesion: 0.5
Nodes (4): _connection_rate_rows_from_payload(), export_connection_rate_report(), generate_connection_rate_pdf(), Print-friendly Consumer Report rate summary with wrapped descriptions.

### Community 22 - "Community 22"
Cohesion: 0.5
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

## Knowledge Gaps
- **155 isolated node(s):** `Aggressively normalize a sector/locality name for robust matching.`, `Extract significant keywords from a sector/locality name.`, `Return display name: paired staff on separate lines, else as-is.`, `Like fmt_staff_name but returns HTML with <br> for display.`, `Remove duplicate uploaded bills without collapsing different bills for one conne` (+150 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_GroupedPdfWrapper` connect `Grouped PDF Generation` to `App Core & Caching`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `fmt()` connect `Audit & Bill Export Rows` to `Bill List & Zone Management`, `Grouped PDF Generation`, `Staff Assignment & Daily Receiving`, `App Core & Caching`, `Commercial & Private Society Masks`, `DNC Register`, `New Connection PDF Export`, `Community 21`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Why does `_get_season_bill_ids()` connect `Bill List & Zone Management` to `Report Builders & Upload Plumbing`, `App Core & Caching`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **What connects `Aggressively normalize a sector/locality name for robust matching.`, `Extract significant keywords from a sector/locality name.`, `Return display name: paired staff on separate lines, else as-is.` to the rest of the system?**
  _155 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Audit & Bill Export Rows` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Report Builders & Upload Plumbing` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._
- **Should `Bill List & Zone Management` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._