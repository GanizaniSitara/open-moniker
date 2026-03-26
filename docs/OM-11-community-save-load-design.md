# OM-11: File-Based Community Feedback, Save & Load System

## Context

The business-catalogue frontend has a rich contributions system (flags, suggestions, annotations, discussions, helpful votes) backed by Prisma/SQLite. With PostgreSQL removed, this needs to become file-based JSON storage served by the existing FastAPI management service. Okta JWT auth already exists and will be reused. The goal is zero frontend component changes — only the API transport layer changes.

---

## Approach: FastAPI Community Module + JSON File Storage

New Python package `src/moniker_svc/community/` following the exact 5-file pattern used by `requests/`, `domains/`, `models/` modules: types.py, registry.py, storage.py, models.py, routes.py. Frontend proxied via Next.js rewrite rule.

---

## Disk Layout

```
community_data/                        # configurable via sample_config.yaml
  entities/
    {entityType}/                      # e.g. "moniker"
      {entityKey}/                     # e.g. "pricing.fx.spot"
        flags.json
        suggestions.json
        annotations.json               # votes embedded in each annotation
        discussions.json               # replies embedded in each discussion
        helpful.json
  configs/                             # shared catalog snapshots (OM-11e)
    {uuid}/
      metadata.json                    # author, title, status, timestamps
      catalog.yaml                     # saved catalog snapshot
```

JSON chosen over YAML for contribution data (faster I/O, matches HTTP exchange format).

---

## Files to Create

### 1. `src/moniker_svc/community/__init__.py`
Package exports: CommunityRegistry, FileStorage, router, config_router.

### 2. `src/moniker_svc/community/types.py`
Frozen dataclasses + enums matching the Prisma schema exactly:
- Enums: `FlagType`, `FlagStatus`, `SuggestionStatus`, `AnnotationType`, `ConfigStatus`
- Dataclasses: `Flag`, `Suggestion`, `Annotation`, `AnnotationVote`, `Discussion`, `DiscussionReply`, `HelpfulVote`, `SharedConfig`
- Snake_case internally; Pydantic handles camelCase in models.py

### 3. `src/moniker_svc/community/registry.py`
Thread-safe in-memory store (pattern: `requests/registry.py`):
- `CommunityRegistry` with `threading.RLock`, keyed by `(entity_type, entity_key)` tuples
- CRUD methods for each contribution type
- Upvote uniqueness enforced in-memory (replaces Prisma `@@unique([annotationId, voter])`)
- `uuid4().hex` for ID generation
- `load_entity()` / `dump_entity()` for persistence round-trips

### 4. `src/moniker_svc/community/storage.py`
JSON file I/O with atomic writes:
- `_atomic_write(path, data)`: write to `.tmp`, fsync, `os.replace()` (crash-safe)
- `load_all()`: scan `entities/` directory at startup, populate registry
- `save_entity(entity_type, entity_key, data)`: persist one entity's contributions
- Config snapshot methods: `save_config_snapshot()`, `load_config_snapshot()`, `list_config_snapshots()`

### 5. `src/moniker_svc/community/models.py`
Pydantic models with `Field(alias="camelCase")` + `ConfigDict(populate_by_name=True, by_alias=True)`:
- Request models: `CreateFlagRequest`, `CreateSuggestionRequest`, `CreateAnnotationRequest`, `CreateDiscussionRequest`, `CreateReplyRequest`, `UpdateFlagStatusRequest`, `ReviewSuggestionRequest`, `UpvoteRequest`, `HelpfulVoteRequest`, `SaveConfigRequest`
- Response models: `FlagModel`, `SuggestionModel`, `AnnotationModel`, `DiscussionModel`, `DiscussionDetailModel`, `ReplyModel`, `FlagSummary`, `HelpfulSummary`, `ActivitySummary`, `ConfigSnapshotModel`

### 6. `src/moniker_svc/community/routes.py`
FastAPI `APIRouter(prefix="/community")` with `configure(registry, storage)`:

| Endpoint | Method | Maps to frontend call |
|---|---|---|
| `/community/flags` | GET, POST | `fetchFlags`, `createFlag` |
| `/community/flags/summary` | GET | `fetchFlagSummary` |
| `/community/flags/{id}/status` | PATCH | `updateFlagStatus` |
| `/community/suggestions` | GET, POST | `fetchSuggestions`, `createSuggestion` |
| `/community/suggestions/{id}/approve` | POST | approve workflow |
| `/community/suggestions/{id}/reject` | POST | reject workflow |
| `/community/annotations` | GET, POST | `fetchAnnotations`, `createAnnotation` |
| `/community/annotations/{id}/upvote` | POST, DELETE | `upvoteAnnotation`, `removeUpvote` |
| `/community/discussions` | GET, POST | `fetchDiscussions`, `createDiscussion` |
| `/community/discussions/{id}` | GET | `fetchDiscussion` (with replies) |
| `/community/discussions/{id}/replies` | POST | `addReply` |
| `/community/helpful` | GET, POST | `fetchHelpfulSummary`, `submitHelpfulVote` |
| `/community/activity` | GET | `fetchActivity` |

Each mutating endpoint calls `_auto_save(entity_type, entity_key)` after registry update.

### 7. `src/moniker_svc/community/config_routes.py`
FastAPI `APIRouter(prefix="/community/configs")`:
- `POST /` — snapshot current catalog (uses existing `CatalogSerializer`)
- `GET /` — list shared configs (optional `?status=published` filter)
- `GET /{id}` — get config metadata
- `POST /{id}/publish` — draft -> published
- `POST /{id}/fork` — copy published config to new draft under caller
- `POST /{id}/load` — load config into active catalog (uses `catalog.atomic_replace()`)

All endpoints use `Depends(get_caller_identity)` from existing auth.

---

## Files to Modify

### 8. `src/moniker_svc/config.py`
Add `CommunityConfig` dataclass:
```python
@dataclass
class CommunityConfig:
    enabled: bool = True
    data_dir: str = "community_data"
```
Add to `Config` class and `from_dict()`.

### 9. `sample_config.yaml`
Add `community:` section with `enabled: true`, `data_dir: "community_data"`.

### 10. `src/moniker_svc/_bootstrap.py`
Add `build_community_registry(config)` function following `build_request_registry()` pattern.

### 11. `src/moniker_svc/management_app.py`
- Import community routes
- In lifespan: build registry + storage, call `configure()`
- `app.include_router(community_routes.router)`
- `app.include_router(community_config_routes.config_router)`
- Add `"Community"` to `openapi_tags`

### 12. `business-catalogue/next.config.ts`
Add rewrite rule to proxy `/api/contributions/*` to `http://localhost:8052/community/*`. This means zero changes to `contributions-client.ts` or any frontend component.

---

## Implementation Order

1. **types.py** — domain types (no dependencies)
2. **storage.py** — file I/O (depends on types)
3. **registry.py** — in-memory store (depends on types)
4. **models.py** — Pydantic API models (depends on types)
5. **routes.py** — contribution endpoints (depends on registry, storage, models)
6. **config_routes.py** — shared config endpoints (depends on storage, catalog)
7. **__init__.py** — package wiring
8. **config.py** — add CommunityConfig
9. **sample_config.yaml** — add community section
10. **_bootstrap.py** — add build function
11. **management_app.py** — wire routers
12. **next.config.ts** — add rewrite proxy

---

## Key Design Decisions

- **JSON over YAML** for contributions: faster I/O, matches HTTP format
- **Per-entity directories**: reads are O(1) per entity, no single-file bottleneck
- **Embedded votes/replies**: votes inside annotations, replies inside discussions (matches Prisma `include` pattern frontend already expects)
- **Atomic writes**: write .tmp -> fsync -> os.replace (crash-safe, pattern from config_ui/routes.py)
- **camelCase aliases in Pydantic**: preserves exact JSON contract so frontend needs zero changes
- **Next.js rewrite proxy**: cleanest approach — no changes to contributions-client.ts at all
- **In-memory registry + file persistence**: same architecture as requests module (thread-safe, fast reads)

---

## Verification

1. Start management service: `PYTHONPATH=src uvicorn moniker_svc.management_app:app --port 8052`
2. Test contribution endpoints via curl:
   - `POST /community/flags` with JSON body
   - `GET /community/flags?entityType=moniker&entityKey=pricing.fx.spot`
   - Verify JSON files appear in `community_data/entities/moniker/pricing.fx.spot/`
3. Test shared configs:
   - `POST /community/configs` to snapshot catalog
   - `POST /community/configs/{id}/publish`
   - `GET /community/configs?status=published`
4. Start Next.js frontend, verify contributions UI loads and works through proxy
5. Restart management service, verify all data reloads from disk
