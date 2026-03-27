"""Oracle SQL dialect implementation."""

from __future__ import annotations

from .base import VersionDialect


class OracleDialect(VersionDialect):
    """Oracle SQL dialect for version type translation."""

    @property
    def name(self) -> str:
        return "oracle"

    def current_date(self) -> str:
        return "SYSDATE"

    def date_literal(self, date_str: str) -> str:
        """Convert YYYYMMDD to Oracle date literal."""
        return f"TO_DATE('{date_str}', 'YYYYMMDD')"

    def lookback_start(self, value: int, unit: str) -> str:
        """Generate Oracle date arithmetic for lookback.

        Oracle uses:
        - ADD_MONTHS(date, n) for months/years
        - date - n for days
        - date - n*7 for weeks
        """
        unit_upper = unit.upper()

        if unit_upper == "Y":
            # Years: use ADD_MONTHS with months * 12
            return f"ADD_MONTHS(SYSDATE, -{value * 12})"
        elif unit_upper == "M":
            # Months
            return f"ADD_MONTHS(SYSDATE, -{value})"
        elif unit_upper == "W":
            # Weeks: multiply by 7 days
            return f"SYSDATE - {value * 7}"
        else:
            # Days (default)
            return f"SYSDATE - {value}"
