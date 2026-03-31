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


class TestSegmentId:
    """Tests for in-path @id identity parameters."""

    def test_segment_id_basic(self):
        m = parse_moniker("holdings/positions@ACC001/summary")
        assert m.segment_id == (1, "ACC001")
        assert str(m.path) == "holdings/positions/summary"
        assert m.version is None

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
        # Catalog sees holdings/positions/summary (no @id)
        assert m.path.segments == ("holdings", "positions", "summary")

    def test_no_segment_id_for_version_at_end(self):
        """@ at end of path is a version, not segment identity."""
        m = parse_moniker("prices/AAPL@20260101")
        assert m.segment_id is None
        assert m.version == "20260101"

    def test_mid_path_at_is_segment_id_not_version(self):
        """@ in a non-final segment is always segment identity."""
        m = parse_moniker("securities/012345678@20260101/details")
        # Under new rules: @ in mid-path segment = segment identity
        assert m.segment_id == (1, "20260101")
        assert str(m.path) == "securities/012345678/details"
        assert m.version is None

    def test_segment_id_with_version(self):
        """Segment identity and version can coexist."""
        m = parse_moniker("holdings/positions@ACC001/summary@latest")
        assert m.segment_id == (1, "ACC001")
        assert m.version == "latest"
        assert str(m.path) == "holdings/positions/summary"

    def test_segment_id_with_namespace(self):
        m = parse_moniker("prod@holdings/positions@ACC001/summary")
        assert m.namespace == "prod"
        assert m.segment_id == (1, "ACC001")
        assert str(m.path) == "holdings/positions/summary"

    def test_segment_id_with_namespace_and_version(self):
        m = parse_moniker("prod@holdings/positions@ACC001/summary@latest")
        assert m.namespace == "prod"
        assert m.segment_id == (1, "ACC001")
        assert m.version == "latest"
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

    def test_segment_id_preserved_by_with_version(self):
        m = parse_moniker("holdings/positions@ACC001/summary")
        m2 = m.with_version("latest")
        assert m2.segment_id == (1, "ACC001")

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

    def test_segment_id_str_roundtrip_with_namespace_and_version(self):
        m = parse_moniker("prod@holdings/positions@ACC001/summary@latest")
        s = str(m)
        m2 = parse_moniker(s)
        assert m2.namespace == "prod"
        assert m2.segment_id == (1, "ACC001")
        assert m2.version == "latest"
        assert m2.path == m.path

    def test_segment_id_full_path(self):
        m = parse_moniker("holdings/positions@ACC001/summary@latest/v2")
        assert "positions@ACC001" in m.full_path
        assert m.full_path == "holdings/positions@ACC001/summary@latest/v2"

    def test_segment_id_canonical_path(self):
        m = parse_moniker("holdings/positions@ACC001/summary")
        assert m.canonical_path == "holdings/positions@ACC001/summary"

    def test_segment_id_catalog_path_clean(self):
        """str(moniker.path) must remain clean (no @id) for catalog lookup."""
        m = parse_moniker("holdings/positions@ACC001/summary")
        assert str(m.path) == "holdings/positions/summary"
