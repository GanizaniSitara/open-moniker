# Changelog

All notable changes to this project will be documented in this file.

Versioning follows [Semantic Versioning](https://semver.org/):
- **Patch** (0.x.Y) — bug fixes, no API change
- **Minor** (0.X.0) — new features, backward compatible  
- **Major** (X.0.0) — breaking changes to path syntax, placeholder names, or `Moniker` fields

---

## [0.3.0] — 2026-04-02

### Breaking — `~SHORTCODE` removed

The `~SHORTCODE` shortlink syntax is replaced by `filter@SHORTCODE`. This is a clean break
to establish a consistent `name@value` pattern throughout the moniker path syntax. All URLs,
API responses, and code referencing `~` shortlinks must update to `filter@`.

### Added
- **`filter@CODE` reserved segment** — shortlink expansion via the OM-10 shortlink registry.
  `filter` is a globally hard-reserved segment name; the parser recognises it before falling
  through to entity `@id` logic. Does NOT count against the one-`@id`-per-path limit.
  Can appear anywhere in the path.
  - Syntax: `prices/equity/filter@xK9f2p`, `holdings/positions@ACC001/filter@abc123`
  - Expansion splices stored `filter_segments` in-place and merges stored `params` into
    query parameters (client params override on conflict)
  - **File changed**: `moniker/parser.py` — `_FILTER_PREFIX`, detection before `date@` and
    `@id` scans, `shortlink_store` optional parameter on `parse_moniker()`; reserved-word
    check in namespace parser to prevent `filter` being consumed as a namespace
  - **File changed**: `moniker/types.py` — `filter_shortlink: str | None` field on `Moniker`
    dataclass (tracks which `filter@CODE` was expanded); updated `with_namespace()` to
    preserve the field
  - **File changed**: `shortlinks/store.py` — `try_expand_path()` detects `filter@` instead
    of `~`; expansion now splices filter segments in-place (preserving surrounding segments)
    rather than returning `link.expand()` wholesale
  - **File changed**: `shortlinks/routes.py` — `resolve_path` in `_to_model()` uses
    `filter@{id}` instead of `~{id}`
  - **File changed**: `shortlinks/models.py` — updated `resolve_path` comment
  - **File changed**: `service.py` — `resolve()` accepts optional `shortlink_store` kwarg,
    passes to `parse_moniker()`; sets `redirected_from` from `filter_shortlink` on the
    parsed moniker
  - **File changed**: `main.py` — removed `~` expansion block from resolve handler; passes
    `_shortlink_store` to `_service.resolve()`; catches `MonikerParseError` for unknown
    shortlink codes (returns 404)

### Removed
- **`~SHORTCODE` shortlink syntax** — the tilde-prefix expansion mechanism is fully removed.
  `try_expand_path()` no longer recognises `~`-prefixed segments.
  - **File changed**: `shortlinks/store.py` — `_TILDE` constant removed, replaced by
    `_FILTER_PREFIX`

### Migration
- Any URL or client code using `~CODE` (e.g. `/resolve/prices/equity/~xK9f2p`) must change
  to `filter@CODE` (e.g. `/resolve/prices/equity/filter@xK9f2p`)
- API response field `resolve_path` now returns `base_path/filter@{id}` instead of
  `base_path/~{id}`
- The `redirected_from` response field now contains `filter@{id}` instead of `~{id}`

---

## [0.2.0] — 2026-04-02

### Added
- **`date@VALUE` reserved segment** — explicit date parameter as the final path segment.
  `date` is a globally hard-reserved segment name; the parser recognises it before falling
  through to entity `@id` logic. Does NOT count against the one-`@id`-per-path limit.
  - Syntax: `prices/equity/AAPL/date@20260101`, `date@latest`, `date@3M`, `date@previous`
  - Supported values: absolute (`YYYYMMDD`), relative (`3M`, `1Y`, `5D`, `2W`),
    symbolic (`latest`, `previous`)
  - **File added/changed**: `moniker/parser.py` — `DATE_PARAM_PATTERN`, extraction logic
    before `@id` scan, validation
  - **File changed**: `moniker/types.py` — `date_param: str | None` field on `Moniker`
    dataclass; updated `__str__` to include `date@VALUE` in representation; stripped from
    `canonical_path` (not part of catalog lookup) and not a positional segment
- New placeholders in `dialect/placeholders.py`:
  - `{date_value}` — raw date parameter value (e.g. `"20260101"`, `"latest"`, `"3M"`)
  - `{date_sql}` — dialect-aware SQL expression from `date@VALUE`
    (e.g. `TO_DATE('20260101', 'YYYYMMDD')` for Snowflake, `SYSDATE` for `latest` on Oracle)
  - `{date_filter:COL}` — `COL = <date_sql>`, or `1=1` if no date param present
  - **File changed**: `dialect/placeholders.py` — new entries in `PLACEHOLDERS` dict
- `resolve_date_param(value: str) -> str` method on `VersionDialect` base class —
  dispatches to `date_literal()`, `current_date()`, or `lookback_start()` per value type.
  All four dialects (Snowflake, Oracle, MSSQL, REST) inherit automatically.
  - **File changed**: `dialect/base.py` — new method + `_previous_date()` helper
- **File changed**: `service.py` `_format_template()` — wires `{date_value}`, `{date_sql}`,
  `{date_filter:COL}` into template expansion

### Removed
- `{segments[N]:date}` placeholder — was: YYYYMMDD segment formatted as YYYY-MM-DD.
  Replaced by `{date_value}` from the `date@VALUE` mechanism.
  - **File changed**: `dialect/placeholders.py`, `service.py`
- `{segment_date_sql[N]}` placeholder — was: dialect-aware SQL from a positional segment.
  Replaced by `{date_sql}` from the `date@VALUE` mechanism.
  - **File changed**: `dialect/placeholders.py`, `service.py`

### Migration
- Any catalog templates using `{segments[N]:date}` must change to `{date_value}` and move
  the date from a positional path segment to `date@VALUE` at the end of the path.
- Any catalog templates using `{segment_date_sql[N]}` must change to `{date_sql}`.
- Example before: `prices/equity/AAPL/20260101` with `{segment_date_sql[2]}`
- Example after: `prices/equity/AAPL/date@20260101` with `{date_sql}`
