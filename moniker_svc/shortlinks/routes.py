"""FastAPI routes for shortlink CRUD API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from .models import (
    CreateShortlinkRequest,
    DeleteResponse,
    ShortlinkListResponse,
    ShortlinkModel,
)
from .store import ShortlinkStore
from .types import Shortlink

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/s", tags=["Shortlinks"])

_store: ShortlinkStore | None = None


def configure(store: ShortlinkStore) -> None:
    """Set the shortlink store for route handlers."""
    global _store
    _store = store


def _get_store() -> ShortlinkStore:
    if _store is None:
        raise HTTPException(status_code=503, detail="Shortlink service not configured")
    return _store


def _to_model(link: Shortlink) -> ShortlinkModel:
    return ShortlinkModel(
        id=link.id,
        base_path=link.base_path,
        filter_segments=list(link.filter_segments),
        params=link.params,
        label=link.label,
        created_by=link.created_by,
        created_at=link.created_at,
        resolve_path=f"{link.base_path}/filter@{link.id}",
        expanded_path=link.expand(),
    )


# ── Routes ───────────────────────────────────────────────────────────

@router.post("", response_model=ShortlinkModel)
async def create_shortlink(req: CreateShortlinkRequest):
    """Create a short link for a moniker filter combination.

    If an identical filter already exists, returns the existing link (dedup).
    """
    store = _get_store()
    link = store.create(
        base_path=req.base_path,
        filter_segments=req.filter_segments,
        params=req.params,
        label=req.label,
    )
    model = _to_model(link)
    return JSONResponse(content=model.model_dump(), status_code=201)


@router.get("", response_model=ShortlinkListResponse)
async def list_shortlinks():
    """List all shortlinks."""
    store = _get_store()
    links = store.all()
    return ShortlinkListResponse(
        shortlinks=[_to_model(link) for link in links],
        count=len(links),
    )


@router.get("/{short_id}", response_model=ShortlinkModel)
async def get_shortlink(short_id: str):
    """Inspect a shortlink by ID."""
    store = _get_store()
    link = store.get(short_id)
    if link is None:
        raise HTTPException(status_code=404, detail=f"Shortlink '{short_id}' not found")
    return _to_model(link)


@router.delete("/{short_id}", response_model=DeleteResponse)
async def delete_shortlink(short_id: str):
    """Delete a shortlink."""
    store = _get_store()
    deleted = store.delete(short_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Shortlink '{short_id}' not found")
    return DeleteResponse(success=True, message=f"Shortlink '{short_id}' deleted")
