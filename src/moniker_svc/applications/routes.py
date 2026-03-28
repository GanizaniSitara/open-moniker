"""FastAPI routes for Application Configuration API."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from .types import Application
from .registry import ApplicationRegistry
from .loader import load_applications_from_yaml
from .serializer import save_applications_to_yaml
from .models import (
    ApplicationModel,
    ApplicationListResponse,
    ApplicationDetailResponse,
    ApplicationsForDatasetResponse,
    ApplicationsForFieldResponse,
    CreateApplicationRequest,
    UpdateApplicationRequest,
    SaveResponse,
    ReloadResponse,
)

logger = logging.getLogger(__name__)

# Create router with Applications tag for OpenAPI grouping
router = APIRouter(prefix="/applications", tags=["Applications"])

# Configuration - will be set during app startup
_application_registry: ApplicationRegistry | None = None
_applications_yaml_path: str = "applications.yaml"


def configure(
    application_registry: ApplicationRegistry,
    applications_yaml_path: str = "applications.yaml",
) -> None:
    """Configure the Application routes."""
    global _application_registry, _applications_yaml_path
    _application_registry = application_registry
    _applications_yaml_path = applications_yaml_path


def _get_application_registry() -> ApplicationRegistry:
    """Get the application registry, raising if not configured."""
    if _application_registry is None:
        raise HTTPException(status_code=503, detail="Application configuration not initialized")
    return _application_registry


def _app_to_model(app: Application) -> ApplicationModel:
    """Convert Application dataclass to Pydantic model."""
    return ApplicationModel(
        key=app.key,
        display_name=app.display_name,
        description=app.description,
        category=app.category,
        color=app.color,
        status=app.status,
        owner=app.owner,
        tech_lead=app.tech_lead,
        support_channel=app.support_channel,
        datasets=list(app.datasets),
        fields=list(app.fields),
        documentation_url=app.documentation_url,
        wiki_link=app.wiki_link,
    )


# =============================================================================
# UI
# =============================================================================

@router.get("/ui", response_class=HTMLResponse)
async def applications_ui():
    """Serve the Applications Browser UI."""
    static_dir = Path(__file__).parent / "static"
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Applications UI not found")
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"), status_code=200)


# =============================================================================
# Application CRUD Endpoints
# =============================================================================

@router.get("", response_model=ApplicationListResponse)
async def list_applications():
    """List all applications."""
    registry = _get_application_registry()
    apps = registry.all_applications()

    return ApplicationListResponse(
        applications=[_app_to_model(a) for a in apps],
        count=len(apps),
    )


@router.get("/for-dataset/{path:path}", response_model=ApplicationsForDatasetResponse)
async def applications_for_dataset(path: str):
    """
    Find applications that reference a given dataset path.

    Uses glob matching against each application's dataset patterns.
    """
    registry = _get_application_registry()
    matches = registry.find_by_dataset(path)

    return ApplicationsForDatasetResponse(
        dataset_path=path,
        applications=[_app_to_model(a) for a in matches],
        count=len(matches),
    )


@router.get("/for-field/{path:path}", response_model=ApplicationsForFieldResponse)
async def applications_for_field(path: str):
    """
    Find applications that reference a given field/model path.

    Uses exact matching against each application's field list.
    """
    registry = _get_application_registry()
    matches = registry.find_by_field(path)

    return ApplicationsForFieldResponse(
        field_path=path,
        applications=[_app_to_model(a) for a in matches],
        count=len(matches),
    )


@router.get("/{key}", response_model=ApplicationDetailResponse)
async def get_application(key: str):
    """Get a single application by key."""
    registry = _get_application_registry()

    app = registry.get(key)
    if app is None:
        raise HTTPException(status_code=404, detail=f"Application not found: {key}")

    return ApplicationDetailResponse(
        application=_app_to_model(app),
        dataset_count=len(app.datasets),
        field_count=len(app.fields),
    )


@router.post("", response_model=ApplicationModel, status_code=201)
async def create_application(request: CreateApplicationRequest):
    """Create a new application."""
    registry = _get_application_registry()

    if registry.exists(request.key):
        raise HTTPException(status_code=409, detail=f"Application already exists: {request.key}")

    app = Application(
        key=request.key,
        display_name=request.display_name or request.key,
        description=request.description,
        category=request.category,
        color=request.color,
        status=request.status,
        owner=request.owner,
        tech_lead=request.tech_lead,
        support_channel=request.support_channel,
        datasets=request.datasets,
        fields=request.fields,
        documentation_url=request.documentation_url,
        wiki_link=request.wiki_link,
    )

    registry.register(app)
    logger.info(f"Created application: {request.key}")

    return _app_to_model(app)


@router.put("/{key}", response_model=ApplicationModel)
async def update_application(key: str, request: UpdateApplicationRequest):
    """Update an existing application. Only provided fields are updated."""
    registry = _get_application_registry()

    existing = registry.get(key)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Application not found: {key}")

    updated_display_name = request.display_name if request.display_name is not None else existing.display_name
    app = Application(
        key=key,
        display_name=updated_display_name or key,
        description=request.description if request.description is not None else existing.description,
        category=request.category if request.category is not None else existing.category,
        color=request.color if request.color is not None else existing.color,
        status=request.status if request.status is not None else existing.status,
        owner=request.owner if request.owner is not None else existing.owner,
        tech_lead=request.tech_lead if request.tech_lead is not None else existing.tech_lead,
        support_channel=request.support_channel if request.support_channel is not None else existing.support_channel,
        datasets=request.datasets if request.datasets is not None else list(existing.datasets),
        fields=request.fields if request.fields is not None else list(existing.fields),
        documentation_url=request.documentation_url if request.documentation_url is not None else existing.documentation_url,
        wiki_link=request.wiki_link if request.wiki_link is not None else existing.wiki_link,
    )

    registry.register_or_update(app)
    logger.info(f"Updated application: {key}")

    return _app_to_model(app)


@router.delete("/{key}")
async def delete_application(key: str):
    """Delete an application."""
    registry = _get_application_registry()

    if not registry.exists(key):
        raise HTTPException(status_code=404, detail=f"Application not found: {key}")

    registry.delete(key)
    logger.info(f"Deleted application: {key}")

    return {"success": True, "message": f"Application '{key}' deleted"}


# =============================================================================
# Save/Reload Endpoints
# =============================================================================

@router.post("/save", response_model=SaveResponse)
async def save_applications():
    """Save all applications to YAML file."""
    registry = _get_application_registry()

    output_path = Path(_applications_yaml_path)
    try:
        save_applications_to_yaml(registry, output_path)
        count = registry.count()

        logger.info(f"Saved {count} applications to {output_path}")

        return SaveResponse(
            success=True,
            message=f"Saved {count} applications to {output_path}",
            file_path=str(output_path.absolute()),
        )
    except Exception as e:
        logger.error(f"Failed to save applications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")


@router.post("/reload", response_model=ReloadResponse)
async def reload_applications():
    """Reload applications from YAML file."""
    registry = _get_application_registry()
    source_path = Path(_applications_yaml_path)

    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Applications file not found: {source_path}")

    try:
        registry.clear()
        apps = load_applications_from_yaml(source_path, registry)

        logger.info(f"Reloaded {len(apps)} applications from {source_path}")

        return ReloadResponse(
            success=True,
            message=f"Reloaded {len(apps)} applications from {source_path}",
            applications_loaded=len(apps),
        )
    except Exception as e:
        logger.error(f"Failed to reload applications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload: {str(e)}")
