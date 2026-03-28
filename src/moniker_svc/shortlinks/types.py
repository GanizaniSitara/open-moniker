"""Data types and ID generation for shortlinks."""

from __future__ import annotations

import hashlib
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Base62 alphabet (URL-safe, no ambiguous chars)
_ALPHABET = string.ascii_letters + string.digits  # a-zA-Z0-9
_ID_LENGTH = 7  # ~62^7 ≈ 3.5 trillion combinations


def generate_short_id(content: str, length: int = _ID_LENGTH) -> str:
    """Generate a deterministic base62 short ID from content hash.

    Same input always produces the same ID (enables dedup).
    """
    digest = hashlib.sha256(content.encode()).digest()
    num = int.from_bytes(digest[:6], "big")  # 48 bits
    chars = []
    for _ in range(length):
        num, remainder = divmod(num, len(_ALPHABET))
        chars.append(_ALPHABET[remainder])
    return "".join(chars)


def generate_random_id(length: int = _ID_LENGTH) -> str:
    """Generate a cryptographically random base62 short ID (fallback on collision)."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


@dataclass(frozen=True)
class Shortlink:
    """A shortened alias for a moniker filter combination.

    Stored as JSON on disk. The ``base_path`` is informational — expansion
    only uses ``id`` to look up the filter state.
    """

    id: str
    base_path: str  # e.g. "fixed.income/govies/sovereign"
    filter_segments: tuple[str, ...]  # e.g. ("US", "10Y", "SHORT_DATED")
    version: str | None = None  # e.g. "3M", "20260115", "latest"
    params: dict[str, str] = field(default_factory=dict)  # query params
    label: str = ""
    created_by: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def canonical_filter(self) -> str:
        """Canonical string for the filter state (used for dedup hashing)."""
        parts = "/".join(self.filter_segments)
        if self.version:
            parts += f"@{self.version}"
        if self.params:
            qs = "&".join(f"{k}={v}" for k, v in sorted(self.params.items()))
            parts += f"?{qs}"
        return parts

    def expand(self) -> str:
        """Expand to the full moniker path (base + filters + version + params).

        Returns the path string ready for ``moniker://`` prefix.
        """
        path = self.base_path
        if self.filter_segments:
            path += "/" + "/".join(self.filter_segments)
        if self.version:
            path += f"@{self.version}"
        if self.params:
            qs = "&".join(f"{k}={v}" for k, v in sorted(self.params.items()))
            path += f"?{qs}"
        return path

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "base_path": self.base_path,
            "filter_segments": list(self.filter_segments),
            "version": self.version,
            "params": dict(self.params),
            "label": self.label,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Shortlink:
        return cls(
            id=data["id"],
            base_path=data["base_path"],
            filter_segments=tuple(data.get("filter_segments", ())),
            version=data.get("version"),
            params=data.get("params", {}),
            label=data.get("label", ""),
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at", ""),
        )
