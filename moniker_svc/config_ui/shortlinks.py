"""Bitly-style shortlink registry for catalog filter state.

Generates short IDs that map to a stored filter-state dict (query params,
path fragments, etc.).  Persisted to a JSON file alongside catalog.yaml.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 6 random bytes → 8 URL-safe base64 chars (2^48 ≈ 281 trillion combinations)
_DEFAULT_ID_BYTES = 6
_MAX_COLLISION_RETRIES = 5


@dataclass(frozen=True)
class Shortlink:
    """A single shortlink entry."""

    short_id: str
    filters: dict[str, Any]          # The captured filter / query-param state
    path_prefix: str = ""            # Optional base path the filters apply to
    label: str = ""                  # Optional human-readable label
    created_at: float = 0.0          # Unix epoch seconds
    created_by: str = ""             # Caller identity if available

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Shortlink:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ShortlinkRegistry:
    """Thread-safe, file-backed shortlink store."""

    def __init__(self, persistence_path: str | Path | None = None) -> None:
        self._lock = threading.Lock()
        self._links: dict[str, Shortlink] = {}
        self._persistence_path: Path | None = (
            Path(persistence_path) if persistence_path else None
        )
        if self._persistence_path:
            self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(
        self,
        filters: dict[str, Any],
        *,
        path_prefix: str = "",
        label: str = "",
        created_by: str = "",
    ) -> Shortlink:
        """Create a new shortlink for the given filter state."""
        with self._lock:
            short_id = self._generate_unique_id()
            link = Shortlink(
                short_id=short_id,
                filters=filters,
                path_prefix=path_prefix,
                label=label,
                created_at=time.time(),
                created_by=created_by,
            )
            self._links[short_id] = link
            self._persist()
            logger.info("Created shortlink %s → %d filter keys", short_id, len(filters))
            return link

    def get(self, short_id: str) -> Shortlink | None:
        """Resolve a short ID to its shortlink, or *None*."""
        return self._links.get(short_id)

    def delete(self, short_id: str) -> bool:
        """Remove a shortlink.  Returns *True* if it existed."""
        with self._lock:
            if short_id not in self._links:
                return False
            del self._links[short_id]
            self._persist()
            logger.info("Deleted shortlink %s", short_id)
            return True

    def all(self) -> list[Shortlink]:
        """Return all shortlinks, newest first."""
        return sorted(self._links.values(), key=lambda s: s.created_at, reverse=True)

    def count(self) -> int:
        return len(self._links)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _generate_unique_id(self) -> str:
        """Generate a unique short ID, retrying on collision."""
        for _ in range(_MAX_COLLISION_RETRIES):
            candidate = secrets.token_urlsafe(_DEFAULT_ID_BYTES)
            if candidate not in self._links:
                return candidate
        raise RuntimeError("Failed to generate unique short ID after retries")

    def _persist(self) -> None:
        """Write all links to the JSON file (caller must hold _lock)."""
        if not self._persistence_path:
            return
        try:
            data = [link.to_dict() for link in self._links.values()]
            tmp = self._persistence_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            tmp.replace(self._persistence_path)
        except Exception:
            logger.exception("Failed to persist shortlinks to %s", self._persistence_path)

    def _load(self) -> None:
        """Load existing links from the JSON file (called once at init)."""
        if not self._persistence_path or not self._persistence_path.exists():
            return
        try:
            with open(self._persistence_path, encoding="utf-8") as f:
                data = json.load(f)
            for entry in data:
                link = Shortlink.from_dict(entry)
                self._links[link.short_id] = link
            logger.info(
                "Loaded %d shortlinks from %s", len(self._links), self._persistence_path,
            )
        except Exception:
            logger.exception("Failed to load shortlinks from %s", self._persistence_path)
