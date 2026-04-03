# Open Moniker — Architecture Reference

> **Keep this file current.** It is loaded by task agents at session start to avoid
> redundant codebase exploration. Update it whenever modules are added, removed, or
> significantly changed.

---

## What it is

A unified data-access resolution layer. Clients pass a canonical path string (a *moniker*)
and receive back connection info + a parameterised query ready to execute. The service owns
no data — it owns the mapping from path to source.

---

## Path syntax (current — v0.3.0)

```
<segments>/<optional-reserved-segments>
```

### Positional segments
Plain slash-delimited path: `prices/equity/AAPL`

### `@id` identity parameter
Attach an identity value to any non-reserved segment:
```
holdings/positions@ACC001/summary   → segment_id = (1, "ACC001")
accounts@12345/transactions         → segment_id = (0, "12345")
```
- At most **one** `@id` per path
- Stripped before catalog lookup (`canonical_path` is always clean)
- Value: alphanumeric + `-_.`

### `date@VALUE` reserved segment (final position)
```
prices/equity/AAPL/date@20260101   → date_param = "20260101"
prices/equity/AAPL/date@3M         → date_param = "3M"
prices/equity/AAPL/date@latest     → date_param = "latest"
```
- `date` is a hard-reserved segment name
- Does NOT count against the one-`@id` limit
- Not included in `canonical_path`

### `filter@CODE` reserved segment (anywhere)
```
prices/equity/filter@xK9f2p        → expands via shortlink registry inline
holdings/positions@ACC001/filter@abc123
```
- `filter` is a hard-reserved segment name
- Expands `filter_segments` + `params` from the OM-10 shortlink store
- Does NOT count against the one-`@id` limit

### Removed syntax (do not use)
- ~~`prices/AAPL@20260101`~~ — `@version` suffix removed (OM-19)
- ~~`verified@reference.security/...`~~ — `namespace@` prefix removed (OM-23)
- ~~`~SHORTCODE`~~ — tilde shortlinks removed (OM-21)

---

## Moniker dataclass (`moniker/types.py`)

```python
@dataclass
class Moniker:
    path: str                          # raw input path
    segments: list[str]                # positional segments (clean, no @id)
    canonical_path: str                # clean path for catalog lookup
    segment_id: tuple[int, str] | None # (@id) index + value, e.g. (1, "ACC001")
    date_param: str | None             # date@VALUE, e.g. "20260101", "3M", "latest"
    filter_shortlink: str | None       # filter@CODE that was expanded
    revision: str | None               # /vN version revision
    query_params: dict[str, str]       # ?key=val from URL

# REMOVED fields (do not reference):
# version, version_type, sub_resource, namespace
```

---

## Module map

| Module | Purpose |
|--------|---------|
| `moniker/parser.py` | `parse_moniker()` — splits path, extracts `@id`, `date@`, `filter@`, validates |
| `moniker/types.py` | `Moniker` dataclass |
| `service.py` | `MonikerService.resolve()` — catalog lookup + template expansion |
| `dialect/base.py` | `VersionDialect` base — `resolve_date_param()`, `date_literal()`, `lookback_start()` |
| `dialect/placeholders.py` | All supported `{placeholder}` names + docs |
| `dialect/snowflake.py` | Snowflake SQL dialect |
| `dialect/oracle.py` | Oracle SQL dialect |
| `dialect/mssql.py` | MSSQL dialect |
| `dialect/rest.py` | REST/URL dialect |
| `catalog/registry.py` | In-memory catalog node registry |
| `catalog/loader.py` | YAML catalog loader |
| `shortlinks/store.py` | `try_expand_path()` — `filter@CODE` → segments expansion |
| `shortlinks/routes.py` | CRUD endpoints for shortlink registry |
| `community/` | File-based save/load, config snapshots, flags, suggestions (OM-11) |
| `domains/` | Domain ownership + governance metadata |
| `telemetry/` | Access event batching + sinks (console, file, ZMQ) |
| `auth/` | Okta/Kerberos auth, `get_caller_identity()` |
| `main.py` | FastAPI app entry point, `/resolve` handler |
| `mcp.py` | MCP server (streamable HTTP transport) |
| `_bootstrap.py` | Startup: loads catalog, domains, community data |

---

## Placeholder reference (current)

| Placeholder | Value |
|-------------|-------|
| `{segments[N]}` | Positional segment N |
| `{segment_id[N]}` | `@id` value if bound to segment N, else `""` |
| `{segment_id_value}` | Raw `@id` value regardless of position |
| `{segment_id_index}` | Index of segment carrying `@id` |
| `{has_segment_id}` | `"true"` / `"false"` |
| `{date_value}` | Raw `date@VALUE` string (e.g. `"20260101"`, `"3M"`) |
| `{date_sql}` | Dialect-aware SQL expression for the date |
| `{date_filter:COL}` | `COL = <date_sql>` or `1=1` if no date param |
| `{filter[N]:col}` | Filter value at segment N mapped to column |

### Removed placeholders (do not use)
`{version}`, `{version_type}`, `{is_date}`, `{is_latest}`, `{is_lookback}`,
`{is_frequency}`, `{is_all}`, `{lookback_value}`, `{lookback_unit}`, `{frequency}`,
`{version_date}`, `{lookback_start_sql}`, `{date_filter:col}` (old form),
`{segments[N]:date}`, `{segment_date_sql[N]}`, `{namespace}`, `{sub_resource}`

---

## Running tests

```bash
# Set PYTHONPATH (Windows PowerShell)
$env:PYTHONPATH = "$PWD;$PWD\client;$PWD\external\moniker-data\src"

# Full suite
C:/miniconda3/envs/python312/python.exe -m pytest tests/ -q

# Parser only
C:/miniconda3/envs/python312/python.exe -m pytest tests/integration/test_moniker_parser.py -v

# With coverage
C:/miniconda3/envs/python312/python.exe -m pytest tests/ --tb=short -q
```

---

## Alternative implementations

| Implementation | Location | Status |
|----------------|----------|--------|
| Python (canonical) | `moniker_svc/` | v0.3.0 — current |
| Java | `resolver-java/` | v0.3.1 — OM-17/OM-19 parity |
| Go | `resolver-go/` | v0.3.1 — OM-17/OM-19 parity |

See OM-24 for the delta audit between implementations.

---

## Key design decisions

- **`canonical_path` is always clean** — `@id`, `date@`, `filter@` are stripped before catalog lookup. The catalog never sees them.
- **`filter@` expands inline** — after expansion, the path contains normal positional segments. No `filter` field on `Moniker`.
- **One `@id` per path** — enforced by parser. `date@` and `filter@` are reserved and don't count.
- **No database** — all state (catalog, community, shortlinks) is file-based JSON on disk.
- **Atomic writes** — `temp → fsync → os.replace` pattern throughout community/storage.
