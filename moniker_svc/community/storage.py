"""File-based JSON storage for community contributions.

Atomic writes via temp-file + os.replace for crash safety.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from .types import (
    Annotation,
    AnnotationVote,
    Discussion,
    DiscussionReply,
    EntityContributions,
    Flag,
    HelpfulVote,
    SharedConfig,
    Suggestion,
)

logger = logging.getLogger(__name__)


class FileStorage:
    """JSON file persistence for community data."""

    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _entity_dir(self, entity_type: str, entity_key: str) -> Path:
        return self._base_dir / "entities" / entity_type / entity_key

    def _atomic_write(self, path: Path, data: Any) -> None:
        """Write JSON atomically: write to .tmp, fsync, os.replace."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(path))

    def _read_json(self, path: Path) -> Any:
        """Read and parse a JSON file, returning None if missing."""
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _flag_to_dict(f: Flag) -> dict:
        return {
            "id": f.id,
            "entityType": f.entity_type,
            "entityKey": f.entity_key,
            "flagType": f.flag_type,
            "comment": f.comment,
            "author": f.author,
            "status": f.status,
            "resolvedBy": f.resolved_by,
            "resolvedAt": f.resolved_at,
            "createdAt": f.created_at,
            "updatedAt": f.updated_at,
        }

    @staticmethod
    def _flag_from_dict(d: dict) -> Flag:
        return Flag(
            id=d["id"],
            entity_type=d["entityType"],
            entity_key=d["entityKey"],
            flag_type=d["flagType"],
            author=d["author"],
            comment=d.get("comment"),
            status=d.get("status", "open"),
            resolved_by=d.get("resolvedBy"),
            resolved_at=d.get("resolvedAt"),
            created_at=d.get("createdAt", ""),
            updated_at=d.get("updatedAt", ""),
        )

    @staticmethod
    def _suggestion_to_dict(s: Suggestion) -> dict:
        return {
            "id": s.id,
            "entityType": s.entity_type,
            "entityKey": s.entity_key,
            "fieldName": s.field_name,
            "currentValue": s.current_value,
            "proposedValue": s.proposed_value,
            "reason": s.reason,
            "author": s.author,
            "status": s.status,
            "reviewedBy": s.reviewed_by,
            "reviewComment": s.review_comment,
            "reviewedAt": s.reviewed_at,
            "createdAt": s.created_at,
            "updatedAt": s.updated_at,
        }

    @staticmethod
    def _suggestion_from_dict(d: dict) -> Suggestion:
        return Suggestion(
            id=d["id"],
            entity_type=d["entityType"],
            entity_key=d["entityKey"],
            field_name=d["fieldName"],
            proposed_value=d["proposedValue"],
            author=d["author"],
            current_value=d.get("currentValue"),
            reason=d.get("reason"),
            status=d.get("status", "pending"),
            reviewed_by=d.get("reviewedBy"),
            review_comment=d.get("reviewComment"),
            reviewed_at=d.get("reviewedAt"),
            created_at=d.get("createdAt", ""),
            updated_at=d.get("updatedAt", ""),
        )

    @staticmethod
    def _annotation_to_dict(a: Annotation) -> dict:
        return {
            "id": a.id,
            "entityType": a.entity_type,
            "entityKey": a.entity_key,
            "annotationType": a.annotation_type,
            "content": a.content,
            "author": a.author,
            "upvoteCount": a.upvote_count,
            "votes": [
                {"voter": v.voter, "createdAt": v.created_at}
                for v in a.votes
            ],
            "createdAt": a.created_at,
            "updatedAt": a.updated_at,
        }

    @staticmethod
    def _annotation_from_dict(d: dict) -> Annotation:
        votes = [
            AnnotationVote(voter=v["voter"], created_at=v.get("createdAt", ""))
            for v in d.get("votes", [])
        ]
        return Annotation(
            id=d["id"],
            entity_type=d["entityType"],
            entity_key=d["entityKey"],
            annotation_type=d["annotationType"],
            content=d["content"],
            author=d["author"],
            upvote_count=d.get("upvoteCount", len(votes)),
            votes=votes,
            created_at=d.get("createdAt", ""),
            updated_at=d.get("updatedAt", ""),
        )

    @staticmethod
    def _discussion_to_dict(disc: Discussion) -> dict:
        return {
            "id": disc.id,
            "entityType": disc.entity_type,
            "entityKey": disc.entity_key,
            "title": disc.title,
            "author": disc.author,
            "replies": [
                {
                    "id": r.id,
                    "parentReplyId": r.parent_reply_id,
                    "content": r.content,
                    "author": r.author,
                    "createdAt": r.created_at,
                    "updatedAt": r.updated_at,
                }
                for r in disc.replies
            ],
            "createdAt": disc.created_at,
            "updatedAt": disc.updated_at,
        }

    @staticmethod
    def _discussion_from_dict(d: dict) -> Discussion:
        replies = [
            DiscussionReply(
                id=r["id"],
                content=r["content"],
                author=r["author"],
                parent_reply_id=r.get("parentReplyId"),
                created_at=r.get("createdAt", ""),
                updated_at=r.get("updatedAt", ""),
            )
            for r in d.get("replies", [])
        ]
        return Discussion(
            id=d["id"],
            entity_type=d["entityType"],
            entity_key=d["entityKey"],
            title=d["title"],
            author=d["author"],
            replies=replies,
            created_at=d.get("createdAt", ""),
            updated_at=d.get("updatedAt", ""),
        )

    @staticmethod
    def _helpful_to_dict(h: HelpfulVote) -> dict:
        return {
            "id": h.id,
            "entityType": h.entity_type,
            "entityKey": h.entity_key,
            "helpful": h.helpful,
            "comment": h.comment,
            "author": h.author,
            "createdAt": h.created_at,
        }

    @staticmethod
    def _helpful_from_dict(d: dict) -> HelpfulVote:
        return HelpfulVote(
            id=d["id"],
            entity_type=d["entityType"],
            entity_key=d["entityKey"],
            helpful=d["helpful"],
            comment=d.get("comment"),
            author=d.get("author"),
            created_at=d.get("createdAt", ""),
        )

    # ------------------------------------------------------------------
    # Entity persistence
    # ------------------------------------------------------------------

    def save_entity(
        self,
        entity_type: str,
        entity_key: str,
        contrib: EntityContributions,
    ) -> None:
        """Persist all contribution files for a single entity."""
        edir = self._entity_dir(entity_type, entity_key)

        if contrib.flags:
            self._atomic_write(
                edir / "flags.json",
                {"flags": [self._flag_to_dict(f) for f in contrib.flags.values()]},
            )
        if contrib.suggestions:
            self._atomic_write(
                edir / "suggestions.json",
                {"suggestions": [self._suggestion_to_dict(s) for s in contrib.suggestions.values()]},
            )
        if contrib.annotations:
            self._atomic_write(
                edir / "annotations.json",
                {"annotations": [self._annotation_to_dict(a) for a in contrib.annotations.values()]},
            )
        if contrib.discussions:
            self._atomic_write(
                edir / "discussions.json",
                {"discussions": [self._discussion_to_dict(d) for d in contrib.discussions.values()]},
            )
        if contrib.helpful_votes:
            self._atomic_write(
                edir / "helpful.json",
                {"votes": [self._helpful_to_dict(h) for h in contrib.helpful_votes.values()]},
            )

    def load_entity(self, entity_type: str, entity_key: str) -> EntityContributions | None:
        """Load all contribution files for a single entity. Returns None if directory missing."""
        edir = self._entity_dir(entity_type, entity_key)
        if not edir.exists():
            return None

        contrib = EntityContributions()

        data = self._read_json(edir / "flags.json")
        if data:
            for d in data.get("flags", []):
                f = self._flag_from_dict(d)
                contrib.flags[f.id] = f

        data = self._read_json(edir / "suggestions.json")
        if data:
            for d in data.get("suggestions", []):
                s = self._suggestion_from_dict(d)
                contrib.suggestions[s.id] = s

        data = self._read_json(edir / "annotations.json")
        if data:
            for d in data.get("annotations", []):
                a = self._annotation_from_dict(d)
                contrib.annotations[a.id] = a

        data = self._read_json(edir / "discussions.json")
        if data:
            for d in data.get("discussions", []):
                disc = self._discussion_from_dict(d)
                contrib.discussions[disc.id] = disc

        data = self._read_json(edir / "helpful.json")
        if data:
            for d in data.get("votes", []):
                h = self._helpful_from_dict(d)
                contrib.helpful_votes[h.id] = h

        return contrib

    def load_all(self) -> dict[tuple[str, str], EntityContributions]:
        """Scan entities/ directory and load everything. Used at startup."""
        result: dict[tuple[str, str], EntityContributions] = {}
        entities_dir = self._base_dir / "entities"
        if not entities_dir.exists():
            return result

        for type_dir in entities_dir.iterdir():
            if not type_dir.is_dir():
                continue
            entity_type = type_dir.name
            for key_dir in type_dir.iterdir():
                if not key_dir.is_dir():
                    continue
                entity_key = key_dir.name
                contrib = self.load_entity(entity_type, entity_key)
                if contrib:
                    result[(entity_type, entity_key)] = contrib

        return result

    # ------------------------------------------------------------------
    # Shared config snapshots
    # ------------------------------------------------------------------

    def _configs_dir(self) -> Path:
        return self._base_dir / "configs"

    def save_config_snapshot(
        self,
        config: SharedConfig,
        catalog_yaml: str,
    ) -> None:
        """Save a shared config snapshot (metadata + catalog YAML)."""
        cdir = self._configs_dir() / config.id
        self._atomic_write(cdir / "metadata.json", {
            "id": config.id,
            "title": config.title,
            "description": config.description,
            "author": config.author,
            "status": config.status,
            "forkedFrom": config.forked_from,
            "monikerCount": config.moniker_count,
            "createdAt": config.created_at,
            "updatedAt": config.updated_at,
            "publishedAt": config.published_at,
        })
        # Write catalog YAML (also atomic)
        cdir.mkdir(parents=True, exist_ok=True)
        catalog_path = cdir / "catalog.yaml"
        tmp_path = catalog_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(catalog_yaml)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(catalog_path))

    def load_config_snapshot(self, config_id: str) -> tuple[SharedConfig, str] | None:
        """Load a shared config snapshot. Returns (metadata, catalog_yaml) or None."""
        cdir = self._configs_dir() / config_id
        meta = self._read_json(cdir / "metadata.json")
        if not meta:
            return None
        catalog_path = cdir / "catalog.yaml"
        catalog_yaml = ""
        if catalog_path.exists():
            catalog_yaml = catalog_path.read_text(encoding="utf-8")
        sc = SharedConfig(
            id=meta["id"],
            title=meta["title"],
            author=meta["author"],
            description=meta.get("description", ""),
            status=meta.get("status", "draft"),
            forked_from=meta.get("forkedFrom"),
            moniker_count=meta.get("monikerCount", 0),
            created_at=meta.get("createdAt", ""),
            updated_at=meta.get("updatedAt", ""),
            published_at=meta.get("publishedAt"),
        )
        return sc, catalog_yaml

    def list_config_snapshots(self, status: str | None = None) -> list[SharedConfig]:
        """List all shared config snapshots, optionally filtered by status."""
        result: list[SharedConfig] = []
        configs_dir = self._configs_dir()
        if not configs_dir.exists():
            return result
        for cdir in configs_dir.iterdir():
            if not cdir.is_dir():
                continue
            meta = self._read_json(cdir / "metadata.json")
            if not meta:
                continue
            if status and meta.get("status") != status:
                continue
            result.append(SharedConfig(
                id=meta["id"],
                title=meta["title"],
                author=meta["author"],
                description=meta.get("description", ""),
                status=meta.get("status", "draft"),
                forked_from=meta.get("forkedFrom"),
                moniker_count=meta.get("monikerCount", 0),
                created_at=meta.get("createdAt", ""),
                updated_at=meta.get("updatedAt", ""),
                published_at=meta.get("publishedAt"),
            ))
        result.sort(key=lambda c: c.created_at, reverse=True)
        return result

    def update_config_metadata(self, config: SharedConfig) -> None:
        """Update just the metadata.json for a config snapshot."""
        cdir = self._configs_dir() / config.id
        self._atomic_write(cdir / "metadata.json", {
            "id": config.id,
            "title": config.title,
            "description": config.description,
            "author": config.author,
            "status": config.status,
            "forkedFrom": config.forked_from,
            "monikerCount": config.moniker_count,
            "createdAt": config.created_at,
            "updatedAt": config.updated_at,
            "publishedAt": config.published_at,
        })

    def read_config_catalog_yaml(self, config_id: str) -> str | None:
        """Read just the catalog.yaml for a config snapshot."""
        path = self._configs_dir() / config_id / "catalog.yaml"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
