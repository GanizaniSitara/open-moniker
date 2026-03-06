@echo off
REM Start Open Moniker on Windows

echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting Moniker Service...
echo.
echo Available at:
echo   http://localhost:8050/health
echo   http://localhost:8050/docs
echo   http://localhost:8050/config
echo.

set PYTHONPATH=src
set CONFIG_FILE=sample_config.yaml
set CATALOG_FILE=sample_catalog.yaml

python -m uvicorn moniker_svc.main:app --host 0.0.0.0 --port 8050
