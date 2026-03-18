# Moniker Service

A unified data access layer for enterprise data governance. Canonical identification for all firm data assets with hierarchical ownership and access telemetry.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  Your Code                                                      │
│    m = Moniker("prices.equity/AAPL@20260115")                   │
│    info = m.resolve()                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ GET /resolve/prices.equity/AAPL@20260115
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Moniker Service                                                │
│    Returns: {                                                   │
│      "source_type": "snowflake",                                │
│      "connection": {"account": "firm.snowflake"},               │
│      "query": "SELECT * FROM PRICES WHERE symbol='AAPL'         │
│               AND trade_date = TO_DATE('20260115','YYYYMMDD')"  │
│    }                                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Client executes query
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Snowflake                                                      │
│    → Returns price data                                         │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Your Notebook / Script                                         │
│    from moniker_client import Moniker                           │
│    m = Moniker("risk.cvar/DESK_A/20240115/USD")                 │
│    data = m.fetch()                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Moniker Service (this repo)                                    │
│    - Resolves monikers → source connection info                 │
│    - Tracks ownership hierarchy                                 │
│    - Records access telemetry                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐        ┌──────────┐
   │Snowflake│         │ Oracle  │        │  REST    │
   └─────────┘         └─────────┘        └──────────┘
```

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd open-moniker
pip install -e .
pip install -e client/

# 2. Start the server (uses built-in demo catalog with mock data)
# Linux/Mac:
PYTHONPATH="$PWD/src:$PWD/external/moniker-data/src" uvicorn moniker_svc.main:app --reload

# Windows PowerShell:
$env:PYTHONPATH="$PWD\src;$PWD\external\moniker-data\src"; uvicorn moniker_svc.main:app --reload

# 3. Open the web UI
# http://localhost:8050/ui
```

## Try the API

```bash
# Browse the catalog tree
curl http://localhost:8050/tree

# Get metadata for a domain
curl http://localhost:8050/describe/risk.cvar

# See all endpoints
curl http://localhost:8050/
```

## Using the Client Library

```python
from moniker_client import Moniker

# Create a moniker for AAPL equity prices
m = Moniker("prices.equity/AAPL")

# Resolve to get connection info
result = m.resolve()
print(result.source_type)     # 'snowflake'
print(result.connection)      # {'account': 'firm.snowflake', ...}

# Get ownership and metadata
info = m.describe()
print(info["ownership"]["accountable_owner"])   # market-data-governance@firm.com
print(info["ownership"]["support_channel"])     # #market-data

# Trace data lineage
lin = m.lineage()
print(lin["path_hierarchy"])                    # ['prices', 'prices.equity', ...]

# Historical data with date version
m_hist = Moniker("prices.equity/AAPL@20260115")
historical = m_hist.resolve()

# Navigate to children
m_prices = Moniker("prices.equity")
print(m_prices.children())    # ['AAPL', 'MSFT', 'GOOGL', ...]
```

## Run Tests

```bash
# Set PYTHONPATH (Linux/Mac)
export PYTHONPATH="$PWD/src:$PWD/client:$PWD/external/moniker-data/src"

# Windows PowerShell
$env:PYTHONPATH="$PWD\src;$PWD\client;$PWD\external\moniker-data\src"

# Run all tests
python -m pytest tests/ external/moniker-tests/tests/ -v
```

## Configure Your Own Catalog

Edit `sample_catalog.yaml` to define your data domains:

```yaml
risk.cvar:
  display_name: "CVaR Risk Measures"
  description: "Daily CVaR calculations by portfolio"

  ownership:
    accountable_owner: risk-governance@firm.com
    data_specialist: risk-quants@firm.com
    support_channel: "#risk-data"

  # Governance roles (optional)
  adop: jane.smith@firm.com      # Accountable Data Owner Partner
  ads: john.doe@firm.com         # Accountable Data Steward

  source_binding:
    type: oracle
    config:
      host: risk-db.firm.com
      service_name: RISKPROD
      query: |
        SELECT portfolio_id, currency, security_id,
               cvar_95, cvar_99, var_95, calculation_date
        FROM RISK.DAILY_CVAR
        WHERE portfolio_id = '{segments[0]}'
          AND currency = '{segments[2]}'
          AND calculation_date = TO_DATE('{segments[1]}', 'YYYYMMDD')

  documentation:
    glossary_url: https://confluence.firm.com/risk/cvar-glossary
    runbook_url: https://confluence.firm.com/risk/cvar-runbook
```

## Project Structure

```
open-moniker/
├── src/moniker_svc/           # FastAPI service
├── client/moniker_client/     # Python client library
├── external/                  # Will become separate repos
│   └── moniker-tests/         # Integration tests
├── tests/                     # Unit tests
└── sample_catalog.yaml        # Example catalog definition
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Moniker** | Canonical path like `risk.cvar/DESK_A/20240115/USD` |
| **Ownership** | Who's accountable (ADOP), who knows the data (ADS), where to get help |
| **Source Binding** | Maps moniker paths to actual databases/APIs |
| **Access Policy** | Rules that block expensive queries (e.g., "no SELECT * on 10M rows") |

## Web UI

Browse the catalog visually at **http://localhost:8050/ui**

- Tree view of all data domains
- Click nodes to see ownership, source type, governance roles
- Links to API endpoints for each node

## Deploy to Render.com

**Option 1: One-click deploy**
1. Fork this repo
2. Go to [render.com/new](https://render.com/new)
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` and deploys

**Option 2: Manual setup**
1. New → Web Service → Connect repo
2. Settings:
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `PYTHONPATH=src:external/moniker-data/src uvicorn moniker_svc.main:app --host 0.0.0.0 --port $PORT`
3. Add environment variable: `PYTHON_VERSION=3.11`

Once deployed, access:
- **Web UI**: `https://your-app.onrender.com/ui`
- **API docs**: `https://your-app.onrender.com/docs`
- **Health check**: `https://your-app.onrender.com/health`

**Test the deployed API:**
```bash
# Get the tree structure
curl https://your-app.onrender.com/tree

# Run tests against deployed instance
MONIKER_SERVICE_URL=https://your-app.onrender.com python -m pytest external/moniker-tests/tests/ -v
```

## License

MIT
