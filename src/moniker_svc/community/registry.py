"""Community registry - thread-safe in-memory store for contributions."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from uuid import uuid4

from .types import (
    Annotation,
    AnnotationVote,
    Discussion,
    DiscussionReply,
    EntityContributions,
    Flag,
    HelpfulVote,
    Suggestion,
)

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid4().hex


class CommunityRegistry:
    """
    Thread-safe in-memory registry of community contributions.

    Keyed by (entity_type, entity_key) tuples.
    """

    def __init__(self) -> None:
        self._entities: dict[tuple[str, str], EntityContributions] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create(self, entity_type: str, entity_key: str) -> EntityContributions:
        key = (entity_type, entity_key)
        if key not in self._entities:
            self._entities[key] = EntityContributions()
        return self._entities[key]

    def _find_entity_for_id(
        self,
        collection_attr: str,
        item_id: str,
    ) -> tuple[tuple[str, str], EntityContributions] | None:
        """Find which entity contains a given contribution ID."""
        for key, contrib in self._entities.items():
            coll = getattr(contrib, collection_attr)
            if item_id in coll:
                return key, contrib
        return None

    # ------------------------------------------------------------------
    # Bulk load/dump (for persistence)
    # ------------------------------------------------------------------

    def load_entity(
        self,
        entity_type: str,
        entity_key: str,
        contrib: EntityContributions,
    ) -> None:
        with self._lock:
            self._entities[(entity_type, entity_key)] = contrib

    def dump_entity(
        self,
        entity_type: str,
        entity_key: str,
    ) -> EntityContributions | None:
        with self._lock:
            return self._entities.get((entity_type, entity_key))

    def all_entity_keys(self) -> list[tuple[str, str]]:
        with self._lock:
            return list(self._entities.keys())

    # ------------------------------------------------------------------
    # Flags
    # ------------------------------------------------------------------

    def create_flag(
        self,
        entity_type: str,
        entity_key: str,
        flag_type: str,
        author: str,
        comment: str | None = None,
    ) -> Flag:
        with self._lock:
            now = _now()
            flag = Flag(
                id=_new_id(),
                entity_type=entity_type,
                entity_key=entity_key,
                flag_type=flag_type,
                author=author,
                comment=comment,
                created_at=now,
                updated_at=now,
            )
            contrib = self._get_or_create(entity_type, entity_key)
            contrib.flags[flag.id] = flag
            return flag

    def get_flags(self, entity_type: str, entity_key: str) -> list[Flag]:
        with self._lock:
            contrib = self._entities.get((entity_type, entity_key))
            if not contrib:
                return []
            return list(contrib.flags.values())

    def get_flag_summary(self, entity_type: str, entity_key: str) -> dict:
        with self._lock:
            flags = self.get_flags(entity_type, entity_key)
            by_type: dict[str, int] = {}
            for f in flags:
                by_type[f.flag_type] = by_type.get(f.flag_type, 0) + 1
            return {"total": len(flags), "byType": by_type}

    def update_flag_status(
        self,
        flag_id: str,
        status: str,
        resolved_by: str | None = None,
    ) -> Flag | None:
        with self._lock:
            result = self._find_entity_for_id("flags", flag_id)
            if not result:
                return None
            _, contrib = result
            flag = contrib.flags[flag_id]
            now = _now()
            flag.status = status
            flag.updated_at = now
            if status in ("resolved", "dismissed"):
                flag.resolved_by = resolved_by
                flag.resolved_at = now
            return flag

    # ------------------------------------------------------------------
    # Suggestions
    # ------------------------------------------------------------------

    def create_suggestion(
        self,
        entity_type: str,
        entity_key: str,
        field_name: str,
        proposed_value: str,
        author: str,
        current_value: str | None = None,
        reason: str | None = None,
    ) -> Suggestion:
        with self._lock:
            now = _now()
            s = Suggestion(
                id=_new_id(),
                entity_type=entity_type,
                entity_key=entity_key,
                field_name=field_name,
                proposed_value=proposed_value,
                author=author,
                current_value=current_value,
                reason=reason,
                created_at=now,
                updated_at=now,
            )
            contrib = self._get_or_create(entity_type, entity_key)
            contrib.suggestions[s.id] = s
            return s

    def get_suggestions(self, entity_type: str, entity_key: str) -> list[Suggestion]:
        with self._lock:
            contrib = self._entities.get((entity_type, entity_key))
            if not contrib:
                return []
            return list(contrib.suggestions.values())

    def approve_suggestion(
        self,
        suggestion_id: str,
        reviewed_by: str | None = None,
        review_comment: str | None = None,
    ) -> Suggestion | None:
        with self._lock:
            result = self._find_entity_for_id("suggestions", suggestion_id)
            if not result:
                return None
            _, contrib = result
            s = contrib.suggestions[suggestion_id]
            now = _now()
            s.status = "approved"
            s.reviewed_by = reviewed_by
            s.review_comment = review_comment
            s.reviewed_at = now
            s.updated_at = now
            return s

    def reject_suggestion(
        self,
        suggestion_id: str,
        reviewed_by: str | None = None,
        review_comment: str | None = None,
    ) -> Suggestion | None:
        with self._lock:
            result = self._find_entity_for_id("suggestions", suggestion_id)
            if not result:
                return None
            _, contrib = result
            s = contrib.suggestions[suggestion_id]
            now = _now()
            s.status = "rejected"
            s.reviewed_by = reviewed_by
            s.review_comment = review_comment
            s.reviewed_at = now
            s.updated_at = now
            return s

    # ------------------------------------------------------------------
    # Annotations
    # ------------------------------------------------------------------

    def create_annotation(
        self,
        entity_type: str,
        entity_key: str,
        annotation_type: str,
        content: str,
        author: str,
    ) -> Annotation:
        with self._lock:
            now = _now()
            a = Annotation(
                id=_new_id(),
                entity_type=entity_type,
                entity_key=entity_key,
                annotation_type=annotation_type,
                content=content,
                author=author,
                created_at=now,
                updated_at=now,
            )
            contrib = self._get_or_create(entity_type, entity_key)
            contrib.annotations[a.id] = a
            return a

    def get_annotations(self, entity_type: str, entity_key: str) -> list[Annotation]:
        with self._lock:
            contrib = self._entities.get((entity_type, entity_key))
            if not contrib:
                return []
            anns = list(contrib.annotations.values())
            anns.sort(key=lambda a: a.upvote_count, reverse=True)
            return anns

    def upvote_annotation(self, annotation_id: str, voter: str) -> bool:
        """Add upvote. Returns True if added, False if already voted."""
        with self._lock:
            result = self._find_entity_for_id("annotations", annotation_id)
            if not result:
                return False
            _, contrib = result
            a = contrib.annotations[annotation_id]
            if any(v.voter == voter for v in a.votes):
                return False  # already voted
            a.votes.append(AnnotationVote(voter=voter, created_at=_now()))
            a.upvote_count = len(a.votes)
            a.updated_at = _now()
            return True

    def remove_upvote(self, annotation_id: str, voter: str) -> bool:
        """Remove upvote. Returns True if removed, False if not found."""
        with self._lock:
            result = self._find_entity_for_id("annotations", annotation_id)
            if not result:
                return False
            _, contrib = result
            a = contrib.annotations[annotation_id]
            original_len = len(a.votes)
            a.votes = [v for v in a.votes if v.voter != voter]
            if len(a.votes) == original_len:
                return False  # wasn't voted
            a.upvote_count = len(a.votes)
            a.updated_at = _now()
            return True

    # ------------------------------------------------------------------
    # Discussions
    # ------------------------------------------------------------------

    def create_discussion(
        self,
        entity_type: str,
        entity_key: str,
        title: str,
        author: str,
    ) -> Discussion:
        with self._lock:
            now = _now()
            d = Discussion(
                id=_new_id(),
                entity_type=entity_type,
                entity_key=entity_key,
                title=title,
                author=author,
                created_at=now,
                updated_at=now,
            )
            contrib = self._get_or_create(entity_type, entity_key)
            contrib.discussions[d.id] = d
            return d

    def get_discussions(self, entity_type: str, entity_key: str) -> list[Discussion]:
        with self._lock:
            contrib = self._entities.get((entity_type, entity_key))
            if not contrib:
                return []
            return list(contrib.discussions.values())

    def get_discussion(self, discussion_id: str) -> Discussion | None:
        with self._lock:
            result = self._find_entity_for_id("discussions", discussion_id)
            if not result:
                return None
            _, contrib = result
            return contrib.discussions[discussion_id]

    def add_reply(
        self,
        discussion_id: str,
        content: str,
        author: str,
        parent_reply_id: str | None = None,
    ) -> DiscussionReply | None:
        with self._lock:
            result = self._find_entity_for_id("discussions", discussion_id)
            if not result:
                return None
            _, contrib = result
            disc = contrib.discussions[discussion_id]
            now = _now()
            reply = DiscussionReply(
                id=_new_id(),
                content=content,
                author=author,
                parent_reply_id=parent_reply_id,
                created_at=now,
                updated_at=now,
            )
            disc.replies.append(reply)
            disc.updated_at = now
            return reply

    # ------------------------------------------------------------------
    # Helpful votes
    # ------------------------------------------------------------------

    def submit_helpful_vote(
        self,
        entity_type: str,
        entity_key: str,
        helpful: bool,
        comment: str | None = None,
        author: str | None = None,
    ) -> HelpfulVote:
        with self._lock:
            now = _now()
            vote = HelpfulVote(
                id=_new_id(),
                entity_type=entity_type,
                entity_key=entity_key,
                helpful=helpful,
                comment=comment,
                author=author,
                created_at=now,
            )
            contrib = self._get_or_create(entity_type, entity_key)
            contrib.helpful_votes[vote.id] = vote
            return vote

    def get_helpful_summary(self, entity_type: str, entity_key: str) -> dict:
        with self._lock:
            contrib = self._entities.get((entity_type, entity_key))
            if not contrib:
                return {"helpful": 0, "notHelpful": 0, "total": 0}
            votes = list(contrib.helpful_votes.values())
            helpful = sum(1 for v in votes if v.helpful)
            not_helpful = len(votes) - helpful
            return {"helpful": helpful, "notHelpful": not_helpful, "total": len(votes)}

    # ------------------------------------------------------------------
    # Activity summary
    # ------------------------------------------------------------------

    def get_activity_summary(self, entity_type: str, entity_key: str) -> dict:
        with self._lock:
            contrib = self._entities.get((entity_type, entity_key))
            if not contrib:
                return {"flags": 0, "suggestions": 0, "annotations": 0, "discussions": 0, "total": 0}
            f = len(contrib.flags)
            s = len(contrib.suggestions)
            a = len(contrib.annotations)
            d = len(contrib.discussions)
            return {
                "flags": f,
                "suggestions": s,
                "annotations": a,
                "discussions": d,
                "total": f + s + a + d,
            }
