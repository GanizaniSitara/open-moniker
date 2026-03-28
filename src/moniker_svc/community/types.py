"""Community contribution types - domain types for flags, suggestions, annotations, discussions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FlagType(str, Enum):
    OUTDATED = "outdated"
    INCORRECT = "incorrect"
    MISSING = "missing"
    UNCLEAR = "unclear"


class FlagStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class SuggestionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AnnotationType(str, Enum):
    TIP = "tip"
    WARNING = "warning"
    CONTEXT = "context"
    USAGE = "usage"


class ConfigStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


# ---------------------------------------------------------------------------
# Contribution dataclasses
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Flag:
    id: str
    entity_type: str
    entity_key: str
    flag_type: str  # FlagType value
    author: str
    comment: str | None = None
    status: str = FlagStatus.OPEN.value
    resolved_by: str | None = None
    resolved_at: str | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class Suggestion:
    id: str
    entity_type: str
    entity_key: str
    field_name: str
    proposed_value: str
    author: str
    current_value: str | None = None
    reason: str | None = None
    status: str = SuggestionStatus.PENDING.value
    reviewed_by: str | None = None
    review_comment: str | None = None
    reviewed_at: str | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True, slots=True)
class AnnotationVote:
    voter: str
    created_at: str = ""


@dataclass(slots=True)
class Annotation:
    id: str
    entity_type: str
    entity_key: str
    annotation_type: str  # AnnotationType value
    content: str
    author: str
    upvote_count: int = 0
    votes: list[AnnotationVote] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class DiscussionReply:
    id: str
    content: str
    author: str
    parent_reply_id: str | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class Discussion:
    id: str
    entity_type: str
    entity_key: str
    title: str
    author: str
    replies: list[DiscussionReply] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class HelpfulVote:
    id: str
    entity_type: str
    entity_key: str
    helpful: bool
    comment: str | None = None
    author: str | None = None
    created_at: str = ""


@dataclass(slots=True)
class SharedConfig:
    id: str
    title: str
    author: str
    description: str = ""
    status: str = ConfigStatus.DRAFT.value
    forked_from: str | None = None
    moniker_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    published_at: str | None = None


# ---------------------------------------------------------------------------
# Container for all contributions on a single entity
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class EntityContributions:
    """All contributions for a single (entity_type, entity_key) pair."""
    flags: dict[str, Flag] = field(default_factory=dict)
    suggestions: dict[str, Suggestion] = field(default_factory=dict)
    annotations: dict[str, Annotation] = field(default_factory=dict)
    discussions: dict[str, Discussion] = field(default_factory=dict)
    helpful_votes: dict[str, HelpfulVote] = field(default_factory=dict)
