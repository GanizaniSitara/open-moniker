"""Placeholder documentation and helpers for catalog template authors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PlaceholderInfo:
    """Documentation for a single placeholder."""
    name: str
    description: str
    example_input: str
    example_output: str
    category: Literal["raw", "version", "dialect", "segment"]


# All available placeholders with documentation
PLACEHOLDERS: dict[str, PlaceholderInfo] = {
    # Raw value placeholders
    "path": PlaceholderInfo(
        name="path",
        description="Full sub-path after the catalog binding",
        example_input="prices/equity/AAPL@3M",
        example_output="equity/AAPL",
        category="raw",
    ),
    "version": PlaceholderInfo(
        name="version",
        description="Raw version string from @suffix",
        example_input="prices/AAPL@3M",
        example_output="3M",
        category="raw",
    ),
    "revision": PlaceholderInfo(
        name="revision",
        description="Revision number from /vN suffix",
        example_input="prices/AAPL@latest/v2",
        example_output="2",
        category="raw",
    ),
    "namespace": PlaceholderInfo(
        name="namespace",
        description="Namespace prefix if provided",
        example_input="prod@prices/AAPL@latest",
        example_output="prod",
        category="raw",
    ),
    "moniker": PlaceholderInfo(
        name="moniker",
        description="Full moniker string as provided",
        example_input="prices/AAPL@3M",
        example_output="moniker://prices/AAPL@3M",
        category="raw",
    ),
    "sub_resource": PlaceholderInfo(
        name="sub_resource",
        description="Sub-resource path after @version (dot-separated)",
        example_input="securities/ABC@20260101/details.corporate",
        example_output="details.corporate",
        category="raw",
    ),

    # Version type placeholders
    "version_type": PlaceholderInfo(
        name="version_type",
        description="Semantic version type: date, latest, lookback, frequency, all, custom",
        example_input="prices/AAPL@3M",
        example_output="lookback",
        category="version",
    ),
    "is_date": PlaceholderInfo(
        name="is_date",
        description="'true' if version is YYYYMMDD date format",
        example_input="prices/AAPL@20260101",
        example_output="true",
        category="version",
    ),
    "is_latest": PlaceholderInfo(
        name="is_latest",
        description="'true' if version is 'latest'",
        example_input="prices/AAPL@latest",
        example_output="true",
        category="version",
    ),
    "is_lookback": PlaceholderInfo(
        name="is_lookback",
        description="'true' if version is lookback period (3M, 1Y, 2W, 5D)",
        example_input="prices/AAPL@3M",
        example_output="true",
        category="version",
    ),
    "is_frequency": PlaceholderInfo(
        name="is_frequency",
        description="'true' if version is frequency (daily, weekly, monthly)",
        example_input="prices/AAPL@daily",
        example_output="true",
        category="version",
    ),
    "is_all": PlaceholderInfo(
        name="is_all",
        description="'true' if version is 'all' (full time series)",
        example_input="prices/AAPL@all",
        example_output="true",
        category="version",
    ),
    "lookback_value": PlaceholderInfo(
        name="lookback_value",
        description="Numeric part of lookback period",
        example_input="prices/AAPL@3M",
        example_output="3",
        category="version",
    ),
    "lookback_unit": PlaceholderInfo(
        name="lookback_unit",
        description="Unit of lookback: Y (year), M (month), W (week), D (day)",
        example_input="prices/AAPL@3M",
        example_output="M",
        category="version",
    ),
    "frequency": PlaceholderInfo(
        name="frequency",
        description="Frequency value: daily, weekly, or monthly",
        example_input="prices/AAPL@weekly",
        example_output="weekly",
        category="version",
    ),

    # Dialect-aware SQL placeholders
    "current_date": PlaceholderInfo(
        name="current_date",
        description="Dialect-specific current date (CURRENT_DATE(), SYSDATE, ISO)",
        example_input="(any moniker)",
        example_output="CURRENT_DATE()  # Snowflake",
        category="dialect",
    ),
    "version_date": PlaceholderInfo(
        name="version_date",
        description="Dialect-specific SQL for the version date",
        example_input="prices/AAPL@20260115",
        example_output="TO_DATE('20260115', 'YYYYMMDD')",
        category="dialect",
    ),
    "lookback_start_sql": PlaceholderInfo(
        name="lookback_start_sql",
        description="Dialect-specific lookback start date SQL",
        example_input="prices/AAPL@3M",
        example_output="DATEADD('MONTH', -3, CURRENT_DATE())",
        category="dialect",
    ),
    "date_filter:COL": PlaceholderInfo(
        name="date_filter:COL",
        description="Complete WHERE clause for date column COL",
        example_input="prices/AAPL@3M with {date_filter:trade_date}",
        example_output="trade_date >= DATEADD('MONTH', -3, CURRENT_DATE())",
        category="dialect",
    ),

    # Segment placeholders
    "segments[N]": PlaceholderInfo(
        name="segments[N]",
        description="Specific path segment by index (0-based)",
        example_input="prices/equity/AAPL with {segments[1]}",
        example_output="equity",
        category="segment",
    ),
    "filter[N]:COL": PlaceholderInfo(
        name="filter[N]:COL",
        description="SQL filter for segment N on column COL. 'ALL' becomes 1=1",
        example_input="prices/ALL/AAPL with {filter[1]:sector}",
        example_output="1=1",
        category="segment",
    ),
    "is_all[N]": PlaceholderInfo(
        name="is_all[N]",
        description="'true' if segment N is 'ALL'",
        example_input="prices/ALL/AAPL with {is_all[1]}",
        example_output="true",
        category="segment",
    ),
    "segments[N]:date": PlaceholderInfo(
        name="segments[N]:date",
        description="Path segment formatted as date (YYYYMMDD → YYYY-MM-DD)",
        example_input="risk/20260101/100 with {segments[0]:date}",
        example_output="2026-01-01",
        category="segment",
    ),
    "segment_date_sql[N]": PlaceholderInfo(
        name="segment_date_sql[N]",
        description="Path segment as dialect-aware SQL date expression",
        example_input="risk/20260101/100 with {segment_date_sql[0]}",
        example_output="TO_DATE('20260101', 'YYYYMMDD')",
        category="dialect",
    ),
}

# Backward compatibility aliases
PLACEHOLDER_ALIASES: dict[str, str] = {
    "is_tenor": "is_lookback",
    "tenor_value": "lookback_value",
    "tenor_unit": "lookback_unit",
}


def get_placeholder_help(name: str) -> PlaceholderInfo | None:
    """Get documentation for a placeholder by name."""
    if name in PLACEHOLDERS:
        return PLACEHOLDERS[name]
    if name in PLACEHOLDER_ALIASES:
        return PLACEHOLDERS.get(PLACEHOLDER_ALIASES[name])
    return None


def list_placeholders(category: str | None = None) -> list[PlaceholderInfo]:
    """List all placeholders, optionally filtered by category."""
    if category is None:
        return list(PLACEHOLDERS.values())
    return [p for p in PLACEHOLDERS.values() if p.category == category]


def format_placeholder_reference() -> str:
    """Generate a formatted reference guide for all placeholders."""
    lines = [
        "# Moniker Template Placeholder Reference",
        "",
        "Use these placeholders in catalog query templates.",
        "",
    ]

    categories = [
        ("raw", "Raw Value Placeholders"),
        ("version", "Version Type Placeholders"),
        ("dialect", "Dialect-Aware SQL Placeholders"),
        ("segment", "Path Segment Placeholders"),
    ]

    for cat_id, cat_name in categories:
        lines.append(f"## {cat_name}")
        lines.append("")
        lines.append("| Placeholder | Description | Example |")
        lines.append("|-------------|-------------|---------|")

        for p in list_placeholders(cat_id):
            lines.append(f"| `{{{p.name}}}` | {p.description} | `{p.example_output}` |")

        lines.append("")

    # Add aliases section
    lines.append("## Backward Compatibility Aliases")
    lines.append("")
    lines.append("| Alias | Maps To |")
    lines.append("|-------|---------|")
    for alias, target in PLACEHOLDER_ALIASES.items():
        lines.append(f"| `{{{alias}}}` | `{{{target}}}` |")
    lines.append("")

    return "\n".join(lines)


# Quick reference for common patterns
COMMON_PATTERNS = {
    "lookback_query": """\
-- Query with lookback date filter
SELECT * FROM {table}
WHERE {date_filter:trade_date}
  AND symbol = '{segments[0]}'
""",
    "frequency_table": """\
-- Select table based on frequency
SELECT * FROM prices_{frequency}
WHERE symbol = '{segments[0]}'
""",
    "conditional_date": """\
-- Conditional date handling
SELECT * FROM prices
WHERE CASE
    WHEN {is_lookback} = 'true' THEN trade_date >= {lookback_start_sql}
    WHEN {is_date} = 'true' THEN trade_date = {version_date}
    WHEN {is_all} = 'true' THEN 1=1
    ELSE trade_date = {current_date}
END
""",
}


def get_pattern(name: str) -> str | None:
    """Get a common query pattern by name."""
    return COMMON_PATTERNS.get(name)
