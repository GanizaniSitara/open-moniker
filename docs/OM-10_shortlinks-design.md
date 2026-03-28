# OM-10: Bitly-style Filter Shortlinks for Moniker Resolution

## Context

Client applications (Python/Go/Java) resolve monikers like:
```
fixed.income/govies/sovereign/US/10Y/SHORT_DATED@3M?format=json&limit=1000
```
The base path (`fixed.income/govies/sovereign`) is meaningful and navigable, but the filter segments + version + params tail gets long and unwieldy.

This feature adds **tilde-prefixed short aliases** that replace only the filter tail:
```
Before:  fixed.income/govies/sovereign/US/10Y/SHORT_DATED@3M?format=json&limit=1000
After:   fixed.income/govies/sovereign/~xK9f2p
```

The `~` prefix is URL-safe (unreserved in RFC 3986) and invalid in moniker segments (`^[a-zA-Z0-9][a-zA-Z0-9_.\-]*$`), so there's zero ambiguity — the resolver sees a `~` segment and knows it's a shortlink.

---

## Approach

### New module: `src/moniker_svc/shortlinks/`

Follows the existing module pattern (domains, applications, requests):

| File | Purpose |
|------|---------|
| `__init__.py` | Public exports |
| `types.py` | `Shortlink` frozen dataclass + `generate_short_id()` (deterministic base62 from SHA-256) |
| `store.py` | Thread-safe in-memory store (`RLock`) + JSON file persistence (atomic write via temp+replace) |
| `models.py` | Pydantic request/response models for CRUD API |
| `routes.py` | `APIRouter(prefix="/s")` with `configure()` pattern, CRUD endpoints |

### Data model (stored in `shortlinks.json`)

```json
{
  "xK9f2p": {
    "id": "xK9f2p",
    "base_path": "fixed.income/govies/sovereign",
    "filter_segments": ["US", "10Y", "SHORT_DATED"],
    "version": "3M",
    "params": {"format": "json", "limit": "1000"},
    "label": "US 10Y short-dated govies JSON",
    "created_by": "jsmith@firm.com",
    "created_at": "2026-03-25T14:30:00Z"
  }
}
```

The shortlink captures a **full snapshot** of everything after the base moniker path: filter segments, version, and query params. When expanded, it reconstructs the complete moniker string.

### How expansion works

Client sends: `GET /resolve/fixed.income/govies/sovereign/~xK9f2p`

1. Resolver scans path segments, finds one starting with `~`
2. Everything before `~xK9f2p` is the base path: `fixed.income/govies/sovereign`
3. Looks up `xK9f2p` in the store → gets filter_segments, version, params
4. Reconstructs full moniker: `fixed.income/govies/sovereign/US/10Y/SHORT_DATED@3M?format=json&limit=1000`
5. Resolves normally, returns standard `ResolveResponse`
6. Sets `redirected_from` to `~xK9f2p` (reuses existing API field, no SDK changes)

### ID generation

- Deterministic: SHA-256 of canonical filter string → first 48 bits → 7-char base62
- Same filter combo always produces the same short ID (dedup built-in)
- On collision (different filter, same hash prefix): retry with random fallback

### CRUD API (`/s` prefix)

| Method | Path | Description |
|--------|------|-------------|
| `POST /s` | Create shortlink (body: `{base_path, filter_segments, version?, params?, label?}`) → 201 or 200 if dedup |
| `GET /s` | List all shortlinks |
| `GET /s/{id}` | Inspect a shortlink by ID |
| `DELETE /s/{id}` | Delete a shortlink |

### Inline resolution — the key integration

Modify the existing `resolve_moniker()` handler at **main.py:1187-1197**. After the path is extracted but before `moniker_str` is built:

```python
# Current code (lines 1188-1197):
full_path = request.url.path
if full_path.startswith("/resolve/"):
    path = full_path[9:]
moniker_str = f"moniker://{path}"
if request.query_params:
    ...

# New code — detect ~ segment and expand:
full_path = request.url.path
if full_path.startswith("/resolve/"):
    path = full_path[9:]

shortlink_alias = None
if _shortlink_store:
    expanded, alias = _shortlink_store.try_expand_path(path)
    if alias:
        shortlink_alias = alias
        path = expanded

moniker_str = f"moniker://{path}"
if not shortlink_alias and request.query_params:
    # Only append client query params for non-shortlink requests
    # (shortlinks have params baked in)
    params = list(request.query_params.items())
    if params:
        moniker_str += "?" + "&".join(f"{k}={v}" for k, v in params)
```

The `try_expand_path()` method on the store scans path segments for a `~`-prefixed one, looks up the ID, and returns the expanded path with filter segments/version/params spliced in. Returns `(original_path, None)` if no tilde segment found.

Then after the response is built (line ~1253), set `redirected_from`:
```python
if shortlink_alias:
    response.redirected_from = shortlink_alias
```

This reuses the existing `redirected_from` field and `X-Moniker-Redirected-From` header — no SDK changes needed.

### Multi-resolver architecture

All three resolvers (Python, Go, Java) are **independent implementations** — each loads the catalog from YAML and resolves locally. None proxy to each other.

This means shortlink expansion must work in all three. The approach:

1. **Shared JSON file** (`shortlinks.json`) sits alongside the catalog YAML — all resolvers read it at startup
2. **Python service is the write master** — CRUD API lives only in Python (`POST /s`, etc.)
3. **Go and Java resolvers are read-only consumers** — they load `shortlinks.json` at startup and expand `~` segments during resolution, but don't create/delete shortlinks
4. **File-watching or reload endpoint** for Go/Java to pick up new shortlinks without restart (mirrors existing catalog reload pattern)

This keeps the CRUD surface small (one implementation) while giving all resolvers the ability to expand shortlinks locally with zero network overhead.

### Scale path

**Phase 1 (this PR): File-based**
- `shortlinks.json` alongside catalog YAML
- In-memory map loaded at startup in all resolvers
- Python write-through on create/delete
- Go/Java read on startup + reload endpoint

**Phase 2 (future): Shared backend**
- Move storage to SQLite or Redis
- All resolvers connect to shared store
- Enables real-time sync without file watching
- The `ShortlinkStore` interface stays the same — just swap the backend

### Config and bootstrap wiring (Python)

**`config.py`** — add after `RequestsConfig`:
```python
@dataclass
class ShortlinksConfig:
    enabled: bool = True
    storage_file: str = "shortlinks.json"
```
Add to `Config` class and `from_dict()`.

**`_bootstrap.py`** — add `build_shortlink_store()` following the `build_request_registry()` pattern.

**`main.py`** — import shortlink_routes, add `_shortlink_store` global, init in lifespan, `app.include_router(shortlink_routes.router)`.

### Go resolver integration

- New `internal/shortlinks/` package: `store.go` (load JSON, in-memory map, `TryExpandPath()`)
- Wire into `internal/service/service.go` `Resolve()` — scan for `~` segment before parsing moniker
- Config: `shortlinks.storage_file` field in Go config struct
- Startup: load JSON in `cmd/resolver/main.go`

### Java resolver integration

- New `shortlinks/` package: `ShortlinkStore.java` (load JSON, ConcurrentHashMap, `tryExpandPath()`)
- Wire into `MonikerService.java` `resolve()` — scan for `~` segment before parsing
- Config: `shortlinks.storageFile` in Spring config
- Startup: load JSON in `MonikerResolverApplication.java`

---

## Files to modify

### Python
| File | Change |
|------|--------|
| `src/moniker_svc/config.py` | Add `ShortlinksConfig` dataclass, wire into `Config` |
| `src/moniker_svc/_bootstrap.py` | Add `build_shortlink_store()` |
| `src/moniker_svc/main.py` | Import, lifespan init, router include, resolve handler `~` expansion |

### Go
| File | Change |
|------|--------|
| `resolver-go/internal/service/service.go` | Add shortlink expansion before `ParseMoniker()` call |
| `resolver-go/cmd/resolver/main.go` | Load shortlinks JSON at startup |

### Java
| File | Change |
|------|--------|
| `resolver-java/.../service/MonikerService.java` | Add shortlink expansion before `parseMoniker()` call |
| `resolver-java/.../MonikerResolverApplication.java` | Load shortlinks JSON at startup |

## Files to create

### Python
| File | Purpose |
|------|---------|
| `src/moniker_svc/shortlinks/__init__.py` | Exports |
| `src/moniker_svc/shortlinks/types.py` | `Shortlink` dataclass + ID generation |
| `src/moniker_svc/shortlinks/store.py` | Thread-safe store + JSON persistence + `try_expand_path()` |
| `src/moniker_svc/shortlinks/models.py` | Pydantic request/response models |
| `src/moniker_svc/shortlinks/routes.py` | CRUD API router (write master) |
| `tests/test_shortlinks.py` | Unit + integration tests |

### Go
| File | Purpose |
|------|---------|
| `resolver-go/internal/shortlinks/store.go` | Load JSON, in-memory map, `TryExpandPath()` |

### Java
| File | Purpose |
|------|---------|
| `resolver-java/.../shortlinks/ShortlinkStore.java` | Load JSON, ConcurrentHashMap, `tryExpandPath()` |

---

## Verification

1. **Unit tests (Python)**: ID generation determinism, store CRUD, persistence roundtrip, dedup, `try_expand_path()` with/without tilde
2. **Unit tests (Go)**: `TryExpandPath()` expansion, JSON loading, missing tilde passthrough
3. **Unit tests (Java)**: `tryExpandPath()` expansion, JSON loading, missing tilde passthrough
4. **Integration tests (Python)**: All 4 CRUD endpoints, `GET /resolve/base/path/~id` transparent expansion, `redirected_from` field set, normal resolve paths unaffected
5. **Cross-resolver test**: Create shortlink via Python `POST /s`, resolve via Go and Java resolvers (after reload), verify identical results
