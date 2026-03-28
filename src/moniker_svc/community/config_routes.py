"""Shared config snapshot API routes (OM-11e publishing pipeline).

Save/load/publish/fork community catalog snapshots.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

import yaml
from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_caller_identity
from ..catalog.registry import CatalogRegistry
from ..catalog.serializer import CatalogSerializer
from ..telemetry.events import CallerIdentity
from .models import ConfigSnapshotModel, SaveConfigRequest
from .storage import FileStorage
from .types import SharedConfig

logger = logging.getLogger(__name__)

config_router = APIRouter(prefix="/community/configs", tags=["Community Configs"])

# Set by configure() during lifespan startup
_storage: FileStorage | None = None
_catalog: CatalogRegistry | None = None
_serializer: CatalogSerializer | None = None


def configure(
    storage: FileStorage,
    catalog: CatalogRegistry,
    serializer: CatalogSerializer,
) -> None:
    global _storage, _catalog, _serializer
    _storage = storage
    _catalog = catalog
    _serializer = serializer


def _store() -> FileStorage:
    if _storage is None:
        raise HTTPException(status_code=503, detail="Community configs not configured")
    return _storage


def _cat() -> CatalogRegistry:
    if _catalog is None:
        raise HTTPException(status_code=503, detail="Catalog not configured")
    return _catalog


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_model(sc: SharedConfig) -> ConfigSnapshotModel:
    return ConfigSnapshotModel(
        id=sc.id,
        title=sc.title,
        description=sc.description,
        author=sc.author,
        status=sc.status,
        forked_from=sc.forked_from,
        moniker_count=sc.moniker_count,
        created_at=sc.created_at,
        updated_at=sc.updated_at,
        published_at=sc.published_at,
    )


@config_router.post("", response_model=ConfigSnapshotModel, status_code=201)
async def save_config_snapshot(
    body: SaveConfigRequest,
    caller: CallerIdentity = Depends(get_caller_identity),
):
    """Snapshot current catalog to a sharable config."""
    catalog = _cat()
    nodes = catalog.all_nodes()

    # Serialize to YAML string
    catalog_dict = _serializer.serialize_catalog(nodes)
    catalog_yaml = yaml.dump(catalog_dict, default_flow_style=False, allow_unicode=True, sort_keys=False)

    now = _now()
    sc = SharedConfig(
        id=uuid4().hex,
        title=body.title,
        description=body.description,
        author=caller.user_id or "anonymous",
        moniker_count=len(nodes),
        created_at=now,
        updated_at=now,
    )
    _store().save_config_snapshot(sc, catalog_yaml)
    logger.info("Saved config snapshot %s (%d monikers) by %s", sc.id, len(nodes), sc.author)
    return _to_model(sc)


@config_router.get("", response_model=list[ConfigSnapshotModel])
async def list_configs(status: str | None = None):
    """List all shared config snapshots, optionally filtered by status."""
    configs = _store().list_config_snapshots(status=status)
    return [_to_model(sc) for sc in configs]


@config_router.get("/{config_id}", response_model=ConfigSnapshotModel)
async def get_config(config_id: str):
    """Get metadata for a shared config."""
    result = _store().load_config_snapshot(config_id)
    if not result:
        raise HTTPException(status_code=404, detail="Config snapshot not found")
    sc, _ = result
    return _to_model(sc)


@config_router.post("/{config_id}/publish", response_model=ConfigSnapshotModel)
async def publish_config(
    config_id: str,
    caller: CallerIdentity = Depends(get_caller_identity),
):
    """Publish a draft config (draft -> published)."""
    result = _store().load_config_snapshot(config_id)
    if not result:
        raise HTTPException(status_code=404, detail="Config snapshot not found")
    sc, _ = result
    if sc.status != "draft":
        raise HTTPException(status_code=400, detail=f"Config is already {sc.status}")
    if sc.author != (caller.user_id or "anonymous") and caller.user_id:
        raise HTTPException(status_code=403, detail="Only the author can publish")

    now = _now()
    sc.status = "published"
    sc.published_at = now
    sc.updated_at = now
    _store().update_config_metadata(sc)
    logger.info("Published config snapshot %s by %s", sc.id, caller.user_id)
    return _to_model(sc)


@config_router.post("/{config_id}/fork", response_model=ConfigSnapshotModel, status_code=201)
async def fork_config(
    config_id: str,
    body: SaveConfigRequest,
    caller: CallerIdentity = Depends(get_caller_identity),
):
    """Fork a published config into a new draft under the caller's ownership."""
    result = _store().load_config_snapshot(config_id)
    if not result:
        raise HTTPException(status_code=404, detail="Config snapshot not found")
    original, catalog_yaml = result

    now = _now()
    forked = SharedConfig(
        id=uuid4().hex,
        title=body.title or f"Fork of {original.title}",
        description=body.description,
        author=caller.user_id or "anonymous",
        forked_from=config_id,
        moniker_count=original.moniker_count,
        created_at=now,
        updated_at=now,
    )
    _store().save_config_snapshot(forked, catalog_yaml)
    logger.info("Forked config %s -> %s by %s", config_id, forked.id, forked.author)
    return _to_model(forked)


@config_router.post("/{config_id}/load")
async def load_config_into_catalog(
    config_id: str,
    caller: CallerIdentity = Depends(get_caller_identity),
):
    """Load a shared config into the active catalog (replaces current)."""
    from ..catalog.loader import load_catalog

    catalog_yaml = _store().read_config_catalog_yaml(config_id)
    if catalog_yaml is None:
        raise HTTPException(status_code=404, detail="Config snapshot not found")

    try:
        catalog_dict = yaml.safe_load(catalog_yaml)
        new_catalog = load_catalog(catalog_dict)
        new_nodes = new_catalog.all_nodes()
        _cat().atomic_replace(new_nodes)
        logger.info("Loaded config %s into catalog (%d nodes) by %s", config_id, len(new_nodes), caller.user_id)
        return {"ok": True, "monikerCount": len(new_nodes)}
    except Exception as e:
        logger.error("Failed to load config %s: %s", config_id, e)
        raise HTTPException(status_code=500, detail=f"Failed to load config: {e}")
