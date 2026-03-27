"""Dashboard and UI layout tests using BeautifulSoup.

Validates that each HTML UI endpoint returns well-formed pages with the
expected corporate structure, consistent styling, and no broken templates.

Run: C:/Anaconda3/envs/python312/python.exe -m pytest tests/test_ui.py -v
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from bs4 import BeautifulSoup
from httpx import ASGITransport, AsyncClient

_REPO_ROOT = Path(__file__).resolve().parent.parent
_EXTERNAL_DATA = _REPO_ROOT / "external" / "moniker-data" / "src"
for p in (_REPO_ROOT, _EXTERNAL_DATA):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from moniker_svc.main import app


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
# Helper to fetch and parse a UI page
# ===================================================================

UI_ENDPOINTS = [
    "/config/ui",
    "/domains/ui",
    "/models/ui",
    "/requests/ui",
    "/ui",
]


async def _get_soup(client: AsyncClient, path: str) -> tuple:
    """Return (response, BeautifulSoup) for a UI endpoint."""
    r = await client.get(path)
    soup = BeautifulSoup(r.text, "html.parser") if r.status_code == 200 else None
    return r, soup


# ===================================================================
# HTML structure checks (for each UI endpoint)
# ===================================================================

class TestHTMLStructure:
    """Every UI page must return valid HTML with core structural tags."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_returns_200_html(self, client, endpoint):
        r = await client.get(endpoint)
        assert r.status_code == 200, f"{endpoint} returned {r.status_code}"
        assert "text/html" in r.headers.get("content-type", "")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_has_html_head_body(self, client, endpoint):
        r, soup = await _get_soup(client, endpoint)
        assert r.status_code == 200
        assert soup.find("html") is not None, f"{endpoint} missing <html>"
        assert soup.find("head") is not None, f"{endpoint} missing <head>"
        assert soup.find("body") is not None, f"{endpoint} missing <body>"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_has_title_or_header(self, client, endpoint):
        r, soup = await _get_soup(client, endpoint)
        assert r.status_code == 200
        has_title = soup.find("title") is not None
        has_header = soup.find(re.compile(r"^h[1-6]$")) is not None
        assert has_title or has_header, f"{endpoint} missing <title> or header element"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_no_broken_template_vars(self, client, endpoint):
        r = await client.get(endpoint)
        assert r.status_code == 200
        text = r.text
        # Jinja/template artefacts should never appear in served HTML
        assert "{{ " not in text, f"{endpoint} contains broken template {{ variable"
        assert "{%" not in text, f"{endpoint} contains broken template {{% tag"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_has_css(self, client, endpoint):
        r, soup = await _get_soup(client, endpoint)
        assert r.status_code == 200
        has_style_tag = soup.find("style") is not None
        has_link_css = soup.find("link", rel="stylesheet") is not None
        has_inline_style = any(tag.get("style") for tag in soup.find_all(True))
        assert has_style_tag or has_link_css or has_inline_style, (
            f"{endpoint} has no CSS (no <style>, no stylesheet <link>, no inline styles)"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_has_script_tags(self, client, endpoint):
        r, soup = await _get_soup(client, endpoint)
        assert r.status_code == 200
        assert soup.find("script") is not None, f"{endpoint} missing <script> tags"


# ===================================================================
# Specific page checks
# ===================================================================

class TestPageContent:

    @pytest.mark.asyncio
    async def test_config_ui_contains_catalog_config(self, client):
        r, soup = await _get_soup(client, "/config/ui")
        assert r.status_code == 200
        text = soup.get_text()
        assert "Catalog Config" in text or "Moniker Catalog Config" in text

    @pytest.mark.asyncio
    async def test_domains_ui_contains_domain_text(self, client):
        r, soup = await _get_soup(client, "/domains/ui")
        assert r.status_code == 200
        text = soup.get_text()
        assert "Domain" in text

    @pytest.mark.asyncio
    async def test_domains_ui_has_table(self, client):
        r, soup = await _get_soup(client, "/domains/ui")
        assert r.status_code == 200
        assert soup.find("table") is not None, "/domains/ui should contain a table element"

    @pytest.mark.asyncio
    async def test_models_ui_contains_models_text(self, client):
        r, soup = await _get_soup(client, "/models/ui")
        assert r.status_code == 200
        text = soup.get_text()
        assert "Models" in text or "Model" in text

    @pytest.mark.asyncio
    async def test_requests_ui_contains_review_queue(self, client):
        r, soup = await _get_soup(client, "/requests/ui")
        assert r.status_code == 200
        text = soup.get_text()
        assert "Review Queue" in text

    @pytest.mark.asyncio
    async def test_main_ui_returns_200(self, client):
        r = await client.get("/ui")
        assert r.status_code == 200


# ===================================================================
# Cross-cutting checks
# ===================================================================

class TestCrossCutting:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_consistent_navy_color(self, client, endpoint):
        """All UI pages should reference the corporate navy hex #022D5E."""
        r = await client.get(endpoint)
        assert r.status_code == 200
        assert "#022D5E" in r.text or "#022d5e" in r.text.lower(), (
            f"{endpoint} does not reference navy color #022D5E"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_viewport_meta_tag(self, client, endpoint):
        r, soup = await _get_soup(client, endpoint)
        assert r.status_code == 200
        meta_viewport = soup.find("meta", attrs={"name": "viewport"})
        assert meta_viewport is not None, f"{endpoint} missing viewport meta tag"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_no_img_without_alt(self, client, endpoint):
        """All <img> tags must have an alt attribute (accessibility)."""
        r, soup = await _get_soup(client, endpoint)
        assert r.status_code == 200
        imgs = soup.find_all("img")
        for img in imgs:
            assert img.get("alt") is not None, (
                f"{endpoint} has <img> without alt attribute: {str(img)[:80]}"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("endpoint", UI_ENDPOINTS)
    async def test_internal_links_not_broken(self, client, endpoint):
        """href attributes pointing to internal routes should not 404."""
        r, soup = await _get_soup(client, endpoint)
        assert r.status_code == 200

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Only check internal paths (not external URLs, anchors, or JS)
            if href.startswith("/") and not href.startswith("//"):
                # Skip dynamic/parameterized paths and fragment-only links
                if "{" in href or "#" in href.split("/")[-1]:
                    continue
                # Skip known parameterised API endpoints used with JS
                if "/catalog/" in href and "/audit" in href:
                    continue
                link_r = await client.get(href)
                assert link_r.status_code != 404, (
                    f"{endpoint} has internal link to {href} that returns 404"
                )
