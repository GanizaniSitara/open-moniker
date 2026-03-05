# Plan: Split Resolver and Management into Separate Processes

## Context

The current service is a single FastAPI monolith (`main.py`, ~1700 lines) that mixes two very different workloads:

- **Resolver / data plane** — high-throughput, read-only, latency-sensitive. Benchmarked at ~600 req/s per process. This is what scales horizontally (6 instances, 3×AZ, 2 regions).
- **Management / control plane** — low-traffic, write-heavy, serves UIs. Should run centrally (1–2 instances), not replicated across every AZ.

Running them together means every resolver instance carries the weight of all management initialisation, all management routers, and unused in-memory state (ModelRegistry, RequestRegistry, etc.) — overhead on the hot path.

**Where APIs run after the split:**
- Resolver API (`port 8050`) → in each AZ behind an internal load balancer, client-facing
- Management API (`port 8060`) → centralised (1–2 instances per region), internal-only

Shared state is the YAML files on disk. Management writes → Resolver hot-reloads via `reload_interval_seconds: 60` (already in config) or on-demand via `POST /config/reload`.

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `src/moniker_svc/_bootstrap.py` | **Create** — shared init helpers extracted from `main.py` lifespan |
| `src/moniker_svc/resolver_app.py` | **Create** — resolver-only FastAPI entry point |
| `src/moniker_svc/management_app.py` | **Create** — management-only FastAPI entry point |
| `src/moniker_svc/main.py` | **Refactor** lifespan to call `_bootstrap` helpers; no route or behaviour changes |
| `CLAUDE.md` | **Update** with new start commands |

---

## Route Assignment

### Resolver process (`resolver_app.py`)

| Routes | Category |
|--------|----------|
| `GET /resolve/{path}`, `POST /resolve/batch` | Core resolution |
| `GET /describe/{path}`, `GET /lineage/{path}`, `GET /list/{path}` | Metadata |
| `GET /fetch/{path}`, `GET /metadata/{path}` | Server-side execution |
| `GET /catalog`, `/catalog/search`, `/catalog/stats` | Read-only browse |
| `GET /tree`, `GET /tree/{path}` | Read-only browse |
| `PUT /catalog/{path}/status`, `GET /catalog/{path}/audit` | Governance |
| `GET /cache/status`, `POST /cache/refresh/{path}` | Cache management |
| `POST /telemetry/access` | Tracking |
| `GET /health` | Health check |

**Initialises:** config, CatalogRegistry (read), DomainRegistry (read), InMemoryCache, TelemetryEmitter, MonikerService, AdapterRegistry, RateLimiter, CircuitBreaker, Auth.

**Does not initialise:** ModelRegistry, RequestRegistry, config_ui, dashboard.

### Management process (`management_app.py`)

| Routes | Category |
|--------|----------|
| `/config/*` | Catalog CRUD + save/reload |
| `/domains/*` | Domain CRUD |
| `/models/*` | Model CRUD |
| `/requests/*` | Approval workflow |
| `/dashboard/*` | Observability UI |
| `GET /` | Landing page |

**Initialises:** config, CatalogRegistry (read-write), DomainRegistry (read-write), ModelRegistry, RequestRegistry, config_ui, dashboard.

**Does not initialise:** AdapterRegistry, InMemoryCache, RateLimiter, TelemetryEmitter.

---

## `_bootstrap.py` — Shared Helpers

Extract the following pure functions from `main.py`'s `lifespan` block:

```python
def load_config(path=None) -> AppConfig
def build_catalog_registry(cfg) -> CatalogRegistry
def build_domain_registry(cfg) -> DomainRegistry
def build_cache(cfg) -> InMemoryCache
def build_adapter_registry() -> AdapterRegistry
async def build_telemetry(cfg) -> tuple[TelemetryEmitter, TelemetryBatcher]
def build_service(catalog, cache, emitter, cfg) -> MonikerService
def build_rate_limiter(cfg) -> RateLimiter | None
def build_circuit_breaker(cfg) -> CircuitBreaker | None
def build_auth(cfg) -> Authenticator | None
def build_model_registry(cfg) -> ModelRegistry | None
def build_request_registry(cfg, catalog, domains) -> RequestRegistry | None
```

`main.py` lifespan is then rewritten to call these (no behaviour change — full monolith still works).

---

## Resolver App Lifespan (sketch)

```python
@asynccontextmanager
async def lifespan(app):
    cfg     = load_config()
    catalog = build_catalog_registry(cfg)
    domains = build_domain_registry(cfg)
    cache   = build_cache(cfg)
    emitter, batcher = await build_telemetry(cfg)
    svc     = build_service(catalog, cache, emitter, cfg)
    svc.domain_registry = domains
    # wire globals consumed by resolver route handlers in main.py
    _set_resolver_globals(svc, catalog, domains, cache, ...)
    yield
    # shutdown: cancel tasks, stop telemetry
```

## Management App Lifespan (sketch)

```python
@asynccontextmanager
async def lifespan(app):
    cfg      = load_config()
    catalog  = build_catalog_registry(cfg)
    domains  = build_domain_registry(cfg)
    models   = build_model_registry(cfg)
    requests = build_request_registry(cfg, catalog, domains)
    config_ui_routes.configure(catalog, domains)
    domain_routes.configure(domains, catalog)
    model_routes.configure(models, catalog)
    request_routes.configure(requests, catalog, domains)
    dashboard_routes.configure(catalog, requests)
    yield
```

---

## YAML Backwards Compatibility

All three entry points (`main.py`, `resolver_app.py`, `management_app.py`) call the same `load_config()` helper, which reads `config.yaml` from the repo root exactly as today. No YAML schema changes. No new config keys required.

- `catalog.definition_file` → same path, read by both resolver and management
- `domains.yaml`, `models.yaml`, `requests.yaml` → same paths, read by management; resolver reads domains only (for ownership inheritance)
- `server.port` in config.yaml is ignored — the port is always passed as a uvicorn CLI flag (`--port 8051 / 8052`), so existing `config.yaml` with `port: 8050` doesn't conflict

An existing deployment pointing at `main:app` on port 8050 continues to work without any YAML edits.

---

## Shared-State Contract

```
┌──────────────────┐
│  Management API  │  port 8060  (1–2 instances per region)
│  writes YAMLs    │
└────────┬─────────┘
         │  catalog.yaml, domains.yaml, models.yaml, requests.yaml
         ▼
   [ filesystem / shared volume ]
         │  reload_interval_seconds: 60  (or POST /config/reload)
         ▼
┌────────────────────────────────┐
│       Resolver API             │  port 8050  (6 instances)
│  read-only, hot-reloads YAMLs  │
└────────────────────────────────┘
```

No Redis or message bus needed for catalog propagation for now.

---

## Updated Start Commands (CLAUDE.md)

```bash
# Resolver — run on all scaled instances
PYTHONPATH=src uvicorn moniker_svc.resolver_app:app --host 0.0.0.0 --port 8051

# Management — run once per region
PYTHONPATH=src uvicorn moniker_svc.management_app:app --host 0.0.0.0 --port 8052

# Legacy monolith (local dev / backwards compat — unchanged, keeps existing port)
PYTHONPATH=src uvicorn moniker_svc.main:app --host 0.0.0.0 --port 8050
```

---

## Verification

1. Start resolver on 8051 → `GET /health` 200; `GET /resolve/<any-path>` works; `GET /config/ui` → **404**.
2. Start management on 8052 → `GET /config/ui` returns HTML; `GET /resolve/<path>` → **404**.
3. Edit a node via management `PUT /config/nodes/<path>` + `POST /config/save`. Within 60 s, `GET /resolve/<path>` on resolver reflects change.
4. `python3 -m pytest tests/integration/ -x` against resolver on 8051 — all pass.
5. `python3 tests/stress/harness.py --workers 1 --duration 30 --port 8051` against resolver — throughput at ~600 req/s baseline.
6. Start legacy `main.py` on 8050 — still works (no regression).

---

## Implementation Order

1. **Read `main.py`** — identify exact lifespan block, all global variables, and how route modules are wired.
2. **Create `_bootstrap.py`** — extract init helpers, keeping original logic intact.
3. **Refactor `main.py` lifespan** — replace inline init with calls to `_bootstrap` functions (no behaviour change).
4. **Create `resolver_app.py`** — resolver lifespan + resolver routes only.
5. **Create `management_app.py`** — management lifespan + management routes only.
6. **Update `CLAUDE.md`** — add new start commands.
7. **Run verification steps** — smoke test all three entry points.
