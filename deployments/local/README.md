# Local Development Deployment

Fast iteration with dev/UAT environments. No Docker required. Supports Java and Go resolvers.

## Quick Start

```bash
# Start dev environment (default: Java resolver)
python3 bootstrap.py dev

# Start dev with Go resolver
python3 bootstrap.py dev --resolver go

# Start UAT for demos
python3 bootstrap.py uat

# Run both side-by-side
python3 bootstrap.py both

# Check status
python3 bootstrap.py status

# Stop everything
python3 bootstrap.py stop
```

## Architecture

Each environment (dev/uat) runs:
- **1x Resolver** (Java OR Go, your choice)
- **1x Python Management** (FastAPI)
- **1x SQLite Database** (telemetry)

All services share config/catalog YAML files.

## Ports

| Environment | Java | Go | Python |
|-------------|------|-----|---------|
| **dev** | 8054 | 8053 | 8052 |
| **uat** | 9054 | 9053 | 9052 |

## Directory Structure

```
deployments/local/
├── bootstrap.py          # Main orchestrator
├── dev/
│   ├── config.yaml      # Dev config (auto-generated from sample)
│   ├── catalog.yaml     # Dev catalog (auto-generated)
│   └── telemetry.db     # SQLite telemetry database
├── uat/
│   ├── config.yaml      # UAT config
│   ├── catalog.yaml     # UAT catalog (stable for demos)
│   └── telemetry.db     # Separate UAT telemetry
└── README.md            # This file
```

## Testing

```bash
# Test Java resolver (dev)
curl http://localhost:8054/health
curl http://localhost:8054/resolve/reference
curl http://localhost:8054/resolve/prices.equity/AAPL@latest

# Test Go resolver (dev)
curl http://localhost:8053/health
curl http://localhost:8053/resolve/reference

# Test Python management
curl http://localhost:8052/config
curl http://localhost:8052/health
open http://localhost:8052/dashboard

# Check telemetry database
sqlite3 dev/telemetry.db "SELECT COUNT(*) FROM access_log;"
```

## Performance Benchmarking

```bash
# Benchmark Java
hey -z 30s -c 100 http://localhost:8054/resolve/test/path@latest

# Benchmark Go
hey -z 30s -c 100 http://localhost:8053/resolve/test/path@latest

# Expected results (MacBook Pro M1):
# Java: ~8,500 req/s
# Go: ~21,000 req/s
```

## Switching Between Java and Go

The resolvers are **interchangeable**. Both support:
- Parent node resolution (returns children)
- Leaf node resolution (source bindings)
- Full telemetry to SQLite
- Same API contract

To switch:
```bash
# Stop current resolver
python3 bootstrap.py stop dev

# Start with different resolver
python3 bootstrap.py dev --resolver go
```

## Troubleshooting

### Java resolver won't start
```bash
# Build Java resolver
cd resolver-java
mvn clean package -DskipTests
```

### Go resolver won't start
```bash
# Build Go resolver
cd resolver-go
make build
```

### Python service fails
```bash
# Install dependencies
pip install -r requirements.txt

# Check PYTHONPATH
export PYTHONPATH=/home/user/open-moniker-svc/src
```

### Port already in use
```bash
# Kill process on port 8054
lsof -ti :8054 | xargs kill -9

# Or use different ports by editing bootstrap.py
```

## Hot Reload

The Python management service supports hot reload:
1. Edit `sample_config.yaml` or `sample_catalog.yaml`
2. POST to `/config/reload`
3. Changes applied without restart

Java and Go resolvers require restart for config changes.

## Backwards Compatibility

The Python monolith can run alongside:

```bash
# Terminal 1: Java resolver (dev)
python3 bootstrap.py dev

# Terminal 2: Python monolith (backwards compat)
cd ~/open-moniker-svc
PYTHONPATH=src uvicorn moniker_svc.main:app --port 8050
```

All three can coexist and share the same config/catalog files.
