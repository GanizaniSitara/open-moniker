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
    category: Literal["raw", "dialect", "segment"]


# All available placeholders with documentation
PLACEHOLDERS: dict[str, PlaceholderInfo] = {
    # Raw value placeholders
    "path": PlaceholderInfo(
        name="path",
        description="Full sub-path after the catalog binding",
        example_input="prices/equity/AAPL",
        example_output="equity/AAPL",
        category="raw",
    ),
    "revision": PlaceholderInfo(
        name="revision",
        description="Revision number from /vN suffix",
        example_input="prices/AAPL/v2",
        example_output="2",
        category="raw",
    ),
    "namespace": PlaceholderInfo(
        name="namespace",
        description="Namespace prefix if provided",
        example_input="prod@prices/AAPL",
        example_output="prod",
        category="raw",
    ),
    "moniker": PlaceholderInfo(
        name="moniker",
        description="Full moniker string as provided",
        example_input="prices/AAPL",
        example_output="moniker://prices/AAPL",
        category="raw",
    ),

    # Dialect-aware SQL placeholders
    "current_date": PlaceholderInfo(
        name="current_date",
        description="Dialect-specific current date (CURRENT_DATE(), SYSDATE, ISO)",
        example_input="(any moniker)",
        example_output="CURRENT_DATE()  # Snowflake",
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

    # Segment identity placeholders (in-path @id)
    "segment_id[N]": PlaceholderInfo(
        name="segment_id[N]",
        description="Identity value from segment N (only if that segment carries @id)",
        example_input="holdings/positions@ACC001/summary with {segment_id[1]}",
        example_output="ACC001",
        category="segment",
    ),
    "segment_id_value": PlaceholderInfo(
        name="segment_id_value",
        description="Raw identity value regardless of which segment carries it",
        example_input="holdings/positions@ACC001/summary",
        example_output="ACC001",
        category="segment",
    ),
    "segment_id_index": PlaceholderInfo(
        name="segment_id_index",
        description="Index of the segment carrying the @id identity",
        example_input="holdings/positions@ACC001/summary",
        example_output="1",
        category="segment",
    ),
    "has_segment_id": PlaceholderInfo(
        name="has_segment_id",
        description="'true' if any segment has an @id identity, else 'false'",
        example_input="holdings/positions@ACC001/summary",
        example_output="true",
        category="segment",
    ),
}


def get_placeholder_help(name: str) -> PlaceholderInfo | None:
    """Get documentation for a placeholder by name."""
    return PLACEHOLDERS.get(name)


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

    return "\n".join(lines)
