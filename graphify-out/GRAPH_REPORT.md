# Graph Report - .  (2026-07-10)

## Corpus Check
- Large corpus: 75 files · ~1,248,000 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 462 nodes · 895 edges · 29 communities (28 shown, 1 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Core App & Bill Builders|Core App & Bill Builders]]
- [[_COMMUNITY_Report Routes & Dashboard|Report Routes & Dashboard]]
- [[_COMMUNITY_Bill List Exports|Bill List Exports]]
- [[_COMMUNITY_Commercial & Daily Reports|Commercial & Daily Reports]]
- [[_COMMUNITY_App Overview & Dependencies|App Overview & Dependencies]]
- [[_COMMUNITY_Water Report Data Schema|Water Report Data Schema]]
- [[_COMMUNITY_Advanced Bill PDF Export|Advanced Bill PDF Export]]
- [[_COMMUNITY_Budget Calculation (JS)|Budget Calculation (JS)]]
- [[_COMMUNITY_Commercial Budget Debug (JS)|Commercial Budget Debug (JS)]]
- [[_COMMUNITY_Commercial Budget Tests (JS)|Commercial Budget Tests (JS)]]
- [[_COMMUNITY_CSV Parsing Debug (JS)|CSV Parsing Debug (JS)]]
- [[_COMMUNITY_Rate Matching (JS)|Rate Matching (JS)]]
- [[_COMMUNITY_Sector Normalization & Merge|Sector Normalization & Merge]]
- [[_COMMUNITY_Upload Progress UI (JS)|Upload Progress UI (JS)]]
- [[_COMMUNITY_Bundled Dependencies|Bundled Dependencies]]
- [[_COMMUNITY_Commercial CSV Debug 2 (JS)|Commercial CSV Debug 2 (JS)]]
- [[_COMMUNITY_UI Screenshots & Flow|UI Screenshots & Flow]]
- [[_COMMUNITY_Rate Alias Normalization|Rate Alias Normalization]]
- [[_COMMUNITY_Setuptools Vendored|Setuptools Vendored]]

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 27 edges
2. `get_db()` - 26 edges
3. `init_bill_list_db()` - 22 edges
4. `DateWise Water Supply Report` - 21 edges
5. `download_card()` - 19 edges
6. `Base Template` - 16 edges
7. `parse_number()` - 15 edges
8. `_GroupedPdfWrapper` - 15 edges
9. `export_six_month_pitch()` - 15 edges
10. `consumer_sector_remaining_report()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Consumer Report - After Upload` --conceptually_related_to--> `Test 04 - Report With Data`  [AMBIGUOUS]
  consumer-report-after-upload.png → test-04-report-with-data.png
- `Advanced Bill Filters Feature Prompt` --conceptually_related_to--> `Bill List Export Endpoints (zones/sectors/staff/unpaid/zone/staff/six-month/season)`  [INFERRED]
  instruction.md.md → templates/bill_list.html
- `Portable App README (root)` --semantically_similar_to--> `Portable App README (dist)`  [EXTRACTED] [semantically similar]
  PORTABLE_APP_README.txt → WaterSupplyReport-Portable/README.txt
- `Consumer Report - Initial State` --precedes--> `Consumer Report - After Upload`  [INFERRED]
  consumer-report-initial.png → consumer-report-after-upload.png
- `Test 01 - Page Loaded` --precedes--> `Test 02 - Page Ready`  [INFERRED]
  test-01-page-loaded.png → test-02-page-ready.png

## Hyperedges (group relationships)
- **Reports-section pages extending base.html with shared sidebar nav** — tpl_index, tpl_bill_list, tpl_daily, tpl_consumer, tpl_consumer_remaining, tpl_arrear, tpl_base [INFERRED]
- **Client-side-only file tools (no server route, use browser CDN libraries)** — tpl_fcm, tpl_merge, ext_sheetjs, ext_pdflib [INFERRED]
- **Report pages with PDF/CSV/XLSX export endpoint families** — tpl_index, tpl_bill_list, tpl_consumer, tpl_consumer_remaining, tpl_daily, tpl_arrear, exp_index, exp_bill_list, exp_consumer, exp_consumer_remaining, exp_daily, exp_arrear [INFERRED]
- **Upload to Report User Flow** — img_test_01_page_loaded, img_test_02_page_ready, img_test_03_after_upload, img_test_04_report_with_data [INFERRED 0.70]

## Communities (29 total, 1 thin omitted)

### Community 0 - "Core App & Bill Builders"
Cohesion: 0.05
Nodes (73): apply_manual_zone_overrides(), _bracket_rich_text(), _build_arrear_export_rows(), build_bill_key(), build_connection_summary(), build_receipt_monthly_rows(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths() (+65 more)

### Community 1 - "Report Routes & Dashboard"
Cohesion: 0.06
Nodes (58): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), bill_list(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), build_dashboard_results() (+50 more)

### Community 2 - "Bill List Exports"
Cohesion: 0.11
Nodes (43): bill_list_export_rows(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_unpaid_amount_summary(), clear_bill_list_data(), export_bill_list(), export_bill_list_staff() (+35 more)

### Community 3 - "Commercial & Daily Reports"
Cohesion: 0.08
Nodes (37): build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report(), build_monthly_rows(), clean_cell() (+29 more)

### Community 4 - "App Overview & Dependencies"
Cohesion: 0.09
Nodes (34): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database, Application Launch Command, Advanced Bill Filters Feature Prompt, Portable App README (root), Portable App README (dist) (+26 more)

### Community 5 - "Water Report Data Schema"
Cohesion: 0.08
Nodes (33): Arrears (Bill Type), Regular (Bill Type), Water Domestic 1/2 (Connection Type), Date Coverage (2024-2026), DateWise Water Supply Report, After Due Date (Amount), Amount Received, Arrears (+25 more)

### Community 6 - "Advanced Bill PDF Export"
Cohesion: 0.14
Nodes (18): _calc_col_widths(), export_advanced_bills(), export_advanced_bills_response(), generate_advanced_filtered_pdf(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), generate_zip_of_group_pdfs(), group_bills() (+10 more)

### Community 7 - "Budget Calculation (JS)"
Cohesion: 0.09
Nodes (19): annual, bakeriesStats, commercialSectors, csv, fields, fs, headers, lines (+11 more)

### Community 8 - "Commercial Budget Debug (JS)"
Cohesion: 0.11
Nodes (14): budget, commLocalities, csv, fields, fs, lines, locality, period (+6 more)

### Community 9 - "Commercial Budget Tests (JS)"
Cohesion: 0.12
Nodes (13): budget, commercialLocalityMap, csv, fields, fs, line, lines, period (+5 more)

### Community 10 - "CSV Parsing Debug (JS)"
Cohesion: 0.12
Nodes (14): consumerStatusIdx, csv, fields, fs, headers, lines, localityIdx, rates (+6 more)

### Community 11 - "Rate Matching (JS)"
Cohesion: 0.14
Nodes (12): csv, fields, fs, line, lines, period, rateLookup, rates (+4 more)

### Community 12 - "Sector Normalization & Merge"
Cohesion: 0.18
Nodes (12): backfill_bill_arrears(), _bill_list_summary_from_rows(), merge_sector_list_rows(), merge_sector_rows(), normalise_sector(), parse_number(), Normalise a sector name for grouping: trim, lowercase, collapse spaces., Merge rows that share the same normalised sector name.      For each unique se (+4 more)

### Community 13 - "Upload Progress UI (JS)"
Cohesion: 0.44
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 14 - "Bundled Dependencies"
Cohesion: 0.31
Nodes (9): chardet (character encoding detection, training metadata), Click 8.3.3 (command-line interface library), Flask 3.0.3 (Pallets web framework), itsdangerous 2.2.0 (cryptographic signing library), MarkupSafe 3.0.3 (HTML escaping library), bill_list.html (bill listing template), daily_staff_receive.html (daily staff receive template), index.html (All Received Bill Report template) (+1 more)

### Community 15 - "Commercial CSV Debug 2 (JS)"
Cohesion: 0.33
Nodes (4): fields, fs, headers, lines

### Community 16 - "UI Screenshots & Flow"
Cohesion: 0.33
Nodes (6): Consumer Report - After Upload, Consumer Report - Initial State, Test 01 - Page Loaded, Test 02 - Page Ready, Test 03 - After Upload, Test 04 - Report With Data

### Community 17 - "Rate Alias Normalization"
Cohesion: 0.5
Nodes (4): _add_rate_alias(), _normalize_rate_title(), Canonical key for rate matching; tolerates case/spacing drift without changing d, Map known legacy consumer rate labels to the active rate title.

## Ambiguous Edges - Review These
- `Consumer Report - After Upload` → `Test 04 - Report With Data`  [AMBIGUOUS]
  consumer-report-after-upload.png · relation: conceptually_related_to

## Knowledge Gaps
- **161 isolated node(s):** `Aggressively normalize a sector/locality name for robust matching.`, `Extract significant keywords from a sector/locality name.`, `Return display name: paired staff on separate lines, else as-is.`, `Like fmt_staff_name but returns HTML with <br> for display.`, `Remove duplicate uploaded bills without collapsing different bills for one conne` (+156 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Consumer Report - After Upload` and `Test 04 - Report With Data`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `_GroupedPdfWrapper` connect `Advanced Bill PDF Export` to `Core App & Bill Builders`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `_get_season_bill_ids()` connect `Bill List Exports` to `Core App & Bill Builders`, `Report Routes & Dashboard`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `generate_grouped_advanced_pdf()` connect `Advanced Bill PDF Export` to `Core App & Bill Builders`, `Bill List Exports`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **What connects `Aggressively normalize a sector/locality name for robust matching.`, `Extract significant keywords from a sector/locality name.`, `Return display name: paired staff on separate lines, else as-is.` to the rest of the system?**
  _161 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Core App & Bill Builders` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Report Routes & Dashboard` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._