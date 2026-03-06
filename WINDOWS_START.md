# Starting Open Moniker on Windows

## Prerequisites

1. Install Python 3.9+ 
2. Install dependencies:
```cmd
pip install -r requirements.txt
```

## Start Options

### Option 1: Python Monolith (Legacy, Port 8050)
```cmd
cd open-moniker-svc
set PYTHONPATH=src
python -m uvicorn moniker_svc.main:app --host 0.0.0.0 --port 8050
```

### Option 2: Management Service (Port 8052)
```cmd
cd open-moniker-svc
set PYTHONPATH=src
python -m uvicorn moniker_svc.management_app:app --host 0.0.0.0 --port 8052
```

### Option 3: Using start.py (Port 8060)
```cmd
cd open-moniker-svc
python start.py
```

## Configuration

Make sure these files exist:
- `sample_config.yaml`
- `sample_catalog.yaml`

Or set environment variables:
```cmd
set CONFIG_FILE=sample_config.yaml
set CATALOG_FILE=sample_catalog.yaml
```

## Troubleshooting

**Error: No module named 'moniker_svc.dashboard'**
- Run from project root directory
- Set PYTHONPATH: `set PYTHONPATH=src`
- Or use: `python -m uvicorn moniker_svc.main:app`

**Error: No module named 'fastapi'**
- Install dependencies: `pip install -r requirements.txt`

**Error: Cannot find config files**
- Copy sample files: 
  ```cmd
  copy sample_config.yaml config.yaml
  copy sample_catalog.yaml catalog.yaml
  ```

## Accessing the Service

Once started:
- Health: http://localhost:8050/health
- Docs: http://localhost:8050/docs
- Config UI: http://localhost:8050/config
- Dashboard: http://localhost:8050/dashboard

## Quick Test

```cmd
curl http://localhost:8050/health
```

Or open in browser: http://localhost:8050/docs
