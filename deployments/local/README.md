# Local Development Environment

Quick start guide for running Open Moniker locally with Python app + Java/Go resolvers.

## One-Command Quick Start

```bash
# Start everything, run tests, verify, and open dashboard
python3 quick_start.py
```

This single command:
1. ✅ Starts Python app (port 8050) + Java resolver (port 8054)
2. ✅ Runs health checks
3. ✅ Generates test traffic (15s)
4. ✅ Verifies telemetry is working
5. ✅ Opens dashboard in browser

**Stop everything:**
```bash
python3 quick_start.py --stop
```

---

## Manual Control (Advanced)

### Bootstrap Script

**Start services:**
```bash
python3 bootstrap.py dev           # Start dev environment
python3 bootstrap.py uat           # Start UAT environment
python3 bootstrap.py both          # Run both side-by-side
```

**Stop services:**
```bash
python3 bootstrap.py stop dev      # Stop dev
python3 bootstrap.py stop uat      # Stop UAT
python3 bootstrap.py stop both     # Stop all
```

**What it does:**
- Starts Python app (main.py) on configured port
- Starts Java resolver on configured port
- Manages PID files in `.pids/`
- Logs to `dev-python.log` and `dev-java.log`

### Load Tester

**Generate test traffic:**
```bash
cd ../../tests
python3 load_tester.py --duration 60 --concurrent 10 --rps 20
```

**Options:**
- `--duration`: Test duration in seconds (default: 30)
- `--concurrent`: Number of concurrent workers (default: 10)
- `--rps`: Target requests per second (default: 50)
- `--url`: Base URL (default: http://localhost:8054)

**Examples:**
```bash
# Light load for 30 seconds
python3 load_tester.py --duration 30 --rps 10

# Heavy load for 2 minutes
python3 load_tester.py --duration 120 --concurrent 20 --rps 100

# Stress test
python3 load_tester.py --duration 60 --concurrent 50 --rps 500
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Python App (main.py)                                   │
│  Port: 8050 (dev) / 9050 (uat)                         │
│  - Admin UI & config management                         │
│  - Live telemetry dashboard                             │
│  - Catalog CRUD operations                              │
│  - Can also handle resolution (for dev/testing)         │
└─────────────────────────────────────────────────────────┘
                          ↓
               Shared Catalog YAML Files
                          ↓
         ┌────────────────┴────────────────┐
         ↓                                  ↓
┌──────────────────┐              ┌──────────────────┐
│ Java Resolver    │              │ Go Resolver      │
│ Port: 8054 (dev) │              │ Port: 8053       │
│ High-performance │              │ High-performance │
│ Complementary    │              │ Complementary    │
└──────────────────┘              └──────────────────┘
         ↓                                  ↓
         └────────────────┬─────────────────┘
                          ↓
               Shared Telemetry Database
                 (SQLite or PostgreSQL)
```

**All three can run together:**
- Python manages catalog files
- Java/Go read same catalog files (hot-reload on changes)
- All write to same telemetry database
- Dashboard shows metrics from all resolvers

---

## Ports

### Dev Environment
- **8050** - Python app (main.py)
- **8053** - Go resolver (if running)
- **8054** - Java resolver

### UAT Environment
- **9050** - Python app (main.py)
- **9053** - Go resolver (if running)
- **9054** - Java resolver

---

## Configuration

Each environment has its own config directory:

```
dev/
├── config.yaml           # Python app config
├── catalog.yaml          # Catalog definition
└── telemetry.db          # SQLite telemetry database

uat/
├── config.yaml           # UAT config
├── catalog.yaml          # UAT catalog
└── telemetry.db          # UAT telemetry database
```

**Key config options:**

```yaml
# config.yaml
project_name: "Open Moniker"

# Telemetry (via environment variables)
TELEMETRY_DB_TYPE: sqlite
TELEMETRY_DB_PATH: ./dev/telemetry.db

# For production (PostgreSQL)
TELEMETRY_DB_TYPE: postgres
TELEMETRY_DB_HOST: localhost
TELEMETRY_DB_PORT: 5432
TELEMETRY_DB_NAME: moniker_telemetry
TELEMETRY_DB_USER: telemetry
TELEMETRY_DB_PASSWORD: secret
```

---

## URLs

### Python App (8050)
- **Landing Page:** http://localhost:8050/
- **Live Telemetry:** http://localhost:8050/telemetry
- **Config UI:** http://localhost:8050/config/ui
- **Catalog Browser:** http://localhost:8050/ui
- **Dashboard:** http://localhost:8050/dashboard/ui
- **Swagger Docs:** http://localhost:8050/docs
- **Health:** http://localhost:8050/health

### Java Resolver (8054)
- **Health:** http://localhost:8054/health
- **Resolve:** http://localhost:8054/resolve/commodities/crypto@latest
- **Catalog:** http://localhost:8054/catalog

### Go Resolver (8053)
- **Health:** http://localhost:8053/health
- **Resolve:** http://localhost:8053/resolve/commodities/crypto@latest

---

## Testing

**Manual curl tests:**
```bash
# Test Python app
curl http://localhost:8050/health

# Test Java resolver
curl http://localhost:8054/health
curl http://localhost:8054/resolve/commodities/crypto@latest

# Test Go resolver (if running)
curl http://localhost:8053/health
```

**Load testing:**
```bash
# Generate sustained traffic to populate telemetry
python3 ../../tests/load_tester.py --duration 60 --rps 20

# Watch telemetry dashboard update in real-time
open http://localhost:8050/telemetry
```

---

## Troubleshooting

**Services won't start:**
```bash
# Check logs
tail -f dev-python.log
tail -f dev-java.log

# Check if ports are in use
lsof -i :8050
lsof -i :8054

# Force kill if needed
python3 bootstrap.py stop dev
pkill -f "uvicorn moniker_svc.main"
pkill -f "resolver-java"
```

**Telemetry not showing data:**
```bash
# Check database has records
sqlite3 dev/telemetry.db "SELECT COUNT(*) FROM access_log;"

# Check recent records
sqlite3 dev/telemetry.db "SELECT timestamp, resolver_id, moniker FROM access_log ORDER BY id DESC LIMIT 5;"

# Generate test traffic
python3 ../../tests/load_tester.py --duration 30 --rps 10
```

**Config changes not taking effect:**
```bash
# Restart services to reload config
python3 bootstrap.py stop dev
python3 bootstrap.py dev
```

---

## Development Workflow

**1. Start dev environment:**
```bash
python3 quick_start.py
```

**2. Make changes to code**

**3. Restart to test:**
```bash
python3 quick_start.py --stop
python3 quick_start.py
```

**4. Run side-by-side dev + UAT:**
```bash
python3 bootstrap.py both
# Dev on 8050, UAT on 9050
```

---

## Scripts Summary

| Script | Purpose | Usage |
|--------|---------|-------|
| **quick_start.py** | One-command start + test + verify | `python3 quick_start.py` |
| **bootstrap.py** | Service management (start/stop) | `python3 bootstrap.py dev` |
| **../../tests/load_tester.py** | Generate test traffic | `python3 load_tester.py --rps 20` |

---

## Files

- `quick_start.py` - One-command start + test + verify
- `bootstrap.py` - Service management (start/stop)
- `dev/` - Dev environment config and data
- `uat/` - UAT environment config and data
- `.pids/` - PID files for running services
- `*.log` - Service logs
