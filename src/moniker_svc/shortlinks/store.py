"""Thread-safe, file-backed shortlink store."""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

from .types import Shortlink, generate_random_id, generate_short_id

logger = logging.getLogger(__name__)

_MAX_COLLISION_RETRIES = 5
_TILDE = "~"


class ShortlinkStore:
    """Thread-safe in-memory store with JSON file persistence.

    All resolvers (Python, Go, Java) read the same ``shortlinks.json``.
    Python is the write master; Go/Java are read-only consumers.
    """

    def __init__(self, file_path: str | Path | None = None) -> None:
        self._path = Path(file_path) if file_path else None
        self._lock = threading.RLock()
        self._links: dict[str, Shortlink] = {}  # id -> Shortlink

    # ── Persistence ──────────────────────────────────────────────────

    def load(self) -> int:
        """Load shortlinks from JSON file. Returns count loaded."""
        if not self._path or not self._path.exists():
            return 0
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            with self._lock:
                self._links = {k: Shortlink.from_dict(v) for k, v in raw.items()}
            logger.info("Loaded %d shortlinks from %s", len(self._links), self._path)
            return len(self._links)
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Failed to load shortlinks from %s: %s", self._path, exc)
            return 0

    def save(self) -> None:
        """Write current state to disk atomically (temp file + replace)."""
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {k: v.to_dict() for k, v in self._links.items()}
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(str(tmp), str(self._path))

    # ── CRUD ─────────────────────────────────────────────────────────

    def create(
        self,
        base_path: str,
        filter_segments: list[str] | tuple[str, ...],
        version: str | None = None,
        params: dict[str, str] | None = None,
        label: str = "",
        created_by: str = "",
    ) -> Shortlink:
        """Create a shortlink. Returns existing link if dedup match."""
        segments = tuple(filter_segments)
        params = params or {}

        # Build canonical filter for hashing
        tmp = Shortlink(id="", base_path=base_path, filter_segments=segments,
                        version=version, params=params)
        canonical = tmp.canonical_filter

        with self._lock:
            # Dedup: check if identical filter already exists
            for link in self._links.values():
                if link.canonical_filter == canonical:
                    return link

            # Generate deterministic ID, fall back to random on collision
            short_id = generate_short_id(canonical)
            for _ in range(_MAX_COLLISION_RETRIES):
                if short_id not in self._links:
                    break
                short_id = generate_random_id()

            link = Shortlink(
                id=short_id,
                base_path=base_path,
                filter_segments=segments,
                version=version,
                params=params,
                label=label,
                created_by=created_by,
            )
            self._links[short_id] = link
            self.save()
            return link

    def get(self, short_id: str) -> Shortlink | None:
        with self._lock:
            return self._links.get(short_id)

    def delete(self, short_id: str) -> bool:
        with self._lock:
            if short_id in self._links:
                del self._links[short_id]
                self.save()
                return True
            return False

    def all(self) -> list[Shortlink]:
        with self._lock:
            return list(self._links.values())

    def count(self) -> int:
        with self._lock:
            return len(self._links)

    # ── Path expansion (used by resolve handler) ─────────────────────

    def try_expand_path(self, path: str) -> tuple[str, str | None]:
        """Scan a moniker path for a ``~``-prefixed segment and expand it.

        Returns ``(expanded_path, alias)`` if a tilde segment was found and
        expanded, or ``(original_path, None)`` if no tilde segment exists.

        Raises ``KeyError`` if a tilde segment is found but the ID is unknown.
        """
        # Split on / but preserve dot-separated domain segments
        # The tilde segment can appear anywhere after the base path
        segments = path.split("/")
        tilde_idx = None
        for i, seg in enumerate(segments):
            if seg.startswith(_TILDE):
                tilde_idx = i
                break

        if tilde_idx is None:
            return (path, None)

        short_id = segments[tilde_idx][1:]  # strip ~
        with self._lock:
            link = self._links.get(short_id)

        if link is None:
            raise KeyError(f"Shortlink not found: {short_id}")

        # Expand: base path (everything before ~) + stored filter state
        return (link.expand(), f"~{short_id}")
