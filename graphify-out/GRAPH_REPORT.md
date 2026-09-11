# Graph Report - water suppy report  (2026-09-11)

## Corpus Check
- 55 files · ~1,741,736 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1365 nodes · 2983 edges · 108 communities (78 shown, 30 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 64 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d2d6b92d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_BytesIO|BytesIO]]
- [[_COMMUNITY_app.py|app.py]]
- [[_COMMUNITY_DataFrame|DataFrame]]
- [[_COMMUNITY_consumer_report|consumer_report]]
- [[_COMMUNITY__build_new_connection_detail_report|_build_new_connection_detail_report]]
- [[_COMMUNITY_Base Template|Base Template]]
- [[_COMMUNITY_upload-progress.js|upload-progress.js]]
- [[_COMMUNITY_export_arrear_calculator|export_arrear_calculator]]
- [[_COMMUNITY_app.py|app.py]]
- [[_COMMUNITY_vercel.json|vercel.json]]
- [[_COMMUNITY_check_bill_list.py|check_bill_list.py]]
- [[_COMMUNITY_check_csv.py|check_csv.py]]
- [[_COMMUNITY_check_dup.py|check_dup.py]]
- [[_COMMUNITY_check_import.py|check_import.py]]
- [[_COMMUNITY_check_keys.py|check_keys.py]]
- [[_COMMUNITY_check_schema.py|check_schema.py]]
- [[_COMMUNITY_temp_debug.py|temp_debug.py]]
- [[_COMMUNITY_temp_debug2.py|temp_debug2.py]]
- [[_COMMUNITY_temp_debug3.py|temp_debug3.py]]
- [[_COMMUNITY_Agent Instructions|Agent Instructions]]
- [[_COMMUNITY_Claude Code CLI Prompt Advanced Bill List Filters and Export|Claude Code CLI Prompt: Advanced Bill List Filters and Export]]
- [[_COMMUNITY_Advanced Bill Filters Feature Prompt|Advanced Bill Filters Feature Prompt]]
- [[_COMMUNITY_match_staff_assignment|match_staff_assignment]]
- [[_COMMUNITY_match_staff_assignment|match_staff_assignment]]
- [[_COMMUNITY__build_connection_rate_report|_build_connection_rate_report]]
- [[_COMMUNITY__normalize_staff_name|_normalize_staff_name]]
- [[_COMMUNITY_new_connection_detail|new_connection_detail]]
- [[_COMMUNITY_export_arrear_calculator|export_arrear_calculator]]
- [[_COMMUNITY_export_new_connection_detail|export_new_connection_detail]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]

## God Nodes (most connected - your core abstractions)
1. `fmt()` - 33 edges
2. `fmt()` - 33 edges
3. `get_db()` - 27 edges
4. `get_db()` - 27 edges
5. `init_bill_list_db()` - 23 edges
6. `init_bill_list_db()` - 23 edges
7. `download_card()` - 22 edges
8. `download_card()` - 20 edges
9. `summarize_dataframe()` - 18 edges
10. `export_six_month_pitch()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `arrears_analysis()` --calls--> `allowed_file()`  [INFERRED]
  arrears_analysis.py → app.py
- `handover()` --calls--> `allowed_file()`  [INFERRED]
  handover.py → app.py
- `handover()` --calls--> `is_ajax()`  [INFERRED]
  handover.py → app.py
- `arrears_analysis()` --calls--> `ajax_ok()`  [INFERRED]
  arrears_analysis.py → app.py
- `handover()` --calls--> `ajax_ok()`  [INFERRED]
  handover.py → app.py

## Hyperedges (group relationships)
- **Reports-section pages extending base.html with shared sidebar nav** — tpl_index, tpl_bill_list, tpl_daily, tpl_consumer, tpl_consumer_remaining, tpl_arrear, tpl_base [INFERRED]
- **Client-side-only file tools (no server route, use browser CDN libraries)** — tpl_fcm, tpl_merge, ext_sheetjs, ext_pdflib [INFERRED]
- **Report pages with PDF/CSV/XLSX export endpoint families** — tpl_index, tpl_bill_list, tpl_consumer, tpl_consumer_remaining, tpl_daily, tpl_arrear, exp_index, exp_bill_list, exp_consumer, exp_consumer_remaining, exp_daily, exp_arrear [INFERRED]

## Communities (108 total, 30 thin omitted)

### Community 0 - "BytesIO"
Cohesion: 0.06
Nodes (49): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _build_consumer_sector_summary(), _canonical_consumer_sector_locality(), _classify_connection_status(), _clean_rate_type_name() (+41 more)

### Community 1 - "app.py"
Cohesion: 0.09
Nodes (46): build_bill_key(), build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_daily_staff_receive_report(), build_income_category_summary() (+38 more)

### Community 2 - "DataFrame"
Cohesion: 0.09
Nodes (44): active_figures(), _app(), build_comparison(), change_rows(), classify(), clear_result(), _column(), comparable() (+36 more)

### Community 3 - "consumer_report"
Cohesion: 0.11
Nodes (37): Any, _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+29 more)

### Community 4 - "_build_new_connection_detail_report"
Cohesion: 0.06
Nodes (53): build_bill_key(), _build_dnc_register_report(), _build_new_connection_detail_report(), build_receipt_monthly_rows(), clean_amount_value(), _clear_new_connection_detail_cache(), _connection_rate_rows_from_payload(), _dedupe_value() (+45 more)

### Community 5 - "Base Template"
Cohesion: 0.08
Nodes (47): apply_manual_zone_overrides(), backfill_bill_arrears(), bill_list(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_consumer_sector_remaining_report(), build_unpaid_amount_summary() (+39 more)

### Community 6 - "upload-progress.js"
Cohesion: 0.09
Nodes (32): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+24 more)

### Community 7 - "export_arrear_calculator"
Cohesion: 0.16
Nodes (17): _build_new_connection_detail_report(), _clear_new_connection_detail_cache(), _load_new_connection_detail_cache(), _ncd_classification(), _ncd_decimal(), _ncd_financial_year(), _ncd_int(), _ncd_norm() (+9 more)

### Community 8 - "app.py"
Cohesion: 0.33
Nodes (6): merge_sector_list_rows(), merge_sector_rows(), normalise_sector(), Normalise a sector name for grouping: trim, lowercase, collapse spaces., Merge rows that share the same normalised sector name.      For each unique sect, Merge list-of-lists rows by normalised sector. Keeps first locality, sums numeri

### Community 9 - "vercel.json"
Cohesion: 0.22
Nodes (9): _calc_col_widths(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), _GroupedPdfWrapper, Generate a landscape PDF with one section per group showing detailed bill rows., Helper to write grouped PDF sections with smart pagination and staff zone suppor, Estimated mm needed for a group: heading + sub-lines + table header + body + tot, Insert PageBreak before a group if remaining space is too small. (+1 more)

### Community 10 - "check_bill_list.py"
Cohesion: 0.16
Nodes (14): main(), Self-check for the Data Comparison page.  Run:  python check_data_comparison.py, read(), build_handover_dataset(), _compose(), _conn_key(), _key_frame(), Series (+6 more)

### Community 11 - "check_csv.py"
Cohesion: 0.16
Nodes (27): apply_filters(), build_sector_summary(), col_key(), detail_columns(), detail_rows(), drop_excluded_sectors(), filter_label(), _finalize() (+19 more)

### Community 12 - "check_dup.py"
Cohesion: 0.07
Nodes (69): bill_income_category_export_rows(), bill_list_export_rows(), _bill_list_summary_from_rows(), _bracket_rich_text(), build_connection_summary(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), _card_rows_to_df() (+61 more)

### Community 13 - "check_import.py"
Cohesion: 0.06
Nodes (59): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), bill_list(), build_consumer_sector_remaining_report(), _build_consumer_sector_summary(), build_dashboard_results() (+51 more)

### Community 14 - "check_keys.py"
Cohesion: 0.08
Nodes (41): _app(), _column_extents(), _detail_widths(), _draw_ring_text(), _draw_signature_band(), _draw_star(), _draw_watermark(), _emblem_path() (+33 more)

### Community 15 - "check_schema.py"
Cohesion: 0.08
Nodes (36): ajax_error(), ajax_ok(), allowed_file(), arrear_calculator(), build_dashboard_results(), _clear_consumer_summary_cache(), consumer_report(), consumer_sector_remaining_report() (+28 more)

### Community 16 - "temp_debug.py"
Cohesion: 0.11
Nodes (14): Flowable, build_sections(), export_handover(), handover_print(), NumberedCanvas, _page_furniture(), _PageMark, The one date the register carries.      A finalised record is dated when it wa (+6 more)

### Community 17 - "temp_debug2.py"
Cohesion: 0.07
Nodes (56): apply_manual_zone_overrides(), backfill_bill_arrears(), bill_list_sector_seasonly_export_rows(), bill_list_staff_export_rows(), bill_list_zone_export_rows(), build_daily_staff_receive_report(), build_unpaid_amount_summary(), clear_unmatched_log() (+48 more)

### Community 18 - "temp_debug3.py"
Cohesion: 0.09
Nodes (36): test_upload(), _app(), arrears_analysis(), arrears_analysis_print(), _arrears_dir(), build_arrears_pdf(), classify_status(), compute_arrears_analysis() (+28 more)

### Community 19 - "Agent Instructions"
Cohesion: 0.52
Nodes (10): bindUploadForms(), createOverlay(), getUploadFileLabel(), handleUpload(), removeOverlay(), setFormLoading(), shouldUseNativeUpload(), showToast() (+2 more)

### Community 20 - "Claude Code CLI Prompt: Advanced Bill List Filters and Export"
Cohesion: 0.13
Nodes (19): clean_cell(), _closest_staff_key(), _deep_normalize_sector(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), is_large_pdf_text(), _keyword_set() (+11 more)

### Community 21 - "Advanced Bill Filters Feature Prompt"
Cohesion: 0.5
Nodes (4): _numeric_amounts(), Write money columns to Excel as numbers, not "13,040" text, so the     arrears, Parse a money cell tolerantly.      Pulls the first number out rather than del, _to_amount()

### Community 22 - "match_staff_assignment"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list.      Fixed column order:, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 23 - "match_staff_assignment"
Cohesion: 0.4
Nodes (4): maxDuration, functions, app.py, $schema

### Community 24 - "_build_connection_rate_report"
Cohesion: 0.08
Nodes (41): bill_income_category_export_rows(), bill_list_export_rows(), _bill_list_summary_from_rows(), _bracket_rich_text(), build_connection_summary(), _calc_daily_detail_col_widths(), _calc_daily_summary_col_widths(), _card_rows_to_df() (+33 more)

### Community 25 - "_normalize_staff_name"
Cohesion: 0.67
Nodes (3): main(), Self-check for the Handover Register join, filters, and snapshot lock.  Run:, read()

### Community 26 - "new_connection_detail"
Cohesion: 0.5
Nodes (4): Water Supply Report Application, Python Libraries (numpy, pandas, openpyxl, reportlab), Flask Framework, bill_list.sqlite3 Database

### Community 41 - "Community 41"
Cohesion: 0.08
Nodes (39): active_figures(), _app(), build_comparison(), change_rows(), clear_result(), _column(), comparable(), _consumer_active() (+31 more)

### Community 42 - "Community 42"
Cohesion: 0.09
Nodes (31): _blank_totals(), build_audit_report(), classify_negative(), conn_sort_key(), correct_pending(), _corrections_for(), _default_classify(), _hidden_arrear() (+23 more)

### Community 43 - "Community 43"
Cohesion: 0.11
Nodes (25): classify(), Reduce an export to the fields this page compares.      A connection counts as A, apply_filters(), build_handover_dataset(), _canonical_labels(), canonicalise_groups(), _compose(), _conn_key() (+17 more)

### Community 44 - "Community 44"
Cohesion: 0.09
Nodes (19): annual, bakeriesStats, commercialSectors, csv, fields, fs, headers, lines (+11 more)

### Community 45 - "Community 45"
Cohesion: 0.16
Nodes (22): build_commercial_daily_income_rows(), build_commercial_mask(), build_commercial_month_wise_summary(), build_commercial_rows(), build_daily_rows(), build_income_category_summary(), build_monthly_rows(), build_private_society_mask() (+14 more)

### Community 46 - "Community 46"
Cohesion: 0.19
Nodes (11): _calc_col_widths(), export_advanced_bills_response(), generate_advanced_filtered_pdf(), generate_grouped_advanced_pdf(), generate_single_group_pdf(), _GroupedPdfWrapper, Generate a landscape PDF with one section per group showing detailed bill rows., Helper to write grouped PDF sections with smart pagination and staff zone suppor (+3 more)

### Community 47 - "Community 47"
Cohesion: 0.15
Nodes (19): _add_rate_alias(), _annualize_connection_rate(), _build_connection_rate_report(), _build_connection_rate_report_from_summary(), _connection_rate_bucket(), _connection_rate_category(), _connection_rate_default(), _connection_rate_description() (+11 more)

### Community 48 - "Community 48"
Cohesion: 0.19
Nodes (19): build_sector_summary(), col_key(), detail_columns(), filter_label(), _finalize(), handover_snapshot(), is_commercial(), Count one printable block as a single summary line.      Counts come straight (+11 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (14): budget, commLocalities, csv, fields, fs, lines, locality, period (+6 more)

### Community 50 - "Community 50"
Cohesion: 0.12
Nodes (13): budget, commercialLocalityMap, csv, fields, fs, line, lines, period (+5 more)

### Community 51 - "Community 51"
Cohesion: 0.12
Nodes (14): consumerStatusIdx, csv, fields, fs, headers, lines, localityIdx, rates (+6 more)

### Community 52 - "Community 52"
Cohesion: 0.16
Nodes (16): clean_cell(), _deep_normalize_sector(), fmt_staff_name_html(), get_auto_staff_override(), get_staff_by_connection_rule(), _keyword_set(), _levenshtein(), load_alias_rules() (+8 more)

### Community 53 - "Community 53"
Cohesion: 0.17
Nodes (16): _app(), _gunzip(), handover(), _handover_dir(), handover_status(), _list_snapshots(), load_dataset(), Read an uploaded CSV/XLSX as text so connection numbers keep leading zeros. (+8 more)

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (13): Agent Instructions, Auto-Update on Changes, code:block1 (/graphify . --update), code:block2 (/graphify query "how does bill upload work"), code:bash (# Development server), Commands, Development Guidelines, Graph Status (+5 more)

### Community 55 - "Community 55"
Cohesion: 0.14
Nodes (12): csv, fields, fs, line, lines, period, rateLookup, rates (+4 more)

### Community 56 - "Community 56"
Cohesion: 0.15
Nodes (14): _column_extents(), _detail_widths(), _esc(), _index_flowables(), A detail table for the printed register.      Two corrections on top of the sh, Wrap only the long-text columns as Paragraphs.      Matches what ``wrap_pdf_bo, Longest value per column, used to size the columns and decide wrapping., Share the page across columns according to what they actually hold.      Sizin (+6 more)

### Community 57 - "Community 57"
Cohesion: 0.18
Nodes (12): drop_duplicate_bills(), fast_bill_no_key(), fast_upload_number(), fast_upload_text(), import_bill_list_dataframe(), infer_zone(), normalize_column_name(), normalize_dataframe() (+4 more)

### Community 58 - "Community 58"
Cohesion: 0.2
Nodes (11): export_advanced_bills(), format_mobile(), generate_zip_of_group_pdfs(), get_filtered_bills(), group_bills(), map_bills_to_staff(), Add a 'staff_name' key to each bill based on staff_assignments (locality > secto, Return sort key for zone ordering: A=1, B=2, C=3, Commercial=4, unknown=99. (+3 more)

### Community 59 - "Community 59"
Cohesion: 0.22
Nodes (4): NumberedCanvas, _PageMark, A zero-height marker that reports the page it lands on.      Placed at the hea, Canvas that stamps "Page X of Y" once the total is known.      ReportLab strea

### Community 60 - "Community 60"
Cohesion: 0.22
Nodes (10): build_sections(), detail_rows(), export_handover(), handover_print(), _page_furniture(), The one date the register carries.      A finalised record is dated when it wa, Page-begin callback.      Runs before the frame lays its flowables down, which, Split the register into printable blocks.      Ordinary sectors come first, se (+2 more)

### Community 61 - "Community 61"
Cohesion: 0.28
Nodes (9): _build_dnc_register_report(), _dnc_classification(), _dnc_money(), _dnc_pair(), _dnc_rate_and_classification(), _dnc_report_rows(), _dnc_split_sector_locality(), _dnc_sum_rows() (+1 more)

### Community 62 - "Community 62"
Cohesion: 0.33
Nodes (7): export_advanced_bills(), generate_zip_of_group_pdfs(), group_bills(), Return sort key for zone ordering: A=1, B=2, C=3, Commercial=4, unknown=99., Group bills by sector/zone/staff.      Returns:       - sector/zone: list of (gr, sanitize_filename(), _zone_sort_key()

### Community 63 - "Community 63"
Cohesion: 0.29
Nodes (7): _build_arrear_export_rows(), export_arrear_calculator(), _parse_arrear_export_cols(), Parse comma-separated column keys into an ordered list.      Fixed column order:, Build export rows from summary data, selecting only requested columns., Sort rows by the given status priority and order., _sort_arrear_rows()

### Community 64 - "Community 64"
Cohesion: 0.29
Nodes (7): _draw_ring_text(), _draw_star(), _draw_watermark(), _emblem_path(), The municipal emblem shipped in static/, or None if it is absent., Set text right around the circle, evenly spaced with no gap.      The legend i, A round official stamp, faint, centred, behind the page content.

### Community 65 - "Community 65"
Cohesion: 0.29
Nodes (7): _numeric_amounts(), Collapse whitespace and lower-case — used for every exact-match key., Commercial when the rate type says so — including the ``COMERCIAL``     spellin, Write money columns to Excel as numbers, not "13,040" text, so the     arrears, _status_of(), _txt(), _type_of()

### Community 66 - "Community 66"
Cohesion: 0.33
Nodes (5): Sheet: All Negative Records, Sheet: By Sector, Sheet: Incorrect - To Correct, Sheet: Summary, Sheet: Valid - Advances

### Community 67 - "Community 67"
Cohesion: 0.33
Nodes (4): fields, fs, headers, lines

### Community 68 - "Community 68"
Cohesion: 0.33
Nodes (6): merge_sector_list_rows(), merge_sector_rows(), normalise_sector(), Normalise a sector name for grouping: trim, lowercase, collapse spaces., Merge rows that share the same normalised sector name.      For each unique sect, Merge list-of-lists rows by normalised sector. Keeps first locality, sums numeri

### Community 69 - "Community 69"
Cohesion: 0.4
Nodes (4): Sheet: All 931 Records, Sheet: Hidden Dues Recovered, Sheet: Sector 34 Iqbal Nager, Sheet: Summary

### Community 70 - "Community 70"
Cohesion: 0.4
Nodes (4): Claude Code CLI Prompt: Advanced Bill List Filters and Export, code:text (You are working on an existing running application. This app), code:bash (claude), How to Use

### Community 71 - "Community 71"
Cohesion: 0.67
Nodes (3): main(), Self-check for the Data Comparison page.  Run:  python check_data_comparison.py, read()

### Community 72 - "Community 72"
Cohesion: 0.67
Nodes (3): main(), Self-check for the Handover Register join, filters, and snapshot lock.  Run:, read()

### Community 73 - "Community 73"
Cohesion: 0.5
Nodes (4): _canonical_labels(), canonicalise_groups(), Map visually identical labels onto one spelling.      Sector and locality name, Collapse duplicate Sector/Locality spellings before anything groups on them.

## Knowledge Gaps
- **424 isolated node(s):** `Aggressively normalize a sector/locality name for robust matching.`, `Extract significant keywords from a sector/locality name.`, `Return display name: paired staff on separate lines, else as-is.`, `Like fmt_staff_name but returns HTML with <br> for display.`, `Remove duplicate uploaded bills without collapsing different bills for one conne` (+419 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `classify()` connect `DataFrame` to `Community 73`, `check_bill_list.py`, `check_csv.py`, `upload-progress.js`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `parse_register()` connect `upload-progress.js` to `DataFrame`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `classify()` connect `Community 43` to `Community 41`, `Community 42`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `ParagraphStyle` (e.g. with `_report_pdf()` and `export_handover()`) actually correct?**
  _`ParagraphStyle` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Aggressively normalize a sector/locality name for robust matching.`, `Extract significant keywords from a sector/locality name.`, `Return display name: paired staff on separate lines, else as-is.` to the rest of the system?**
  _424 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `BytesIO` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09 - nodes in this community are weakly interconnected._