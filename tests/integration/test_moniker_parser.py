"""Tests for moniker parsing."""

import pytest

from moniker_svc.moniker.parser import (
    parse_moniker,
    parse_path,
    MonikerParseError,
)
from moniker_svc.moniker.types import MonikerPath


class TestParsePath:
    def test_simple_path(self):
        path = parse_path("market-data/prices/equity")
        assert path.segments == ("market-data", "prices", "equity")
        assert str(path) == "market-data/prices/equity"

    def test_path_with_leading_slash(self):
        path = parse_path("/market-data/prices")
        assert path.segments == ("market-data", "prices")

    def test_path_with_trailing_slash(self):
        path = parse_path("market-data/prices/")
        assert path.segments == ("market-data", "prices")

    def test_empty_path(self):
        path = parse_path("")
        assert path.segments == ()
        assert path == MonikerPath.root()

    def test_root_path(self):
        path = parse_path("/")
        assert path.segments == ()

    def test_single_segment(self):
        path = parse_path("market-data")
        assert path.segments == ("market-data",)
        assert path.domain == "market-data"

    def test_invalid_segment_start(self):
        with pytest.raises(MonikerParseError):
            parse_path("-invalid")

    def test_invalid_segment_chars(self):
        with pytest.raises(MonikerParseError):
            parse_path("path/with spaces")


class TestMonikerPath:
    def test_domain(self):
        path = MonikerPath(("market-data", "prices", "equity"))
        assert path.domain == "market-data"

    def test_parent(self):
        path = MonikerPath(("market-data", "prices", "equity"))
        parent = path.parent
        assert parent is not None
        assert parent.segments == ("market-data", "prices")

    def test_parent_at_root(self):
        path = MonikerPath(("market-data",))
        assert path.parent is None

    def test_leaf(self):
        path = MonikerPath(("market-data", "prices", "equity"))
        assert path.leaf == "equity"

    def test_ancestors(self):
        path = MonikerPath(("a", "b", "c", "d"))
        ancestors = path.ancestors()
        assert len(ancestors) == 3
        assert str(ancestors[0]) == "a"
        assert str(ancestors[1]) == "a/b"
        assert str(ancestors[2]) == "a/b/c"

    def test_child(self):
        path = MonikerPath(("market-data", "prices"))
        child = path.child("equity")
        assert child.segments == ("market-data", "prices", "equity")

    def test_is_ancestor_of(self):
        parent = MonikerPath(("a", "b"))
        child = MonikerPath(("a", "b", "c", "d"))
        assert parent.is_ancestor_of(child)
        assert not child.is_ancestor_of(parent)
        assert not parent.is_ancestor_of(parent)


class TestParseMoniker:
    def test_with_scheme(self):
        m = parse_moniker("moniker://market-data/prices/equity")
        assert str(m.path) == "market-data/prices/equity"
        assert not m.params

    def test_without_scheme(self):
        m = parse_moniker("market-data/prices/equity")
        assert str(m.path) == "market-data/prices/equity"

    def test_with_query_params(self):
        m = parse_moniker("moniker://market-data/prices?version=latest&as_of=2024-01-01")
        assert m.params.version == "latest"
        assert m.params.as_of == "2024-01-01"

    def test_str_roundtrip(self):
        original = "moniker://market-data/prices/equity"
        m = parse_moniker(original)
        assert str(m) == original

    def test_str_with_params(self):
        m = parse_moniker("moniker://path?version=v1")
        assert "version=v1" in str(m)

    def test_empty_moniker(self):
        with pytest.raises(MonikerParseError):
            parse_moniker("")

    def test_invalid_scheme(self):
        with pytest.raises(MonikerParseError):
            parse_moniker("http://market-data/prices")


class TestAtVersionRemoved:
    """Verify that @version syntax is rejected (OM-19)."""

    def test_at_version_date_raises(self):
        with pytest.raises(MonikerParseError, match="Invalid use of '@'"):
            parse_moniker("prices/AAPL@20260101")

    def test_at_latest_raises(self):
        with pytest.raises(MonikerParseError, match="Invalid use of '@'"):
            parse_moniker("prices/AAPL@latest")

    def test_at_all_raises(self):
        with pytest.raises(MonikerParseError, match="Invalid use of '@'"):
            parse_moniker("prices/AAPL@all")

    def test_at_lookback_raises(self):
        with pytest.raises(MonikerParseError, match="Invalid use of '@'"):
            parse_moniker("prices/AAPL@3M")

    def test_at_frequency_raises(self):
        with pytest.raises(MonikerParseError, match="Invalid use of '@'"):
            parse_moniker("prices/AAPL@daily")

    def test_at_custom_raises(self):
        with pytest.raises(MonikerParseError, match="Invalid use of '@'"):
            parse_moniker("prices/AAPL@custom123")


class TestSegmentId:
    """Tests for in-path @id identity parameters."""

    def test_segment_id_basic(self):
        m = parse_moniker("holdings/positions@ACC001/summary")
        assert m.segment_id == (1, "ACC001")
        assert str(m.path) == "holdings/positions/summary"

    def test_segment_id_first_segment_with_namespace(self):
        """Segment 0 @id requires namespace prefix to avoid ambiguity."""
        m = parse_moniker("prod@portfolios@FUND_ALPHA/holdings")
        assert m.namespace == "prod"
        assert m.segment_id == (0, "FUND_ALPHA")
        assert str(m.path) == "portfolios/holdings"

    def test_segment_id_numeric(self):
        m = parse_moniker("holdings/accounts@12345/transactions/recent")
        assert m.segment_id == (1, "12345")
        assert str(m.path) == "holdings/accounts/transactions/recent"

    def test_segment_id_with_dots_and_hyphens(self):
        m = parse_moniker("holdings/accounts@ACC-001.v2/transactions")
        assert m.segment_id == (1, "ACC-001.v2")
        assert str(m.path) == "holdings/accounts/transactions"

    def test_segment_id_path_cleaned_for_catalog(self):
        """The @id is stripped from the segment for catalog lookup."""
        m = parse_moniker("holdings/positions@ACC001/summary")
        assert m.path.segments == ("holdings", "positions", "summary")

    def test_mid_path_at_is_segment_id(self):
        """@ in a non-final segment is always segment identity."""
        m = parse_moniker("securities/012345678@20260101/details")
        assert m.segment_id == (1, "20260101")
        assert str(m.path) == "securities/012345678/details"

    def test_segment_id_with_namespace(self):
        m = parse_moniker("prod@holdings/positions@ACC001/summary")
        assert m.namespace == "prod"
        assert m.segment_id == (1, "ACC001")
        assert str(m.path) == "holdings/positions/summary"

    def test_multiple_at_ids_raises(self):
        with pytest.raises(MonikerParseError, match="At most one"):
            parse_moniker("domain/holdings@X/positions@Y/summary")

    def test_empty_segment_id_raises(self):
        with pytest.raises(MonikerParseError, match="Empty @id"):
            parse_moniker("domain/holdings@/summary")

    def test_invalid_segment_id_chars(self):
        with pytest.raises(MonikerParseError, match="Invalid segment identity"):
            parse_moniker("domain/holdings@ACC 001/summary")

    def test_segment_id_preserved_by_with_namespace(self):
        m = parse_moniker("holdings/positions@ACC001/summary")
        m2 = m.with_namespace("prod")
        assert m2.segment_id == (1, "ACC001")

    def test_segment_id_str_roundtrip(self):
        """__str__ must preserve @id so parse(str(m)) == m."""
        m = parse_moniker("holdings/positions@ACC001/summary")
        s = str(m)
        assert "positions@ACC001" in s
        m2 = parse_moniker(s)
        assert m2.segment_id == m.segment_id
        assert m2.path == m.path

    def test_segment_id_full_path(self):
        m = parse_moniker("holdings/positions@ACC001/summary/v2")
        assert "positions@ACC001" in m.full_path
        assert m.full_path == "holdings/positions@ACC001/summary/v2"

    def test_segment_id_canonical_path_is_clean(self):
        """canonical_path is for catalog lookup — no @id."""
        m = parse_moniker("holdings/positions@ACC001/summary")
        assert m.canonical_path == "holdings/positions/summary"

    def test_segment_id_catalog_path_clean(self):
        """str(moniker.path) must remain clean (no @id) for catalog lookup."""
        m = parse_moniker("holdings/positions@ACC001/summary")
        assert str(m.path) == "holdings/positions/summary"


class TestDateParam:
    """Tests for date@VALUE reserved segment parsing."""

    def test_date_absolute(self):
        m = parse_moniker("prices/equity/AAPL/date@20260101")
        assert m.date_param == "20260101"
        assert str(m.path) == "prices/equity/AAPL"
        assert m.segment_id is None

    def test_date_latest(self):
        m = parse_moniker("prices/equity/AAPL/date@latest")
        assert m.date_param == "latest"
        assert str(m.path) == "prices/equity/AAPL"

    def test_date_previous(self):
        m = parse_moniker("prices/equity/AAPL/date@previous")
        assert m.date_param == "previous"

    def test_date_relative_months(self):
        m = parse_moniker("prices/equity/AAPL/date@3M")
        assert m.date_param == "3M"
        assert str(m.path) == "prices/equity/AAPL"

    def test_date_relative_years(self):
        m = parse_moniker("prices/equity/AAPL/date@1Y")
        assert m.date_param == "1Y"

    def test_date_relative_weeks(self):
        m = parse_moniker("prices/equity/AAPL/date@2W")
        assert m.date_param == "2W"

    def test_date_relative_days(self):
        m = parse_moniker("prices/equity/AAPL/date@5D")
        assert m.date_param == "5D"

    def test_date_stripped_from_canonical_path(self):
        """date@VALUE must not appear in canonical_path (used for catalog lookup)."""
        m = parse_moniker("prices/equity/AAPL/date@20260101")
        assert m.canonical_path == "prices/equity/AAPL"
        assert "date" not in m.canonical_path

    def test_date_not_in_segments(self):
        """date@ is not a positional segment."""
        m = parse_moniker("prices/equity/AAPL/date@20260101")
        assert m.path.segments == ("prices", "equity", "AAPL")

    def test_date_with_segment_id(self):
        """date@ and @id can coexist."""
        m = parse_moniker("holdings/positions@ACC001/summary/date@20260101")
        assert m.segment_id == (1, "ACC001")
        assert m.date_param == "20260101"
        assert str(m.path) == "holdings/positions/summary"

    def test_date_with_revision(self):
        m = parse_moniker("prices/equity/AAPL/date@20260101/v2")
        assert m.date_param == "20260101"
        assert m.revision == 2
        assert str(m.path) == "prices/equity/AAPL"

    def test_date_with_query_params(self):
        m = parse_moniker("prices/equity/AAPL/date@latest?format=json")
        assert m.date_param == "latest"
        assert m.params.format == "json"

    def test_date_in_str_representation(self):
        m = parse_moniker("prices/equity/AAPL/date@20260101")
        s = str(m)
        assert "date@20260101" in s

    def test_date_case_insensitive_symbolic(self):
        m = parse_moniker("prices/AAPL/date@Latest")
        assert m.date_param == "Latest"

    def test_date_empty_value_raises(self):
        with pytest.raises(MonikerParseError, match="Empty date value"):
            parse_moniker("prices/AAPL/date@")

    def test_date_invalid_format_raises(self):
        with pytest.raises(MonikerParseError, match="Invalid date parameter"):
            parse_moniker("prices/AAPL/date@notadate")

    def test_date_invalid_relative_raises(self):
        with pytest.raises(MonikerParseError, match="Invalid date parameter"):
            parse_moniker("prices/AAPL/date@0M")  # 0 not valid (must start with 1-9)

    def test_date_with_scheme(self):
        m = parse_moniker("moniker://prices/equity/AAPL/date@20260101")
        assert m.date_param == "20260101"
        assert str(m.path) == "prices/equity/AAPL"

    def test_no_date_param_by_default(self):
        """Monikers without date@ have date_param=None."""
        m = parse_moniker("prices/equity/AAPL")
        assert m.date_param is None

    def test_date_with_namespace(self):
        """date@ works with namespace prefix."""
        m = parse_moniker("prod@prices/equity/AAPL/date@20260101")
        assert m.namespace == "prod"
        assert m.date_param == "20260101"
        assert str(m.path) == "prices/equity/AAPL"


class TestFilterShortlink:
    """Tests for filter@CODE reserved segment expansion."""

    @pytest.fixture()
    def store(self):
        from moniker_svc.shortlinks.store import ShortlinkStore
        s = ShortlinkStore()
        s.create(
            base_path="prices/equity",
            filter_segments=["US", "10Y"],
            params={"format": "json"},
            label="test",
        )
        return s

    def _link_id(self, store):
        return store.all()[0].id

    def test_filter_basic_expansion(self, store):
        """filter@CODE expands to stored filter_segments."""
        lid = self._link_id(store)
        m = parse_moniker(f"prices/equity/filter@{lid}", shortlink_store=store)
        assert str(m.path) == "prices/equity/US/10Y"
        assert m.params.format == "json"
        assert m.filter_shortlink == f"filter@{lid}"

    def test_filter_mid_path(self, store):
        """filter@CODE splices in-place, preserving segments after it."""
        lid = self._link_id(store)
        m = parse_moniker(f"prices/equity/filter@{lid}/summary", shortlink_store=store)
        assert str(m.path) == "prices/equity/US/10Y/summary"

    def test_filter_at_start(self, store):
        """filter@CODE can appear at the beginning of the path."""
        lid = self._link_id(store)
        m = parse_moniker(f"filter@{lid}/summary", shortlink_store=store)
        assert str(m.path) == "US/10Y/summary"

    def test_filter_with_segment_id(self, store):
        """filter@CODE and @id can coexist."""
        lid = self._link_id(store)
        m = parse_moniker(
            f"holdings/positions@ACC001/filter@{lid}/summary",
            shortlink_store=store,
        )
        assert m.segment_id == (1, "ACC001")
        assert m.filter_shortlink == f"filter@{lid}"
        # path has ACC001 stripped + filter expanded
        assert str(m.path) == "holdings/positions/US/10Y/summary"

    def test_filter_with_date(self, store):
        """filter@CODE and date@ can coexist."""
        lid = self._link_id(store)
        m = parse_moniker(
            f"prices/equity/filter@{lid}/date@20260101",
            shortlink_store=store,
        )
        assert m.date_param == "20260101"
        assert str(m.path) == "prices/equity/US/10Y"

    def test_filter_with_namespace(self, store):
        """filter@CODE works with namespace prefix."""
        lid = self._link_id(store)
        m = parse_moniker(f"prod@prices/equity/filter@{lid}", shortlink_store=store)
        assert m.namespace == "prod"
        assert str(m.path) == "prices/equity/US/10Y"

    def test_filter_with_revision(self, store):
        """filter@CODE works with /vN revision."""
        lid = self._link_id(store)
        m = parse_moniker(f"prices/equity/filter@{lid}/v2", shortlink_store=store)
        assert m.revision == 2
        assert str(m.path) == "prices/equity/US/10Y"

    def test_filter_params_merge_with_query(self, store):
        """Shortlink params merge with client query params; client wins on conflict."""
        lid = self._link_id(store)
        m = parse_moniker(
            f"prices/equity/filter@{lid}?format=csv&limit=100",
            shortlink_store=store,
        )
        # Client format=csv overrides shortlink format=json
        assert m.params.format == "csv"
        assert m.params.limit == "100"

    def test_filter_does_not_count_as_at_id(self, store):
        """filter@ is reserved — it does NOT trigger the @id limit."""
        lid = self._link_id(store)
        # filter@ + one @id should work fine
        m = parse_moniker(
            f"holdings/positions@ACC001/filter@{lid}",
            shortlink_store=store,
        )
        assert m.segment_id == (1, "ACC001")
        assert m.filter_shortlink is not None

    def test_filter_canonical_path_is_clean(self, store):
        """canonical_path contains expanded segments, no filter@CODE."""
        lid = self._link_id(store)
        m = parse_moniker(f"prices/equity/filter@{lid}", shortlink_store=store)
        assert "filter@" not in m.canonical_path
        assert m.canonical_path == "prices/equity/US/10Y"

    def test_filter_empty_code_raises(self):
        """filter@ with no code is a parse error."""
        with pytest.raises(MonikerParseError, match="Empty code"):
            parse_moniker("prices/equity/filter@")

    def test_filter_no_store_raises(self):
        """filter@CODE without a shortlink store raises."""
        with pytest.raises(MonikerParseError, match="no shortlink store"):
            parse_moniker("prices/equity/filter@abc1234")

    def test_filter_unknown_code_raises(self):
        """filter@CODE with unknown ID raises."""
        from moniker_svc.shortlinks.store import ShortlinkStore
        store = ShortlinkStore()
        with pytest.raises(MonikerParseError, match="Shortlink not found"):
            parse_moniker("prices/equity/filter@UNKNOWN", shortlink_store=store)
