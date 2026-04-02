"""Base dialect interface for version type translation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Literal


class VersionDialect(ABC):
    """Abstract base class for dialect-specific SQL/API generation.

    Each dialect implements translation of version types (date, lookback,
    frequency, etc.) into source-specific syntax.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the dialect name (e.g., 'snowflake', 'oracle', 'rest')."""
        ...

    @abstractmethod
    def current_date(self) -> str:
        """Return dialect-specific current date expression.

        Examples:
            Snowflake: CURRENT_DATE()
            Oracle: SYSDATE
            REST: 2026-02-05 (ISO format)
        """
        ...

    @abstractmethod
    def date_literal(self, date_str: str) -> str:
        """Convert a YYYYMMDD string to dialect-specific date literal.

        Args:
            date_str: Date string in YYYYMMDD format (e.g., "20260101")

        Returns:
            Dialect-specific date expression

        Examples:
            Snowflake: TO_DATE('20260101', 'YYYYMMDD')
            Oracle: TO_DATE('20260101', 'YYYYMMDD')
            REST: 2026-01-01 (ISO format)
        """
        ...

    @abstractmethod
    def lookback_start(self, value: int, unit: str) -> str:
        """Generate lookback date expression.

        Args:
            value: Numeric lookback amount (e.g., 3)
            unit: Unit character: Y (year), M (month), W (week), D (day)

        Returns:
            Dialect-specific date arithmetic expression

        Examples:
            Snowflake @3M: DATEADD('MONTH', -3, CURRENT_DATE())
            Oracle @3M: ADD_MONTHS(SYSDATE, -3)
            REST @3M: 2025-11-05 (calculated ISO date)
        """
        ...

    def date_filter(self, column: str, value: int, unit: str) -> str:
        """Generate a complete WHERE clause fragment for lookback filtering.

        Args:
            column: Column name to filter on
            value: Lookback amount
            unit: Lookback unit (Y/M/W/D)

        Returns:
            SQL WHERE clause fragment (e.g., "col >= DATEADD(...)")
        """
        lookback_sql = self.lookback_start(value, unit)
        return f"{column} >= {lookback_sql}"

    def no_filter(self) -> str:
        """Return a no-op filter (for @all version type)."""
        return "1=1"

    def latest_subquery_hint(self) -> str:
        """Return a hint/placeholder for @latest version.

        @latest typically requires a subquery (SELECT MAX(date) FROM ...)
        which is catalog-defined. This returns a placeholder.
        """
        return "'__LATEST__'"

    def resolve_date_param(self, value: str) -> str:
        """Resolve a date@ parameter value to a dialect-specific expression.

        Handles:
            - Absolute dates: "20260101" → dialect-specific date literal
            - Symbolic: "latest" → current date, "previous" → current date - 1
            - Relative: "3M", "1Y", "5D" → dialect-specific date arithmetic

        Args:
            value: The raw date parameter value (e.g., "20260101", "latest", "3M")

        Returns:
            Dialect-specific SQL expression or date string
        """
        import re

        lower = value.lower()

        # Symbolic values
        if lower == "latest":
            return self.current_date()
        if lower == "previous":
            return self._previous_date()

        # Absolute date (YYYYMMDD)
        if len(value) == 8 and value.isdigit():
            return self.date_literal(value)

        # Relative lookback (e.g., 3M, 1Y, 5D, 2W)
        rel_match = re.match(r"^(\d+)([YMWD])$", value, re.IGNORECASE)
        if rel_match:
            amount = int(rel_match.group(1))
            unit = rel_match.group(2).upper()
            return self.lookback_start(amount, unit)

        # Fallback: return as quoted string
        return f"'{value}'"

    def _previous_date(self) -> str:
        """Return dialect-specific expression for previous business day (current_date - 1).

        Subclasses may override for more specific behaviour.
        """
        return self.lookback_start(1, "D")
