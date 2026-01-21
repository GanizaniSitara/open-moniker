# Moniker Service

A unified data access layer for enterprise data governance. Provides canonical identification for all firm data assets with hierarchical ownership and full access telemetry.

## Architecture

The Moniker Service is a **resolution service**, not a data proxy. This prevents it from becoming a bottleneck for all firm data.

```
┌─────────────────────────────────────────────────────────────────┐
│  Your Notebook / Script                                         │
│                                                                 │
│    from moniker_client import read                              │
│    data = read("market-data/prices/equity/AAPL")                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  moniker-client (Python library)                                │
│                                                                 │
│    1. RESOLVE → GET /resolve/market-data/prices/equity/AAPL     │
│       Returns: source_type, connection, query, ownership        │
│                                                                 │
│    2. FETCH → Connect DIRECTLY to Snowflake/Oracle/Bloomberg    │
│       Using YOUR credentials (from environment)                 │
│                                                                 │
│    3. TELEMETRY → POST /telemetry/access                        │
│       Reports who accessed what (non-blocking)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌─────────┐         ┌─────────┐        ┌──────────┐
   │Snowflake│         │ Oracle  │        │Bloomberg │
   └─────────┘         └─────────┘        └──────────┘
     (direct)           (direct)           (direct)
```

**Key benefits:**
- Service doesn't become a bottleneck for all firm data
- Credentials stay local (not sent to the service)
- Data flows directly from source to your code
- Telemetry tracks who accessed what

## Components

| Component | Description |
|-----------|-------------|
| `src/moniker_svc/` | Resolution service (FastAPI) |
| `client/moniker_client/` | Python client library |

## Quick Start

### Start the Service

```bash
# Install the service
pip install -e .

# Run
python -m moniker_svc.main
```

Service runs at http://localhost:8000

### Use the Client

```bash
# Install the client library
pip install -e client/

# In Python
python
```

```python
from moniker_client import read, describe, lineage

# Read data
data = read("market-data/prices/equity/AAPL")

# Get ownership info
info = describe("market-data/prices/equity")
print(f"Owner: {info['ownership']['accountable_owner']}")
print(f"Support: {info['ownership']['support_channel']}")

# Get full lineage
lin = lineage("market-data/prices/equity/AAPL")
```

### Run the Demo

```bash
pip install colorama
python demo.py
```

## Configuration

### Client Environment Variables

```bash
# Moniker service URL
export MONIKER_SERVICE_URL=http://moniker-svc:8000

# Your identity (for telemetry)
export MONIKER_APP_ID=my-notebook
export MONIKER_TEAM=quant-research

# Database credentials (used by client, NOT sent to service)
export SNOWFLAKE_USER=your_user
export SNOWFLAKE_PASSWORD=your_password

export ORACLE_USER=your_user
export ORACLE_PASSWORD=your_password
```

### Service Configuration

See `config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8000

telemetry:
  enabled: true
  sink_type: console  # console | file | zmq
  batch_size: 1000
  flush_interval_seconds: 1.0

cache:
  enabled: true
  max_size: 10000
  default_ttl_seconds: 300
```

## Concepts

### Moniker Path

Hierarchical identifier for any data asset:

```
moniker://market-data/prices/equity/AAPL
         └─ domain ─┘└ category ┘└ type ┘└ id ┘
```

Examples:
- `market-data/prices/equity/AAPL` - Apple stock price
- `reference/calendars/trading/NYSE` - NYSE trading calendar
- `risk/var/desk/FX` - FX desk Value at Risk

### Ownership Triple

Each node in the hierarchy can define:

| Field | Description |
|-------|-------------|
| **Accountable Owner** | Executive responsible for data governance |
| **Data Specialist** | Technical SME who understands the data |
| **Support Channel** | Slack/Teams channel for help |

Ownership inherits down the hierarchy. Each field inherits independently.

```
market-data/                 ← Owner: jane@firm.com, Specialist: team@firm.com
├── prices/                  ← Inherits all from parent
│   ├── equity/              ← Override: Specialist: equity-team@firm.com
│   │   └── AAPL             ← Inherits from equity/
│   └── fx/                  ← Inherits from prices/
```

### Source Bindings

Map moniker paths to actual data sources:

| Source | Description |
|--------|-------------|
| `snowflake` | Snowflake data warehouse |
| `oracle` | Oracle database |
| `rest` | REST APIs |
| `static` | JSON/CSV/Parquet files |
| `excel` | Excel files |
| `bloomberg` | Bloomberg BLPAPI |
| `refinitiv` | Refinitiv Eikon/RDP |

## API Endpoints

### Resolution Service

| Endpoint | Description |
|----------|-------------|
| `GET /resolve/{path}` | Resolve moniker → source connection info |
| `GET /list/{path}` | List children in catalog |
| `GET /describe/{path}` | Get metadata and ownership |
| `GET /lineage/{path}` | Get full ownership lineage |
| `GET /catalog` | List all catalog paths |
| `POST /telemetry/access` | Report access telemetry from client |
| `GET /health` | Health check |

### Example: Resolve

```bash
curl http://localhost:8000/resolve/market-data/prices/equity/AAPL
```

Response:
```json
{
  "moniker": "moniker://market-data/prices/equity/AAPL",
  "path": "market-data/prices/equity/AAPL",
  "source_type": "snowflake",
  "connection": {
    "account": "acme.us-east-1",
    "warehouse": "COMPUTE_WH",
    "database": "MARKET_DATA",
    "schema": "PRICES"
  },
  "query": "SELECT symbol, price FROM EQUITY_PRICES WHERE symbol = 'AAPL'",
  "ownership": {
    "accountable_owner": "jane.smith@firm.com",
    "data_specialist": "market-data-team@firm.com",
    "support_channel": "#market-data-support"
  }
}
```

## Telemetry

Two types of events are tracked:

1. **Resolution Events** (from service) - When someone asks where data lives
2. **Access Events** (from client) - When someone actually fetches data

Events include:
- Timestamp and request ID
- Caller identity (app_id, team)
- Moniker path and operation
- Outcome (success/error/not_found)
- Source type and latency
- Owner at time of access

Telemetry sinks:
- `console` - Print to stdout (development)
- `file` - Rotating JSONL files
- `zmq` - ZeroMQ PUB/SUB streaming

### ZeroMQ Streaming Demo

Stream telemetry events in real-time using ZeroMQ PUB/SUB:

```bash
# Install ZeroMQ
pip install pyzmq

# Terminal 1: Start service with ZMQ telemetry
python -m moniker_svc.main --config config_zmq.yaml

# Terminal 2: Subscribe to telemetry stream
python telemetry_subscriber.py
```

The subscriber shows events as they happen:

```
[14:32:15.123] RESOLVE  success    market-data/prices/equity/AAPL <- my-notebook (2.3ms)
[14:32:15.456] ACCESS   success    market-data/prices/equity/AAPL <- my-notebook (145.2ms) [snowflake]
```

Subscriber options:
```bash
# Show raw JSON
python telemetry_subscriber.py --raw

# Connect to different endpoint
python telemetry_subscriber.py --endpoint tcp://moniker-svc:5556

# Filter by topic
python telemetry_subscriber.py --topic moniker.access

# Verbose output with row counts
python telemetry_subscriber.py -v
```

For production, pipe telemetry to Kafka, Splunk, or your data warehouse by modifying `telemetry_subscriber.py` or implementing a custom sink.

## Catalog Definition

Define your catalog in `example_catalog.yaml`:

```yaml
market-data:
  display_name: Market Data
  ownership:
    accountable_owner: jane.smith@firm.com
    data_specialist: market-data-team@firm.com
    support_channel: "#market-data-support"

market-data/prices/equity:
  display_name: Equity Prices
  source_binding:
    type: snowflake
    config:
      account: acme.us-east-1
      warehouse: COMPUTE_WH
      database: MARKET_DATA
      schema: PRICES
      query: |
        SELECT symbol, price, currency, timestamp
        FROM EQUITY_PRICES
        WHERE symbol = '{path}'
```

## Project Structure

```
open-moniker-svc/
├── src/moniker_svc/           # Resolution Service
│   ├── main.py                # FastAPI application
│   ├── service.py             # Core resolution logic
│   ├── catalog/               # Hierarchy + ownership
│   │   ├── types.py           # Ownership, SourceBinding, CatalogNode
│   │   └── registry.py        # CatalogRegistry
│   ├── moniker/               # Path parsing
│   │   ├── types.py           # MonikerPath, Moniker
│   │   └── parser.py          # parse_moniker()
│   ├── telemetry/             # Event streaming
│   │   ├── events.py          # UsageEvent, CallerIdentity
│   │   ├── emitter.py         # Non-blocking emitter
│   │   ├── batcher.py         # Batch for efficiency
│   │   └── sinks/             # Console, File, ZMQ
│   ├── identity/              # Caller extraction
│   └── cache/                 # In-memory cache
│
├── client/moniker_client/     # Python Client Library
│   ├── client.py              # MonikerClient, read(), describe()
│   ├── config.py              # ClientConfig
│   └── adapters/              # Direct source connections
│       ├── snowflake.py
│       ├── oracle.py
│       ├── rest.py
│       ├── bloomberg.py
│       └── ...
│
├── tests/                     # Unit tests
├── demo.py                    # Interactive demo
├── config.yaml                # Service configuration
├── example_catalog.yaml       # Sample catalog
└── pyproject.toml             # Package configuration
```

## Installation Options

### Service

```bash
pip install -e .                    # Basic
pip install -e ".[dev]"             # With dev tools
```

### Client

```bash
pip install -e client/              # Basic
pip install -e "client/[snowflake]" # With Snowflake
pip install -e "client/[oracle]"    # With Oracle
pip install -e "client/[all]"       # All adapters
```

## License

MIT
