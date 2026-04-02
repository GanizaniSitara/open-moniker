# Changelog

All notable changes to this project will be documented in this file.

Versioning follows [Semantic Versioning](https://semver.org/):
- **Patch** (0.x.Y) — bug fixes, no API change
- **Minor** (0.X.0) — new features, backward compatible  
- **Major** (X.0.0) — breaking changes to path syntax, placeholder names, or `Moniker` fields

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
