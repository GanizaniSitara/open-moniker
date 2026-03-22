"""MCP integration tests — run after deployment to verify /mcp/sse.

These tests connect to the monolith's embedded MCP server over SSE
and exercise every read tool, resource, and prompt.

Usage:
    # Against a local instance (auto-starts server on port 18060):
    python -m pytest tests/test_mcp.py -v

    # Against a deployed instance:
    MCP_URL=http://host:port/mcp/sse python -m pytest tests/test_mcp.py -v
"""

from __future__ import annotations

import asyncio
import json
import multiprocessing
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Path setup — ensure moniker_svc is importable
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
_EXTERNAL_DATA = _REPO_ROOT / "external" / "moniker-data" / "src"
for p in (_SRC, _EXTERNAL_DATA):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_TEST_PORT = 18060


def _run_server():
    """Start the moniker service in a subprocess."""
    import uvicorn
    from moniker_svc.main import app
    uvicorn.run(app, host="127.0.0.1", port=_TEST_PORT, log_level="warning")


@pytest.fixture(scope="session")
def mcp_url():
    """Return the SSE URL, starting a local server if needed."""
    url = os.environ.get("MCP_URL")
    if url:
        yield url
        return

    proc = multiprocessing.Process(target=_run_server, daemon=True)
    proc.start()

    base = f"http://127.0.0.1:{_TEST_PORT}/mcp/sse"

    import httpx
    for _ in range(30):
        try:
            r = httpx.get(f"http://127.0.0.1:{_TEST_PORT}/health", timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail("Server did not start in time")

    yield base

    proc.kill()
    proc.join(timeout=5)


# ---------------------------------------------------------------------------
# Helper — open a fresh MCP session for each test
# ---------------------------------------------------------------------------

@asynccontextmanager
async def mcp_session(url: str):
    """Async context manager that yields an initialised MCP ClientSession."""
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    async with sse_client(url) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            yield session


async def _call_tool(session, name: str, args: dict | None = None) -> dict:
    """Call an MCP tool and return parsed JSON."""
    result = await session.call_tool(name, arguments=args or {})
    text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
    return json.loads(text)


# ---------------------------------------------------------------------------
# Test: tool listing
# ---------------------------------------------------------------------------

EXPECTED_READ_TOOLS = {
    "resolve_moniker",
    "list_children",
    "describe_moniker",
    "search_catalog",
    "get_lineage",
    "get_catalog_tree",
    "get_catalog_stats",
    "get_domains",
    "get_models",
    "get_model_detail",
}

WRITE_TOOLS = {
    "submit_request",
    "list_requests",
    "approve_request",
    "reject_request",
    "update_node_status",
}


@pytest.mark.asyncio
async def test_has_all_read_tools(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.list_tools()
        tool_names = {t.name for t in result.tools}
        missing = EXPECTED_READ_TOOLS - tool_names
        assert not missing, f"Missing read tools: {missing}"


@pytest.mark.asyncio
async def test_no_write_tools(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.list_tools()
        tool_names = {t.name for t in result.tools}
        present = WRITE_TOOLS & tool_names
        assert not present, f"Write tools should NOT be present: {present}"


@pytest.mark.asyncio
async def test_tool_count(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.list_tools()
        assert len(result.tools) == len(EXPECTED_READ_TOOLS)


# ---------------------------------------------------------------------------
# Test: read tools
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_resolve_moniker_invalid(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await _call_tool(session, "resolve_moniker", {"moniker": "nonexistent.path.nowhere"})
        assert "error" in result


@pytest.mark.asyncio
async def test_list_children(mcp_url):
    async with mcp_session(mcp_url) as session:
        # Get a valid domain from the catalog tree first
        tree = await _call_tool(session, "get_catalog_tree")
        assert tree["count"] > 0, "Catalog should have at least one domain"
        domain = tree["tree"][0]["path"]
        result = await _call_tool(session, "list_children", {"path": domain})
        assert "children" in result


@pytest.mark.asyncio
async def test_describe_moniker(mcp_url):
    async with mcp_session(mcp_url) as session:
        tree = await _call_tool(session, "get_catalog_tree")
        assert tree["count"] > 0
        path = tree["tree"][0]["path"]
        result = await _call_tool(session, "describe_moniker", {"path": path})
        assert "path" in result
        assert "ownership" in result


@pytest.mark.asyncio
async def test_search_catalog(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await _call_tool(session, "search_catalog", {"query": "risk"})
        assert "results" in result
        assert "count" in result


@pytest.mark.asyncio
async def test_search_catalog_with_limit(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await _call_tool(session, "search_catalog", {"query": "a", "limit": 3})
        assert result["count"] <= 3


@pytest.mark.asyncio
async def test_get_lineage(mcp_url):
    async with mcp_session(mcp_url) as session:
        tree = await _call_tool(session, "get_catalog_tree")
        assert tree["count"] > 0
        path = tree["tree"][0]["path"]
        result = await _call_tool(session, "get_lineage", {"path": path})
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_catalog_tree(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await _call_tool(session, "get_catalog_tree")
        assert result["root"] == "(top)"
        assert "tree" in result
        assert result["count"] > 0


@pytest.mark.asyncio
async def test_get_catalog_tree_subtree(mcp_url):
    async with mcp_session(mcp_url) as session:
        full = await _call_tool(session, "get_catalog_tree")
        if full["count"] > 0:
            domain = full["tree"][0]["path"]
            sub = await _call_tool(session, "get_catalog_tree", {"root_path": domain})
            assert sub["root"] == domain


@pytest.mark.asyncio
async def test_get_catalog_stats(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await _call_tool(session, "get_catalog_stats")
        assert "status_counts" in result
        assert "source_type_counts" in result
        assert "domain_count" in result
        assert "model_count" in result


@pytest.mark.asyncio
async def test_get_domains(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await _call_tool(session, "get_domains")
        assert "domains" in result
        assert "count" in result
        if result["count"] > 0:
            d = result["domains"][0]
            assert "name" in d
            assert "display_name" in d


@pytest.mark.asyncio
async def test_get_models(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await _call_tool(session, "get_models")
        assert "models" in result
        assert "count" in result


@pytest.mark.asyncio
async def test_get_model_detail_not_found(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await _call_tool(session, "get_model_detail", {"model_path": "nonexistent/model"})
        assert result.get("error") == "not_found"


@pytest.mark.asyncio
async def test_get_model_detail_found(mcp_url):
    async with mcp_session(mcp_url) as session:
        models = await _call_tool(session, "get_models")
        if models["count"] > 0:
            path = models["models"][0]["path"]
            result = await _call_tool(session, "get_model_detail", {"model_path": path})
            assert "path" in result
            assert "formula" in result
            assert "appears_in" in result


# ---------------------------------------------------------------------------
# Test: resources
# ---------------------------------------------------------------------------

EXPECTED_RESOURCES = {
    "moniker://catalog",
    "moniker://domains",
    "moniker://about",
    "moniker://naming-guide",
    "moniker://models",
}


@pytest.mark.asyncio
async def test_list_resources(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.list_resources()
        uris = {str(r.uri) for r in result.resources}
        missing = EXPECTED_RESOURCES - uris
        assert not missing, f"Missing resources: {missing}"


@pytest.mark.asyncio
async def test_read_about(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.read_resource("moniker://about")
        text = result.contents[0].text if result.contents else ""
        assert "Open Moniker" in text


@pytest.mark.asyncio
async def test_read_catalog(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.read_resource("moniker://catalog")
        data = json.loads(result.contents[0].text)
        assert "paths" in data
        assert "counts" in data


@pytest.mark.asyncio
async def test_read_domains(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.read_resource("moniker://domains")
        data = json.loads(result.contents[0].text)
        assert "domains" in data


@pytest.mark.asyncio
async def test_read_naming_guide(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.read_resource("moniker://naming-guide")
        text = result.contents[0].text if result.contents else ""
        assert "Naming Guide" in text


@pytest.mark.asyncio
async def test_read_models(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.read_resource("moniker://models")
        data = json.loads(result.contents[0].text)
        assert "models" in data


# ---------------------------------------------------------------------------
# Test: prompts
# ---------------------------------------------------------------------------

EXPECTED_PROMPTS = {
    "explore_domain",
    "find_data",
    "design_moniker_hierarchy",
    "check_ownership",
}


@pytest.mark.asyncio
async def test_list_prompts(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.list_prompts()
        names = {p.name for p in result.prompts}
        missing = EXPECTED_PROMPTS - names
        assert not missing, f"Missing prompts: {missing}"


@pytest.mark.asyncio
async def test_prompt_count(mcp_url):
    async with mcp_session(mcp_url) as session:
        result = await session.list_prompts()
        assert len(result.prompts) == len(EXPECTED_PROMPTS)
