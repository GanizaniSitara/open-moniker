"""Management-only FastAPI entry point (control plane).

Start with:
    PYTHONPATH=src uvicorn moniker_svc.management_app:app --host 0.0.0.0 --port 8052

This process serves only the management/control-plane endpoints:
- /config/*    — catalog CRUD + save/reload
- /domains/*   — domain CRUD
- /models/*    — business model CRUD
- /requests/*  — request/approval workflow
- /dashboard/* — observability dashboard
- GET /        — landing page

It does NOT initialise AdapterRegistry, InMemoryCache, RateLimiter,
TelemetryEmitter, or the cached-query refresh loop.  Resolver endpoints
(/resolve/*, /fetch/*, /catalog, /tree, /health, etc.) are absent — requests
to those paths return 404.
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add external packages path if running from repo
_REPO_ROOT = Path(__file__).parent.parent.parent
_EXTERNAL_DATA = _REPO_ROOT / "external" / "moniker-data" / "src"
if _EXTERNAL_DATA.exists() and str(_EXTERNAL_DATA) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_DATA))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import _bootstrap as bs
from .config_ui import routes as config_ui_routes
from .domains import routes as domain_routes
from .models import routes as model_routes
from .requests import routes as request_routes
from .dashboard import routes as dashboard_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Management-only startup (no adapters, no telemetry, no cache)."""
    logger.info("Starting management service...")

    config, config_path = bs.load_config()

    catalog, _catalog_dir, catalog_definition_path = bs.build_catalog_registry(config, config_path)
    domain_registry, domains_yaml_path = bs.build_domain_registry()
    model_registry, models_yaml_path = bs.build_model_registry(config)
    request_registry, requests_yaml_path = bs.build_request_registry(config)

    # Wire each management sub-router with its runtime dependencies.
    domain_routes.configure(
        domain_registry=domain_registry,
        catalog_registry=catalog,
        domains_yaml_path=domains_yaml_path,
    )
    logger.info("Domain configuration enabled")

    if config.config_ui.enabled:
        config_ui_routes.configure(
            catalog=catalog,
            yaml_output_path=config.config_ui.yaml_output_path,
            catalog_definition_file=str(catalog_definition_path) if catalog_definition_path else None,
            service_cache=None,          # no in-memory cache on management process
            show_file_paths=config.config_ui.show_file_paths,
            domain_registry=domain_registry,
        )
        logger.info("Config UI enabled (catalog_file=%s)", catalog_definition_path)

    if config.models.enabled:
        model_routes.configure(
            model_registry=model_registry,
            catalog_registry=catalog,
            models_yaml_path=models_yaml_path,
        )
        logger.info("Business models configuration enabled")

    if config.requests.enabled:
        request_routes.configure(
            request_registry=request_registry,
            catalog_registry=catalog,
            domain_registry=domain_registry,
            yaml_path=requests_yaml_path,
        )
        logger.info("Request & approval workflow enabled")

    dashboard_routes.configure(
        catalog_registry=catalog,
        request_registry=request_registry,
    )
    logger.info("Dashboard enabled")

    logger.info("Management service started")
    yield

    logger.info("Management service stopped")


app = FastAPI(
    title="Moniker Management",
    description=(
        "Control-plane service.  Low-traffic, write-heavy.\n\n"
        "Resolver endpoints (`/resolve/*`, `/fetch/*`, `/health`, etc.) "
        "are not present on this process — use the resolver service on port 8051."
    ),
    version="0.2.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Config", "description": "Catalog configuration management"},
        {"name": "Domains", "description": "Domain governance and configuration"},
        {"name": "Models", "description": "Business models / measures"},
        {"name": "Requests", "description": "Moniker request submission and approval workflow"},
        {"name": "Dashboard", "description": "Observability dashboard"},
        {"name": "Health", "description": "Landing page"},
    ],
)

# Static files (shared CSS/JS — config UI and dashboard use them)
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

# Management sub-routers
app.include_router(config_ui_routes.router)
app.include_router(domain_routes.router)
app.include_router(model_routes.router)
app.include_router(request_routes.router)
app.include_router(dashboard_routes.router)


# ---------------------------------------------------------------------------
# Landing page — import the HTML string from main so it stays in sync.
# ---------------------------------------------------------------------------

from .main import _LANDING_HTML  # noqa: E402  (after app definition for clarity)


@app.get("/", response_class=HTMLResponse, tags=["Health"])
async def root():
    """Landing page with links to all management UIs and documentation."""
    return HTMLResponse(content=_LANDING_HTML)
