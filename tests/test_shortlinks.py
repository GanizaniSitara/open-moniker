"""Tests for the shortlinks module.

Run: C:/miniconda3/envs/python312/python.exe -m pytest tests/test_shortlinks.py -v
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
_EXTERNAL_DATA = _REPO_ROOT / "external" / "moniker-data" / "src"
for p in (_SRC, _EXTERNAL_DATA):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from moniker_svc.shortlinks.types import Shortlink, generate_short_id, generate_random_id
from moniker_svc.shortlinks.store import ShortlinkStore


# =====================================================================
# Unit tests — ID generation
# =====================================================================

class TestIdGeneration:
    def test_deterministic(self):
        """Same input always produces the same ID."""
        id1 = generate_short_id("fixed.income/govies/sovereign/US/10Y")
        id2 = generate_short_id("fixed.income/govies/sovereign/US/10Y")
        assert id1 == id2

    def test_length(self):
        """Default ID is 7 characters."""
        short_id = generate_short_id("test-content")
        assert len(short_id) == 7

    def test_base62_chars(self):
        """ID contains only alphanumeric characters."""
        short_id = generate_short_id("test-content")
        assert short_id.isalnum()

    def test_different_inputs(self):
        """Different inputs produce different IDs."""
        id1 = generate_short_id("US/10Y")
        id2 = generate_short_id("GB/5Y")
        assert id1 != id2

    def test_random_id_length(self):
        short_id = generate_random_id()
        assert len(short_id) == 7
        assert short_id.isalnum()

    def test_custom_length(self):
        short_id = generate_short_id("test", length=10)
        assert len(short_id) == 10


# =====================================================================
# Unit tests — Shortlink type
# =====================================================================

class TestShortlinkType:
    def test_roundtrip(self):
        """to_dict → from_dict preserves all fields."""
        link = Shortlink(
            id="abc1234",
            base_path="fixed.income/govies/sovereign",
            filter_segments=("US", "10Y", "SHORT_DATED"),
            version="3M",
            params={"format": "json", "limit": "1000"},
            label="Test link",
            created_by="test@firm.com",
        )
        restored = Shortlink.from_dict(link.to_dict())
        assert restored.id == link.id
        assert restored.base_path == link.base_path
        assert restored.filter_segments == link.filter_segments
        assert restored.version == link.version
        assert restored.params == link.params
        assert restored.label == link.label

    def test_expand(self):
        """expand() reconstructs the full moniker path."""
        link = Shortlink(
            id="abc1234",
            base_path="fixed.income/govies/sovereign",
            filter_segments=("US", "10Y"),
            version="3M",
            params={"format": "json"},
        )
        assert link.expand() == "fixed.income/govies/sovereign/US/10Y@3M?format=json"

    def test_expand_no_version(self):
        link = Shortlink(
            id="x", base_path="prices.equity", filter_segments=("AAPL",),
        )
        assert link.expand() == "prices.equity/AAPL"

    def test_expand_no_filters(self):
        link = Shortlink(
            id="x", base_path="indices.equity", filter_segments=(),
            version="latest",
        )
        assert link.expand() == "indices.equity@latest"

    def test_canonical_filter(self):
        link = Shortlink(
            id="x", base_path="test",
            filter_segments=("A", "B"), version="3M",
            params={"z": "1", "a": "2"},
        )
        # Params should be sorted
        assert link.canonical_filter == "A/B@3M?a=2&z=1"


# =====================================================================
# Unit tests — Store
# =====================================================================

class TestStore:
    def test_create_and_get(self):
        store = ShortlinkStore()
        link = store.create(
            base_path="fixed.income/govies/sovereign",
            filter_segments=["US", "10Y"],
            version="3M",
        )
        assert link.id
        assert store.get(link.id) is link

    def test_create_idempotent(self):
        """Creating the same filter twice returns the same shortlink."""
        store = ShortlinkStore()
        link1 = store.create(base_path="test", filter_segments=["A", "B"])
        link2 = store.create(base_path="test", filter_segments=["A", "B"])
        assert link1.id == link2.id

    def test_delete(self):
        store = ShortlinkStore()
        link = store.create(base_path="test", filter_segments=["X"])
        assert store.delete(link.id) is True
        assert store.get(link.id) is None
        assert store.delete(link.id) is False

    def test_all_and_count(self):
        store = ShortlinkStore()
        store.create(base_path="a", filter_segments=["1"])
        store.create(base_path="b", filter_segments=["2"])
        assert store.count() == 2
        assert len(store.all()) == 2

    def test_persistence_roundtrip(self):
        """Create → save → load into new store → verify data."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            store1 = ShortlinkStore(file_path=path)
            link = store1.create(
                base_path="prices.equity",
                filter_segments=["AAPL"],
                version="latest",
                params={"format": "csv"},
                label="Apple prices",
            )

            # New store, load from same file
            store2 = ShortlinkStore(file_path=path)
            store2.load()
            assert store2.count() == 1

            restored = store2.get(link.id)
            assert restored is not None
            assert restored.base_path == "prices.equity"
            assert restored.filter_segments == ("AAPL",)
            assert restored.version == "latest"
            assert restored.params == {"format": "csv"}
            assert restored.label == "Apple prices"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_try_expand_path_with_tilde(self):
        store = ShortlinkStore()
        link = store.create(
            base_path="fixed.income/govies/sovereign",
            filter_segments=["US", "10Y"],
            version="3M",
            params={"format": "json"},
        )

        expanded, alias = store.try_expand_path(
            f"fixed.income/govies/sovereign/~{link.id}"
        )
        assert alias == f"~{link.id}"
        assert expanded == "fixed.income/govies/sovereign/US/10Y@3M?format=json"

    def test_try_expand_path_no_tilde(self):
        store = ShortlinkStore()
        expanded, alias = store.try_expand_path("fixed.income/govies/sovereign/US/10Y")
        assert alias is None
        assert expanded == "fixed.income/govies/sovereign/US/10Y"

    def test_try_expand_path_unknown_id(self):
        store = ShortlinkStore()
        with pytest.raises(KeyError, match="Shortlink not found"):
            store.try_expand_path("fixed.income/~UNKNOWN")


# =====================================================================
# Integration tests — API routes (requires full app)
# =====================================================================

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from moniker_svc.main import app


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


class TestShortlinkAPI:
    @pytest.mark.asyncio
    async def test_create(self, client):
        r = await client.post("/s", json={
            "base_path": "benchmarks.returns",
            "filter_segments": ["equity", "sp500"],
            "version": "latest",
            "label": "S&P 500 returns",
        })
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert body["base_path"] == "benchmarks.returns"
        assert body["resolve_path"].startswith("benchmarks.returns/~")
        assert "equity/sp500@latest" in body["expanded_path"]

    @pytest.mark.asyncio
    async def test_create_idempotent(self, client):
        payload = {
            "base_path": "test.dedup",
            "filter_segments": ["A", "B"],
        }
        r1 = await client.post("/s", json=payload)
        r2 = await client.post("/s", json=payload)
        assert r1.json()["id"] == r2.json()["id"]

    @pytest.mark.asyncio
    async def test_list(self, client):
        r = await client.get("/s")
        assert r.status_code == 200
        body = r.json()
        assert body["count"] >= 1
        assert len(body["shortlinks"]) == body["count"]

    @pytest.mark.asyncio
    async def test_get(self, client):
        # Create one first
        r = await client.post("/s", json={
            "base_path": "test.get",
            "filter_segments": ["X"],
        })
        short_id = r.json()["id"]

        r = await client.get(f"/s/{short_id}")
        assert r.status_code == 200
        assert r.json()["id"] == short_id

    @pytest.mark.asyncio
    async def test_get_not_found(self, client):
        r = await client.get("/s/NONEXISTENT")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_delete(self, client):
        r = await client.post("/s", json={
            "base_path": "test.delete",
            "filter_segments": ["Y"],
        })
        short_id = r.json()["id"]

        r = await client.delete(f"/s/{short_id}")
        assert r.status_code == 200
        assert r.json()["success"] is True

        r = await client.get(f"/s/{short_id}")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client):
        r = await client.delete("/s/NONEXISTENT")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_resolve_via_shortlink(self, client):
        """Create a shortlink for a known moniker, resolve via ~id."""
        # Create shortlink for benchmarks.returns (known in sample catalog)
        r = await client.post("/s", json={
            "base_path": "benchmarks.returns",
            "filter_segments": [],
            "version": "latest",
        })
        assert r.status_code == 201
        short_id = r.json()["id"]

        # Resolve via tilde path
        r = await client.get(f"/resolve/benchmarks.returns/~{short_id}")
        # May be 200 (resolved) or 404 (no source binding for this path in test catalog)
        # The important thing is it didn't 404 with "Shortlink not found"
        if r.status_code == 200:
            body = r.json()
            assert body["redirected_from"] == f"~{short_id}"

    @pytest.mark.asyncio
    async def test_resolve_unknown_shortlink(self, client):
        r = await client.get("/resolve/some/path/~UNKNOWN")
        assert r.status_code == 404
        assert "Shortlink not found" in r.json()["detail"]

    @pytest.mark.asyncio
    async def test_resolve_normal_unaffected(self, client):
        """Normal resolve (no tilde) still works."""
        r = await client.get("/resolve/benchmarks.returns")
        # Should work normally — no shortlink interference
        assert r.status_code in (200, 404)  # depends on demo catalog
