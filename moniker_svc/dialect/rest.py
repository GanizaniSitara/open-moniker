"""REST API dialect implementation - returns ISO date strings."""

from __future__ import annotations

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from .base import VersionDialect


class RestDialect(VersionDialect):
    """REST API dialect - returns ISO date strings instead of SQL.

    This dialect is useful for REST APIs that expect ISO 8601 date
    parameters rather than SQL expressions.
    """

    @property
    def name(self) -> str:
        return "rest"

    def current_date(self) -> str:
        """Return today's date in ISO format."""
        return date.today().isoformat()

    def date_literal(self, date_str: str) -> str:
        """Convert YYYYMMDD to ISO date format (YYYY-MM-DD)."""
        # Parse YYYYMMDD and format as ISO
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        return date(year, month, day).isoformat()

    def lookback_start(self, value: int, unit: str) -> str:
        """Calculate lookback date and return as ISO string.

        Returns the actual calculated date rather than SQL expression.
        """
        today = date.today()
        unit_upper = unit.upper()

        if unit_upper == "Y":
            result = today - relativedelta(years=value)
        elif unit_upper == "M":
            result = today - relativedelta(months=value)
        elif unit_upper == "W":
            result = today - timedelta(weeks=value)
        else:
            # Days (default)
            result = today - timedelta(days=value)

        return result.isoformat()

    def date_filter(self, column: str, value: int, unit: str) -> str:
        """For REST, return the date parameter as a key-value style.

        Unlike SQL dialects, REST APIs typically use query parameters.
        Returns a simple ISO date that can be used as a parameter value.
        """
        return self.lookback_start(value, unit)

    def no_filter(self) -> str:
        """REST doesn't use SQL-style no-op filters."""
        return ""
