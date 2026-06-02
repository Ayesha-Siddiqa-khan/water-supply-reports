Water Supply Report - Portable App

Build on this PC:
1. Double-click "Build Portable App.bat".
2. Wait until it finishes.
3. Open the generated folder:
   dist\WaterSupplyReport

Use on another Windows PC:
1. Copy the whole dist\WaterSupplyReport folder to the other PC.
2. Double-click WaterSupplyReport.exe.
3. The app opens in the browser at http://127.0.0.1:5000.
4. Close the black app window to stop the app.

Notes:
- The other PC does not need Python, uv, or pip.
- Keep all files in the WaterSupplyReport folder together.
- bill_list.sqlite3 and uploads are stored beside WaterSupplyReport.exe, so data stays with the copied folder.
- If port 5000 is busy, run from Command Prompt with another port:
  set WATER_SUPPLY_PORT=5001
  WaterSupplyReport.exe
