# Shortlinks — Bitly-Style Filter Sharing

**Always on** — no feature toggle. Part of the Config UI module.

Shortlinks let users capture a complex filter-state snapshot (domain,
category, maturity, rating, etc.) into an 8-character short ID. The short
URL can be shared with colleagues, bookmarked, or embedded in dashboards.

```
Before:  /config/ui#?domain=finance&category=bonds&subcategory=sovereign&maturity=short&rating=AA+
After:   /config/m/xK9f2p_A
```

---

## Architecture

Shortlinks are **part of the monolith** — they ship as additional routes on
the existing `/config` API router inside the FastAPI service. No separate
process, port, or infrastructure is needed.

```
┌─────────────────────────────────────────────┐
│            moniker-svc (port 8050)          │
│                                             │
│  /resolve/*       ← moniker resolution      │
│  /catalog/*       ← governance & search      │
│  /config/nodes    ← catalog CRUD             │
│  /config/ui       ← Config UI HTML           │
│  /config/shortlinks  ← shortlink CRUD   ◄──  │
│  /config/m/{id}      ← short URL resolve ◄── │
│                                             │
│  ShortlinkRegistry ──► shortlinks.json      │
└─────────────────────────────────────────────┘
```

**Deployment:** Ships with the existing Render.com deploy (or wherever the
monolith runs). No config.yaml changes required — the registry initialises
automatically when the Config UI is enabled, placing `shortlinks.json`
alongside `catalog.yaml`.

---

## API

### Create a shortlink

```
POST /config/shortlinks
Content-Type: application/json

{
  "filters": {
    "domain": "finance",
    "category": "bonds",
    "subcategory": "sovereign",
    "maturity": "short",
    "rating": "AA+"
  },
  "path_prefix": "prices.bonds/sovereign",
  "label": "Short-dated gilts AA+"
}
```

Response (`201 Created`):

```json
{
  "short_id": "xK9f2p_A",
  "filters": { "domain": "finance", "category": "bonds", "subcategory": "sovereign", "maturity": "short", "rating": "AA+" },
  "path_prefix": "prices.bonds/sovereign",
  "label": "Short-dated gilts AA+",
  "created_at": 1743292800.0,
  "created_by": "",
  "short_url": "http://localhost:8050/config/m/xK9f2p_A"
}
```

### Resolve a short URL

```
GET /config/m/xK9f2p_A
```

Returns the stored filter state — the Config UI (or any client) uses
`path_prefix` + `filters` to reconstruct the original view:

```json
{
  "short_id": "xK9f2p_A",
  "path_prefix": "prices.bonds/sovereign",
  "filters": { "domain": "finance", "category": "bonds", "subcategory": "sovereign", "maturity": "short", "rating": "AA+" },
  "label": "Short-dated gilts AA+"
}
```

### Get a shortlink by ID

```
GET /config/shortlinks/xK9f2p_A
```

Returns the full `ShortlinkModel` (same shape as the create response).

### List all shortlinks

```
GET /config/shortlinks
```

```json
{
  "shortlinks": [ ... ],
  "total": 12
}
```

Newest first.

### Delete a shortlink

```
DELETE /config/shortlinks/xK9f2p_A
```

```json
{ "success": true, "short_id": "xK9f2p_A", "message": "Shortlink deleted" }
```

---

## Design Decisions

| Concern | Decision | Rationale |
|---|---|---|
| **ID generation** | `secrets.token_urlsafe(6)` → 8 base64url chars | ~281 trillion combinations, no external dependency |
| **Storage** | `shortlinks.json` file alongside `catalog.yaml` | Consistent with the no-DB philosophy; survives restarts |
| **Collision handling** | Regenerate, up to 5 retries | Statistically near-impossible at this ID length |
| **Expiry** | None — links persist until explicitly deleted | Simple; delete via API if needed |
| **Shareability** | Yes — short URLs are deterministic lookups | Anyone with the URL can resolve the filter state |
| **Stateful vs stateless** | Stateful (requires storage lookup) | Filter combinations are arbitrarily complex; can't be meaningfully compressed into a short stateless token |
| **Thread safety** | `threading.Lock` around writes | FastAPI runs with Uvicorn workers; each worker gets its own registry instance reading from the shared JSON file |

---

## Persistence

The registry writes to `shortlinks.json` using atomic rename
(`write → tmp → rename`) with `fsync` to prevent corruption on crash.

```json
[
  {
    "short_id": "xK9f2p_A",
    "filters": { "domain": "finance", "category": "bonds" },
    "path_prefix": "prices.bonds/sovereign",
    "label": "Short-dated gilts AA+",
    "created_at": 1743292800.0,
    "created_by": ""
  }
]
```

The file is loaded once at service startup. All mutations persist
immediately.

---

## Files

| File | Purpose |
|---|---|
| `moniker_svc/config_ui/shortlinks.py` | `ShortlinkRegistry` — thread-safe, file-backed store |
| `moniker_svc/config_ui/models.py` | `CreateShortlinkRequest`, `ShortlinkModel`, `ShortlinkListResponse` |
| `moniker_svc/config_ui/routes.py` | 5 new endpoints (`POST`/`GET`/`DELETE` shortlinks + `GET /config/m/{id}`) |
| `tests/test_shortlinks.py` | 16 tests (8 unit, 8 API integration) |

---

## Testing

```bash
cd open-moniker-svc
python -m pytest tests/test_shortlinks.py -v
```

16 tests: registry create/get/delete/list, persistence roundtrip,
and full API integration (create, resolve, list, delete, 404 paths).
