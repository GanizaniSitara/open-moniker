"""REST API route tests using FastAPI TestClient (in-process, no server).

Run: C:/Anaconda3/envs/python312/python.exe -m pytest tests/test_api.py -v
"""

from __future__ import annotations

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


# ===================================================================
# Fixture — shared async client with lifespan
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
# Health & metadata
# ===================================================================

class TestHealth:
    @pytest.mark.asyncio
    async def test_health(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert "telemetry" in body
        assert "cache" in body
        assert "catalog_counts" in body

    @pytest.mark.asyncio
    async def test_openapi_spec(self, client):
        r = await client.get("/openapi.json")
        assert r.status_code == 200
        spec = r.json()
        assert "openapi" in spec
        assert "paths" in spec

    @pytest.mark.asyncio
    async def test_docs_page(self, client):
        r = await client.get("/docs")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    @pytest.mark.asyncio
    async def test_root_page(self, client):
        r = await client.get("/")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_favicon(self, client):
        r = await client.get("/favicon.ico")
        assert r.status_code == 204


# ===================================================================
# Resolution
# ===================================================================

class TestResolve:
    @pytest.mark.asyncio
    async def test_resolve_invalid_moniker(self, client):
        r = await client.get("/resolve/")
        # Empty path or invalid should return 4xx
        assert r.status_code in (400, 404, 422)

    @pytest.mark.asyncio
    async def test_resolve_nonexistent(self, client):
        r = await client.get("/resolve/nonexistent.path.nowhere")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_resolve_known_path(self, client):
        # First get a valid path from the catalog
        r = await client.get("/catalog")
        if r.status_code == 200:
            body = r.json()
            paths = body.get("paths", [])
            # Find a leaf with source binding
            for path in paths:
                rr = await client.get(f"/resolve/{path}")
                if rr.status_code == 200:
                    result = rr.json()
                    assert "source_type" in result
                    assert "connection" in result
                    assert "ownership" in result
                    break


# ===================================================================
# Catalog browsing
# ===================================================================

class TestCatalog:
    @pytest.mark.asyncio
    async def test_catalog_list(self, client):
        r = await client.get("/catalog")
        assert r.status_code == 200
        body = r.json()
        assert "paths" in body

    @pytest.mark.asyncio
    async def test_catalog_search(self, client):
        r = await client.get("/catalog/search", params={"q": "risk"})
        assert r.status_code == 200
        body = r.json()
        assert "results" in body
        assert "query" in body

    @pytest.mark.asyncio
    async def test_catalog_search_empty_query(self, client):
        r = await client.get("/catalog/search", params={"q": ""})
        assert r.status_code in (200, 400, 422)

    @pytest.mark.asyncio
    async def test_catalog_stats(self, client):
        r = await client.get("/catalog/stats")
        assert r.status_code == 200
        body = r.json()
        assert "total_monikers" in body
        assert "by_status" in body
        assert "by_source_type" in body

    @pytest.mark.asyncio
    async def test_tree_root(self, client):
        r = await client.get("/tree")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)


class TestDescribe:
    @pytest.mark.asyncio
    async def test_describe_known_path(self, client):
        # Get a valid path first
        r = await client.get("/catalog")
        if r.status_code == 200:
            paths = r.json().get("paths", [])
            if paths:
                rr = await client.get(f"/describe/{paths[0]}")
                assert rr.status_code == 200
                body = rr.json()
                assert "path" in body
                assert "ownership" in body

    @pytest.mark.asyncio
    async def test_describe_nonexistent(self, client):
        r = await client.get("/describe/nonexistent.path")
        # Service returns 200 with partial data even for unknown paths
        assert r.status_code in (200, 404)


class TestList:
    @pytest.mark.asyncio
    async def test_list_children(self, client):
        # Get a domain with children
        r = await client.get("/catalog")
        if r.status_code == 200:
            paths = r.json().get("paths", [])
            if paths:
                rr = await client.get(f"/list/{paths[0]}")
                assert rr.status_code == 200
                body = rr.json()
                assert "children" in body


class TestLineage:
    @pytest.mark.asyncio
    async def test_lineage_known_path(self, client):
        r = await client.get("/catalog")
        if r.status_code == 200:
            paths = r.json().get("paths", [])
            if paths:
                rr = await client.get(f"/lineage/{paths[0]}")
                assert rr.status_code == 200
                body = rr.json()
                assert "ownership" in body


# ===================================================================
# Domain routes
# ===================================================================

class TestDomains:
    @pytest.mark.asyncio
    async def test_list_domains(self, client):
        r = await client.get("/domains")
        assert r.status_code == 200
        body = r.json()
        assert "domains" in body

    @pytest.mark.asyncio
    async def test_get_domain(self, client):
        r = await client.get("/domains")
        if r.status_code == 200:
            domains = r.json().get("domains", [])
            if domains:
                # Domain list items may use "name" or another key
                first = domains[0]
                name = first.get("name") or first.get("key") or list(first.values())[0]
                rr = await client.get(f"/domains/{name}")
                assert rr.status_code == 200

    @pytest.mark.asyncio
    async def test_get_domain_nonexistent(self, client):
        r = await client.get("/domains/nonexistent_domain_xyz")
        assert r.status_code == 404


# ===================================================================
# Model routes
# ===================================================================

class TestModels:
    @pytest.mark.asyncio
    async def test_list_models(self, client):
        r = await client.get("/models")
        assert r.status_code == 200
        body = r.json()
        assert "models" in body

    @pytest.mark.asyncio
    async def test_model_tree(self, client):
        r = await client.get("/models/tree")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_get_model(self, client):
        r = await client.get("/models")
        if r.status_code == 200:
            models = r.json().get("models", [])
            if models:
                path = models[0]["path"]
                rr = await client.get(f"/models/{path}")
                assert rr.status_code == 200

    @pytest.mark.asyncio
    async def test_get_model_nonexistent(self, client):
        r = await client.get("/models/nonexistent/model/path")
        assert r.status_code == 404


# ===================================================================
# Application routes
# ===================================================================

class TestApplications:
    @pytest.mark.asyncio
    async def test_list_applications(self, client):
        r = await client.get("/applications")
        assert r.status_code == 200
        body = r.json()
        assert "applications" in body

    @pytest.mark.asyncio
    async def test_get_application(self, client):
        r = await client.get("/applications")
        if r.status_code == 200:
            apps = r.json().get("applications", [])
            if apps:
                key = apps[0]["key"]
                rr = await client.get(f"/applications/{key}")
                assert rr.status_code == 200

    @pytest.mark.asyncio
    async def test_get_application_nonexistent(self, client):
        r = await client.get("/applications/nonexistent_app_xyz")
        assert r.status_code == 404


# ===================================================================
# Request workflow routes
# ===================================================================

class TestRequests:
    @pytest.mark.asyncio
    async def test_list_requests(self, client):
        r = await client.get("/requests")
        assert r.status_code == 200
        body = r.json()
        assert "requests" in body

    @pytest.mark.asyncio
    async def test_submit_request(self, client):
        r = await client.post("/requests", json={
            "path": "test.submit/api_test_node",
            "display_name": "API Test Node",
            "description": "Created by test_api.py",
            "justification": "Integration testing",
            "requester": {
                "name": "test-runner",
                "email": "test@test.com",
            },
        })
        # 201 on success, 400 if parent domain doesn't exist
        assert r.status_code in (200, 201, 400)
        if r.status_code in (200, 201):
            body = r.json()
            assert "request_id" in body

    @pytest.mark.asyncio
    async def test_get_request_nonexistent(self, client):
        r = await client.get("/requests/nonexistent-id-12345")
        assert r.status_code == 404


# ===================================================================
# Batch resolution
# ===================================================================

class TestBatch:
    @pytest.mark.asyncio
    async def test_batch_resolve(self, client):
        # Get valid paths
        r = await client.get("/catalog")
        if r.status_code == 200:
            paths = r.json().get("paths", [])[:3]
            if paths:
                rr = await client.post("/resolve/batch", json={"monikers": paths})
                assert rr.status_code == 200
                body = rr.json()
                assert "results" in body

    @pytest.mark.asyncio
    async def test_batch_resolve_empty(self, client):
        r = await client.post("/resolve/batch", json={"monikers": []})
        assert r.status_code == 200


# ===================================================================
# Response format checks
# ===================================================================

class TestResponseFormat:
    @pytest.mark.asyncio
    async def test_json_content_type(self, client):
        r = await client.get("/health")
        assert "application/json" in r.headers["content-type"]

    @pytest.mark.asyncio
    async def test_404_is_json(self, client):
        r = await client.get("/resolve/nonexistent.path.nowhere")
        assert r.status_code == 404
        body = r.json()
        assert "error" in body or "detail" in body
