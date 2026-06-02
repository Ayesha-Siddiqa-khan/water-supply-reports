@echo off
setlocal

cd /d "%~dp0"

if "%UV_CACHE_DIR%"=="" set "UV_CACHE_DIR=%~dp0.uv-cache"
if "%UV_PYTHON_INSTALL_DIR%"=="" set "UV_PYTHON_INSTALL_DIR=%~dp0.uv-python"

where uv >nul 2>nul
if errorlevel 1 (
  echo uv is not installed or not available in PATH.
  echo Install uv first, then run this file again.
  pause
  exit /b 1
)

echo Closing any running portable app...
taskkill /f /im "WaterSupplyReport.exe" 2>nul
timeout /t 3 /nobreak >nul

echo Cleaning old build files...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "WaterSupplyReport-Portable.zip" del /f /q "WaterSupplyReport-Portable.zip"
timeout /t 3 /nobreak >nul

echo.
echo Building portable Water Supply Report app...
echo.

uv run ^
  --with flask==3.0.3 ^
  --with numpy==1.26.4 ^
  --with pandas==2.2.2 ^
  --with openpyxl==3.1.5 ^
  --with reportlab==4.2.2 ^
  --with pyinstaller==6.11.1 ^
  pyinstaller --clean --noconfirm WaterSupplyReport.spec

if errorlevel 1 (
  echo.
  echo Build failed.
  pause
  exit /b 1
)

copy /y "PORTABLE_APP_README.txt" "dist\WaterSupplyReport-Portable\README.txt" >nul

echo Waiting for build to complete...
timeout /t 5 /nobreak >nul

echo.
echo Creating ZIP file...
powershell -Command "Compress-Archive -Path 'dist\WaterSupplyReport-Portable\*' -DestinationPath 'WaterSupplyReport-Portable.zip' -Force"

if errorlevel 1 (
  echo.
  echo ZIP creation failed.
  pause
  exit /b 1
)

echo.
echo ================================================
echo Portable app and ZIP file created successfully!
echo.
echo EXE:   %~dp0dist\WaterSupplyReport-Portable\WaterSupplyReport.exe
echo ZIP:   %~dp0WaterSupplyReport-Portable.zip
echo.
echo Copy the ZIP file or the folder to another PC.
echo ================================================
pause
