"""Tests for SQL/REST dialect template generation.

Run: C:/Anaconda3/envs/python312/python.exe -m pytest tests/test_dialects.py -v
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from moniker_svc.dialect.registry import DialectRegistry, get_dialect
from moniker_svc.dialect.snowflake import SnowflakeDialect
from moniker_svc.dialect.oracle import OracleDialect
from moniker_svc.dialect.mssql import MSSQLDialect
from moniker_svc.dialect.rest import RestDialect
from moniker_svc.dialect.placeholders import (
    PLACEHOLDERS,
    get_placeholder_help,
    list_placeholders,
    format_placeholder_reference,
    get_pattern,
)


# ===================================================================
# Registry
# ===================================================================

class TestDialectRegistry:
    def test_get_snowflake(self):
        d = get_dialect("snowflake")
        assert isinstance(d, SnowflakeDialect)
        assert d.name == "snowflake"

    def test_get_oracle(self):
        d = get_dialect("oracle")
        assert isinstance(d, OracleDialect)
        assert d.name == "oracle"

    def test_get_mssql(self):
        d = get_dialect("mssql")
        assert isinstance(d, MSSQLDialect)
        assert d.name == "mssql"

    def test_get_rest(self):
        d = get_dialect("rest")
        assert isinstance(d, RestDialect)
        assert d.name == "rest"

    def test_case_insensitive(self):
        assert isinstance(get_dialect("Snowflake"), SnowflakeDialect)
        assert isinstance(get_dialect("ORACLE"), OracleDialect)
        assert isinstance(get_dialect("MSSQL"), MSSQLDialect)
        assert isinstance(get_dialect("REST"), RestDialect)

    def test_unknown_defaults_to_snowflake(self):
        d = get_dialect("unknown_db")
        assert isinstance(d, SnowflakeDialect)

    def test_list_dialects(self):
        reg = DialectRegistry()
        names = reg.list_dialects()
        assert "snowflake" in names
        assert "oracle" in names
        assert "mssql" in names
        assert "rest" in names

    def test_register_custom(self):
        reg = DialectRegistry()
        reg.register(SnowflakeDialect())  # re-register is fine
        assert reg.get("snowflake").name == "snowflake"


# ===================================================================
# Snowflake Dialect
# ===================================================================

class TestSnowflakeDialect:
    @pytest.fixture
    def sf(self):
        return SnowflakeDialect()

    def test_name(self, sf):
        assert sf.name == "snowflake"

    def test_current_date(self, sf):
        assert sf.current_date() == "CURRENT_DATE()"

    def test_date_literal(self, sf):
        assert sf.date_literal("20260115") == "TO_DATE('20260115', 'YYYYMMDD')"

    def test_date_literal_different_date(self, sf):
        assert sf.date_literal("20251231") == "TO_DATE('20251231', 'YYYYMMDD')"

    def test_lookback_months(self, sf):
        assert sf.lookback_start(3, "M") == "DATEADD('MONTH', -3, CURRENT_DATE())"

    def test_lookback_years(self, sf):
        assert sf.lookback_start(1, "Y") == "DATEADD('YEAR', -1, CURRENT_DATE())"

    def test_lookback_weeks(self, sf):
        assert sf.lookback_start(2, "W") == "DATEADD('WEEK', -2, CURRENT_DATE())"

    def test_lookback_days(self, sf):
        assert sf.lookback_start(5, "D") == "DATEADD('DAY', -5, CURRENT_DATE())"

    def test_lookback_lowercase_unit(self, sf):
        assert sf.lookback_start(3, "m") == "DATEADD('MONTH', -3, CURRENT_DATE())"

    def test_lookback_unknown_unit_defaults_to_day(self, sf):
        assert sf.lookback_start(7, "X") == "DATEADD('DAY', -7, CURRENT_DATE())"

    def test_date_filter(self, sf):
        result = sf.date_filter("trade_date", 3, "M")
        assert result == "trade_date >= DATEADD('MONTH', -3, CURRENT_DATE())"

    def test_no_filter(self, sf):
        assert sf.no_filter() == "1=1"

    def test_latest_subquery_hint(self, sf):
        assert sf.latest_subquery_hint() == "'__LATEST__'"


# ===================================================================
# Oracle Dialect
# ===================================================================

class TestOracleDialect:
    @pytest.fixture
    def ora(self):
        return OracleDialect()

    def test_name(self, ora):
        assert ora.name == "oracle"

    def test_current_date(self, ora):
        assert ora.current_date() == "SYSDATE"

    def test_date_literal(self, ora):
        assert ora.date_literal("20260115") == "TO_DATE('20260115', 'YYYYMMDD')"

    def test_lookback_months(self, ora):
        assert ora.lookback_start(3, "M") == "ADD_MONTHS(SYSDATE, -3)"

    def test_lookback_years(self, ora):
        # Years converted to months * 12
        assert ora.lookback_start(2, "Y") == "ADD_MONTHS(SYSDATE, -24)"

    def test_lookback_weeks(self, ora):
        assert ora.lookback_start(2, "W") == "SYSDATE - 14"

    def test_lookback_days(self, ora):
        assert ora.lookback_start(5, "D") == "SYSDATE - 5"

    def test_lookback_unknown_unit_defaults_to_day(self, ora):
        assert ora.lookback_start(7, "X") == "SYSDATE - 7"

    def test_date_filter(self, ora):
        result = ora.date_filter("as_of", 6, "M")
        assert result == "as_of >= ADD_MONTHS(SYSDATE, -6)"


# ===================================================================
# MSSQL Dialect
# ===================================================================

class TestMSSQLDialect:
    @pytest.fixture
    def ms(self):
        return MSSQLDialect()

    def test_name(self, ms):
        assert ms.name == "mssql"

    def test_current_date(self, ms):
        assert ms.current_date() == "CAST(GETDATE() AS DATE)"

    def test_date_literal(self, ms):
        assert ms.date_literal("20260115") == "CONVERT(DATE, '20260115', 112)"

    def test_lookback_months(self, ms):
        assert ms.lookback_start(3, "M") == "DATEADD(MONTH, -3, CAST(GETDATE() AS DATE))"

    def test_lookback_years(self, ms):
        assert ms.lookback_start(1, "Y") == "DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))"

    def test_lookback_weeks(self, ms):
        assert ms.lookback_start(2, "W") == "DATEADD(WEEK, -2, CAST(GETDATE() AS DATE))"

    def test_lookback_days(self, ms):
        assert ms.lookback_start(10, "D") == "DATEADD(DAY, -10, CAST(GETDATE() AS DATE))"

    def test_lookback_unknown_unit_defaults_to_day(self, ms):
        assert ms.lookback_start(7, "X") == "DATEADD(DAY, -7, CAST(GETDATE() AS DATE))"

    def test_date_filter(self, ms):
        result = ms.date_filter("valuation_date", 1, "Y")
        assert result == "valuation_date >= DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))"


# ===================================================================
# REST Dialect
# ===================================================================

class TestRestDialect:
    @pytest.fixture
    def rest(self):
        return RestDialect()

    def test_name(self, rest):
        assert rest.name == "rest"

    def test_current_date_is_iso(self, rest):
        result = rest.current_date()
        # Should be today in YYYY-MM-DD format
        assert result == date.today().isoformat()

    def test_date_literal(self, rest):
        assert rest.date_literal("20260115") == "2026-01-15"

    def test_date_literal_leap_year(self, rest):
        assert rest.date_literal("20240229") == "2024-02-29"

    def test_lookback_days(self, rest):
        expected = (date.today() - timedelta(days=5)).isoformat()
        assert rest.lookback_start(5, "D") == expected

    def test_lookback_weeks(self, rest):
        expected = (date.today() - timedelta(weeks=2)).isoformat()
        assert rest.lookback_start(2, "W") == expected

    def test_lookback_months(self, rest):
        # relativedelta handles month arithmetic
        result = rest.lookback_start(3, "M")
        assert len(result) == 10  # YYYY-MM-DD format
        assert result < date.today().isoformat()  # in the past

    def test_lookback_years(self, rest):
        result = rest.lookback_start(1, "Y")
        assert len(result) == 10
        assert result < date.today().isoformat()

    def test_date_filter_returns_iso_date(self, rest):
        # REST date_filter returns just the ISO date (no SQL)
        result = rest.date_filter("col", 3, "M")
        assert len(result) == 10  # YYYY-MM-DD

    def test_no_filter_empty_string(self, rest):
        assert rest.no_filter() == ""


# ===================================================================
# Base dialect interface (via concrete implementations)
# ===================================================================

class TestBaseDialectInterface:
    """Test methods inherited from VersionDialect base class."""

    @pytest.mark.parametrize("dialect_name", ["snowflake", "oracle", "mssql"])
    def test_no_filter_returns_1_eq_1(self, dialect_name):
        d = get_dialect(dialect_name)
        assert d.no_filter() == "1=1"

    @pytest.mark.parametrize("dialect_name", ["snowflake", "oracle", "mssql"])
    def test_latest_subquery_hint(self, dialect_name):
        d = get_dialect(dialect_name)
        assert d.latest_subquery_hint() == "'__LATEST__'"

    @pytest.mark.parametrize("dialect_name", ["snowflake", "oracle", "mssql"])
    def test_date_filter_includes_column_name(self, dialect_name):
        d = get_dialect(dialect_name)
        result = d.date_filter("my_col", 1, "D")
        assert "my_col" in result
        assert ">=" in result


# ===================================================================
# Placeholders
# ===================================================================

class TestPlaceholders:
    def test_all_placeholders_have_required_fields(self):
        for name, info in PLACEHOLDERS.items():
            assert info.name, f"{name} missing name"
            assert info.description, f"{name} missing description"
            assert info.category in ("raw", "dialect", "segment")

    def test_get_placeholder_help_found(self):
        info = get_placeholder_help("path")
        assert info is not None
        assert info.name == "path"
        assert info.category == "raw"

    def test_get_placeholder_help_not_found(self):
        assert get_placeholder_help("nonexistent") is None

    def test_removed_alias_returns_none(self):
        info = get_placeholder_help("is_tenor")
        assert info is None

    def test_list_all(self):
        all_ph = list_placeholders()
        assert len(all_ph) == len(PLACEHOLDERS)

    def test_list_by_category(self):
        raw = list_placeholders("raw")
        assert all(p.category == "raw" for p in raw)
        assert len(raw) > 0

        dialect = list_placeholders("dialect")
        assert all(p.category == "dialect" for p in dialect)

    def test_format_reference_contains_all_categories(self):
        ref = format_placeholder_reference()
        assert "Raw Value Placeholders" in ref
        assert "Dialect-Aware SQL Placeholders" in ref
        assert "Path Segment Placeholders" in ref

    def test_old_segment_date_placeholders_removed(self):
        """segments[N]:date and segment_date_sql[N] replaced by date@ mechanism."""
        assert get_placeholder_help("segments[N]:date") is None
        assert get_placeholder_help("segment_date_sql[N]") is None

    def test_date_placeholders_exist(self):
        """New date@ placeholders are registered."""
        assert get_placeholder_help("date_value") is not None
        assert get_placeholder_help("date_sql") is not None
        assert get_placeholder_help("date_filter:COL") is not None

    def test_get_pattern(self):
        p = get_pattern("segment_filter_query")
        assert p is not None
        assert "{filter[0]:symbol}" in p

    def test_get_pattern_not_found(self):
        assert get_pattern("nonexistent") is None


# ===================================================================
# resolve_date_param (via dialect base class)
# ===================================================================

class TestResolveDateParam:
    """Tests for resolve_date_param across all dialects."""

    def test_absolute_snowflake(self):
        d = SnowflakeDialect()
        assert d.resolve_date_param("20260101") == "TO_DATE('20260101', 'YYYYMMDD')"

    def test_absolute_oracle(self):
        d = OracleDialect()
        assert d.resolve_date_param("20260115") == "TO_DATE('20260115', 'YYYYMMDD')"

    def test_absolute_mssql(self):
        d = MSSQLDialect()
        assert d.resolve_date_param("20260115") == "CONVERT(DATE, '20260115', 112)"

    def test_absolute_rest(self):
        d = RestDialect()
        assert d.resolve_date_param("20260115") == "2026-01-15"

    def test_latest_snowflake(self):
        d = SnowflakeDialect()
        assert d.resolve_date_param("latest") == "CURRENT_DATE()"

    def test_latest_oracle(self):
        d = OracleDialect()
        assert d.resolve_date_param("latest") == "SYSDATE"

    def test_latest_mssql(self):
        d = MSSQLDialect()
        assert d.resolve_date_param("latest") == "CAST(GETDATE() AS DATE)"

    def test_latest_rest(self):
        d = RestDialect()
        assert d.resolve_date_param("latest") == date.today().isoformat()

    def test_latest_case_insensitive(self):
        d = SnowflakeDialect()
        assert d.resolve_date_param("Latest") == "CURRENT_DATE()"
        assert d.resolve_date_param("LATEST") == "CURRENT_DATE()"

    def test_previous_snowflake(self):
        d = SnowflakeDialect()
        assert d.resolve_date_param("previous") == "DATEADD('DAY', -1, CURRENT_DATE())"

    def test_previous_oracle(self):
        d = OracleDialect()
        assert d.resolve_date_param("previous") == "SYSDATE - 1"

    def test_relative_3m_snowflake(self):
        d = SnowflakeDialect()
        assert d.resolve_date_param("3M") == "DATEADD('MONTH', -3, CURRENT_DATE())"

    def test_relative_1y_oracle(self):
        d = OracleDialect()
        assert d.resolve_date_param("1Y") == "ADD_MONTHS(SYSDATE, -12)"

    def test_relative_5d_mssql(self):
        d = MSSQLDialect()
        assert d.resolve_date_param("5D") == "DATEADD(DAY, -5, CAST(GETDATE() AS DATE))"

    def test_relative_2w_rest(self):
        d = RestDialect()
        expected = (date.today() - timedelta(weeks=2)).isoformat()
        assert d.resolve_date_param("2W") == expected
