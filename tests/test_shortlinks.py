"""Shortlink registry and API tests.

Run: C:/miniconda3/envs/python312/python.exe -m pytest tests/test_shortlinks.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

_REPO_ROOT = Path(__file__).resolve().parent.parent
_EXTERNAL_DATA = _REPO_ROOT / "external" / "moniker-data" / "src"
for p in (_REPO_ROOT, _EXTERNAL_DATA):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from moniker_svc.config_ui.shortlinks import ShortlinkRegistry
from moniker_svc.main import app


# ===================================================================
# Unit tests — ShortlinkRegistry
# ===================================================================

class TestShortlinkRegistry:
    """In-memory registry (no persistence file)."""

    def test_create_and_get(self):
        reg = ShortlinkRegistry()
        link = reg.create(filters={"domain": "finance", "category": "bonds"})
        assert len(link.short_id) == 8
        assert link.filters == {"domain": "finance", "category": "bonds"}

        fetched = reg.get(link.short_id)
        assert fetched is not None
        assert fetched.short_id == link.short_id

    def test_get_missing_returns_none(self):
        reg = ShortlinkRegistry()
        assert reg.get("nonexistent") is None

    def test_delete(self):
        reg = ShortlinkRegistry()
        link = reg.create(filters={"x": 1})
        assert reg.delete(link.short_id) is True
        assert reg.get(link.short_id) is None
        assert reg.delete(link.short_id) is False

    def test_list_returns_all(self):
        reg = ShortlinkRegistry()
        a = reg.create(filters={"a": 1})
        b = reg.create(filters={"b": 2})
        all_links = reg.all()
        ids = {link.short_id for link in all_links}
        assert ids == {a.short_id, b.short_id}

    def test_count(self):
        reg = ShortlinkRegistry()
        assert reg.count() == 0
        reg.create(filters={"x": 1})
        reg.create(filters={"y": 2})
        assert reg.count() == 2

    def test_label_and_path_prefix(self):
        reg = ShortlinkRegistry()
        link = reg.create(
            filters={"maturity": "short"},
            path_prefix="prices.bonds/sovereign",
            label="Short gilts",
        )
        assert link.path_prefix == "prices.bonds/sovereign"
        assert link.label == "Short gilts"

    def test_persistence_roundtrip(self, tmp_path):
        path = tmp_path / "links.json"
        reg1 = ShortlinkRegistry(path)
        link = reg1.create(filters={"a": 1}, label="test")

        # New registry reads from same file
        reg2 = ShortlinkRegistry(path)
        fetched = reg2.get(link.short_id)
        assert fetched is not None
        assert fetched.filters == {"a": 1}
        assert fetched.label == "test"

    def test_persistence_delete(self, tmp_path):
        path = tmp_path / "links.json"
        reg = ShortlinkRegistry(path)
        link = reg.create(filters={"a": 1})
        reg.delete(link.short_id)

        reg2 = ShortlinkRegistry(path)
        assert reg2.count() == 0


# ===================================================================
# API tests — /config/shortlinks and /config/m/{id}
# ===================================================================

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
    async def test_create_shortlink(self, client):
        r = await client.post("/config/shortlinks", json={
            "filters": {"domain": "finance", "category": "bonds"},
            "path_prefix": "prices",
            "label": "Finance bonds",
        })
        assert r.status_code == 201
        body = r.json()
        assert "short_id" in body
        assert body["filters"] == {"domain": "finance", "category": "bonds"}
        assert body["path_prefix"] == "prices"
        assert body["short_url"].endswith(f"/config/m/{body['short_id']}")

    @pytest.mark.asyncio
    async def test_get_shortlink(self, client):
        # Create first
        r = await client.post("/config/shortlinks", json={"filters": {"x": 1}})
        short_id = r.json()["short_id"]

        # Fetch
        r = await client.get(f"/config/shortlinks/{short_id}")
        assert r.status_code == 200
        assert r.json()["short_id"] == short_id

    @pytest.mark.asyncio
    async def test_get_shortlink_404(self, client):
        r = await client.get("/config/shortlinks/doesnotexist")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_list_shortlinks(self, client):
        r = await client.get("/config/shortlinks")
        assert r.status_code == 200
        body = r.json()
        assert "shortlinks" in body
        assert body["total"] >= 0

    @pytest.mark.asyncio
    async def test_resolve_short_url(self, client):
        # Create
        r = await client.post("/config/shortlinks", json={
            "filters": {"rating": "AA+"},
            "path_prefix": "bonds/sovereign",
        })
        short_id = r.json()["short_id"]

        # Resolve via /config/m/{id}
        r = await client.get(f"/config/m/{short_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["filters"] == {"rating": "AA+"}
        assert body["path_prefix"] == "bonds/sovereign"

    @pytest.mark.asyncio
    async def test_resolve_short_url_404(self, client):
        r = await client.get("/config/m/doesnotexist")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_shortlink(self, client):
        # Create
        r = await client.post("/config/shortlinks", json={"filters": {"del": True}})
        short_id = r.json()["short_id"]

        # Delete
        r = await client.delete(f"/config/shortlinks/{short_id}")
        assert r.status_code == 200

        # Verify gone
        r = await client.get(f"/config/shortlinks/{short_id}")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_shortlink_404(self, client):
        r = await client.delete("/config/shortlinks/doesnotexist")
        assert r.status_code == 404
