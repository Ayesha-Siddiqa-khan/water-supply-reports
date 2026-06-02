# Claude Code CLI Prompt: Advanced Bill List Filters and Export

Copy and paste this prompt into **Claude Code CLI** while inside your existing app/project folder.

```text
You are working on an existing running application. This app is already functional, so do NOT disturb, remove, rename, refactor, or break any existing feature, UI, route, API, database logic, component, or option.

Your task is to carefully study the existing project first, understand the app structure, bill list page logic, data flow, filters, export/download logic if any, and existing UI patterns. After understanding the logic, add a new feature only on the Bill List page.

Important rules:
1. Do not change existing functionality.
2. Do not remove or modify existing options.
3. Add the new feature as an additional card/section on the Bill List page.
4. Follow the existing code style, folder structure, component pattern, naming style, and UI design.
5. Make the implementation safe, clean, and backward compatible.
6. If any existing export system exists, reuse it. If not, add a clean implementation.
7. Do not hardcode data unless the app already follows that style.
8. Before making changes, inspect the relevant files and explain briefly what you found.
9. After implementation, tell me exactly which files were changed and what was added.

Feature to add:

On the Bill List page, add a new card/section for Advanced Bill Checking and Export.

This new card should allow the user to filter and download bills based on different conditions.

Required filters/options:

1. Outstanding amount filter:
   - User should be able to enter/select an amount.
   - Example: If user enters 10000, the app should show bills where outstanding amount is greater than 10000.
   - The filtered bills should be displayed clearly.

2. Sector-wise filter/export:
   - User should be able to filter/download bills by sector.
   - If the user selects a sector, only bills from that sector should appear/export.

3. Zone-wise filter/export:
   - User should be able to filter/download bills by zone.
   - If the user selects a zone, only bills from that zone should appear/export.

4. Staff-wise filter/export:
   - User should be able to filter/download bills by staff.
   - If the user selects staff, only bills related to that staff should appear/export.

5. Combined filters:
   - The filters should work together if possible.
   - Example: Sector + outstanding amount above 10000.
   - Example: Zone + staff + outstanding amount.

6. Download/export options:
   - User should be able to download the filtered bill data in:
     - PDF
     - CSV
     - Excel/XLSX

7. Output requirements:
   - Exported files should contain the filtered bill list only.
   - Include important bill fields already used in the app, such as bill number, customer/name, sector, zone, staff, total amount, paid amount, outstanding amount, date/status, or whatever fields exist in the app.
   - File names should be clear, for example:
     - bills_outstanding_above_10000.pdf
     - bills_sector_A.xlsx
     - bills_zone_1.csv

Implementation instructions:

Step 1: Explore the project.
- Find the Bill List page/component.
- Find where bill data comes from.
- Check whether filters already exist.
- Check whether PDF/CSV/Excel export already exists.
- Check UI components/cards used in this app.

Step 2: Make a safe plan.
- Explain which files need to be changed.
- Explain where the new card will be added.
- Explain how filtering and exporting will work.

Step 3: Implement the feature.
- Add the new card/section without disturbing existing layout.
- Add filters for outstanding amount, sector, zone, and staff.
- Add filtered result display.
- Add download buttons for PDF, CSV, and Excel.
- Reuse existing utilities/components where possible.
- Add new helper functions only if needed.

Step 4: Validate.
- Check that the old Bill List page still works.
- Check that previous options are unchanged.
- Check that each filter works.
- Check that combined filters work.
- Check that PDF, CSV, and Excel downloads work.
- Fix any TypeScript, linting, import, or build errors.

Step 5: Final response.
After completing the work, provide:
- Summary of changes
- Files changed
- How to use the new feature
- Any package installed, if needed
- Any assumptions made
- Any testing performed

Do not rewrite the whole app. Only add this feature safely.
```

## How to Use

Open your project folder in terminal and run:

```bash
claude
```

Then paste the full prompt above into Claude Code CLI.
