"""Shortlink (alias) system for monikers.

Short aliases encode complex filter combinations into tilde-prefixed
path segments (e.g. ``~xK9f2p``) that expand transparently during
moniker resolution.
"""

from .store import ShortlinkStore
from .types import Shortlink, generate_short_id

__all__ = ["Shortlink", "ShortlinkStore", "generate_short_id"]
