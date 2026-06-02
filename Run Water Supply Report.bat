@echo off
setlocal

cd /d "%~dp0"

set "UV_CACHE_DIR=%~dp0.uv-cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.uv-python"
set "APP_URL=http://127.0.0.1:5000"

where uv >nul 2>nul
if errorlevel 1 (
  echo uv is not installed or not available in PATH.
  echo Install uv first, then run this file again.
  pause
  exit /b 1
)

echo Starting Water Supply Report...
echo.
echo App URL: %APP_URL%
echo Close this window to stop the app.
echo.

uv run --with flask==3.0.3 --with numpy==1.26.4 --with pandas==2.2.2 --with openpyxl==3.1.5 --with reportlab==4.2.2 python app.py

pause
