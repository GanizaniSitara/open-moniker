"""Snowflake SQL dialect implementation."""

from __future__ import annotations

from .base import VersionDialect


class SnowflakeDialect(VersionDialect):
    """Snowflake SQL dialect for version type translation."""

    @property
    def name(self) -> str:
        return "snowflake"

    def current_date(self) -> str:
        return "CURRENT_DATE()"

    def date_literal(self, date_str: str) -> str:
        """Convert YYYYMMDD to Snowflake date literal."""
        return f"TO_DATE('{date_str}', 'YYYYMMDD')"

    def lookback_start(self, value: int, unit: str) -> str:
        """Generate Snowflake DATEADD expression for lookback.

        Snowflake uses: DATEADD(part, amount, date)
        """
        unit_upper = unit.upper()
        unit_map = {
            "Y": "YEAR",
            "M": "MONTH",
            "W": "WEEK",
            "D": "DAY",
        }
        sql_unit = unit_map.get(unit_upper, "DAY")
        return f"DATEADD('{sql_unit}', -{value}, CURRENT_DATE())"
