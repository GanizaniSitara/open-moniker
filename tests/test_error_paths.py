"""Negative and error-path tests for the moniker service.

Covers moniker parsing errors, registry edge cases, cache semantics,
and HTTP error codes with response-format consistency.

Run: C:/Anaconda3/envs/python312/python.exe -m pytest tests/test_error_paths.py -v
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
_EXTERNAL_DATA = _REPO_ROOT / "external" / "moniker-data" / "src"
for p in (_SRC, _EXTERNAL_DATA):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from moniker_svc.main import app
from moniker_svc.moniker.parser import parse_moniker, MonikerParseError
from moniker_svc.catalog.registry import CatalogRegistry
from moniker_svc.catalog.types import CatalogNode, NodeStatus
from moniker_svc.cache.memory import InMemoryCache
from moniker_svc.models.registry import ModelRegistry
from moniker_svc.models.types import Model
from moniker_svc.applications.registry import ApplicationRegistry
from moniker_svc.applications.types import Application
from moniker_svc.requests import RequestRegistry


# ===================================================================
# Fixture -- shared async client with lifespan
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


# ===================================================================
# Moniker parsing errors
# ===================================================================

class TestMonikerParsing:
    def test_empty_string_raises(self):
        with pytest.raises(MonikerParseError):
            parse_moniker("")

    def test_special_chars_only_raises(self):
        with pytest.raises(MonikerParseError):
            parse_moniker("!!!@@@###")

    def test_extremely_long_path_does_not_crash(self):
        long_path = "a" * 10000
        # Should either parse or raise MonikerParseError -- must not crash
        try:
            result = parse_moniker(long_path)
            # If it parses, it should have a path
            assert result.path is not None
        except MonikerParseError:
            pass  # Acceptable


# ===================================================================
# Catalog registry errors
# ===================================================================

class TestCatalogErrors:
    def test_get_nonexistent_returns_none(self):
        reg = CatalogRegistry()
        assert reg.get("nonexistent/path/xyz") is None

    def test_children_of_nonexistent_returns_empty(self):
        reg = CatalogRegistry()
        children = reg.children("nonexistent/path/xyz")
        assert children == []

    def test_register_duplicate_path_overwrites(self):
        reg = CatalogRegistry()
        node1 = CatalogNode(path="test/dup", display_name="First")
        node2 = CatalogNode(path="test/dup", display_name="Second")
        reg.register(node1)
        reg.register(node2)
        result = reg.get("test/dup")
        assert result is not None
        assert result.display_name == "Second"


# ===================================================================
# Cache errors
# ===================================================================

class TestCacheErrors:
    def test_get_from_empty_cache_returns_none(self):
        cache = InMemoryCache()
        assert cache.get("nonexistent_key") is None

    @pytest.mark.asyncio
    async def test_set_with_zero_ttl_behaviour(self):
        cache = InMemoryCache()
        await cache.set("key", "value", ttl_seconds=0)
        # With ttl=0, is_expired uses strict > comparison:
        #   time.time() > created_at + 0
        # On fast machines time advances between set() and get(),
        # so the entry may or may not be expired. Just verify
        # that after a tiny sleep it is definitely gone.
        import time
        time.sleep(0.01)
        result_after = cache.get("key")
        assert result_after is None


# ===================================================================
# Registry errors (models, applications)
# ===================================================================

class TestModelRegistryErrors:
    def test_duplicate_register_raises_value_error(self):
        reg = ModelRegistry()
        model = Model(path="risk/dv01", display_name="DV01")
        reg.register(model)
        with pytest.raises(ValueError, match="already registered"):
            reg.register(model)

    def test_get_or_raise_missing_raises_key_error(self):
        reg = ModelRegistry()
        with pytest.raises(KeyError, match="not found"):
            reg.get_or_raise("nonexistent/path")


class TestApplicationRegistryErrors:
    def test_duplicate_register_raises_value_error(self):
        reg = ApplicationRegistry()
        app_obj = Application(key="test-app", display_name="Test App")
        reg.register(app_obj)
        with pytest.raises(ValueError, match="already registered"):
            reg.register(app_obj)

    def test_get_or_raise_missing_raises_key_error(self):
        reg = ApplicationRegistry()
        with pytest.raises(KeyError, match="not found"):
            reg.get_or_raise("nonexistent-app")


# ===================================================================
# HTTP error codes
# ===================================================================

class TestHTTPErrors:
    @pytest.mark.asyncio
    async def test_resolve_empty_path_returns_4xx(self, client):
        r = await client.get("/resolve/")
        assert 400 <= r.status_code < 500

    @pytest.mark.asyncio
    async def test_resolve_nonexistent_deep_path_returns_404(self, client):
        r = await client.get("/resolve/nonexistent.deep.path.nowhere")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_batch_empty_monikers_returns_200(self, client):
        r = await client.post("/resolve/batch", json={"monikers": []})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_batch_invalid_json_returns_422(self, client):
        r = await client.post(
            "/resolve/batch",
            content=b"not json at all",
            headers={"content-type": "application/json"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_domains_nonexistent_returns_404(self, client):
        r = await client.get("/domains/nonexistent_domain_xyz_123")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_models_nonexistent_returns_404(self, client):
        r = await client.get("/models/nonexistent/path/xyz")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_applications_nonexistent_returns_404(self, client):
        r = await client.get("/applications/nonexistent_app_xyz_999")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_requests_nonexistent_returns_404(self, client):
        r = await client.get("/requests/nonexistent-id-9999")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_requests_post_missing_fields_returns_422(self, client):
        # Missing required "requester" and "path" fields
        r = await client.post("/requests", json={})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_catalog_status_invalid_status_returns_error(self, client):
        r = await client.put(
            "/catalog/nonexistent/path/status",
            json={"status": "totally_invalid_status", "actor": "test"},
        )
        # Should return 4xx (either 404 for missing path or 422 for bad status)
        assert 400 <= r.status_code < 500


# ===================================================================
# Response consistency
# ===================================================================

class TestResponseConsistency:
    """Error responses must be JSON (not HTML 500 pages) with standard fields."""

    @pytest.mark.asyncio
    async def test_404_resolve_is_json(self, client):
        r = await client.get("/resolve/nonexistent.path.nowhere")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")
        body = r.json()
        assert "error" in body or "detail" in body

    @pytest.mark.asyncio
    async def test_404_domain_is_json(self, client):
        r = await client.get("/domains/nonexistent_domain_xyz_123")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")
        body = r.json()
        assert "error" in body or "detail" in body

    @pytest.mark.asyncio
    async def test_404_model_is_json(self, client):
        r = await client.get("/models/nonexistent/model/path/xyz")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")
        body = r.json()
        assert "error" in body or "detail" in body

    @pytest.mark.asyncio
    async def test_404_application_is_json(self, client):
        r = await client.get("/applications/nonexistent_app_999")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")
        body = r.json()
        assert "error" in body or "detail" in body

    @pytest.mark.asyncio
    async def test_404_request_is_json(self, client):
        r = await client.get("/requests/nonexistent-id-0000")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")
        body = r.json()
        assert "error" in body or "detail" in body

    @pytest.mark.asyncio
    async def test_422_invalid_post_is_json(self, client):
        r = await client.post("/requests", json={})
        assert r.status_code == 422
        assert "application/json" in r.headers.get("content-type", "")
        body = r.json()
        assert "detail" in body
