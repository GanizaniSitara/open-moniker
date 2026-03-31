"""Community contribution API routes.

Endpoints mirror the existing Next.js /api/contributions/* contract
so the frontend needs zero changes (proxied via Next.js rewrite).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from .models import (
    ActivitySummaryModel,
    AnnotationModel,
    CreateAnnotationRequest,
    CreateDiscussionRequest,
    CreateFlagRequest,
    CreateReplyRequest,
    CreateSuggestionRequest,
    DiscussionDetailModel,
    DiscussionModel,
    FlagModel,
    FlagSummaryModel,
    HelpfulSummaryModel,
    HelpfulVoteRequest,
    ReplyModel,
    ReviewSuggestionRequest,
    SuggestionModel,
    UpdateFlagStatusRequest,
    UpvoteRequest,
    VoteModel,
)
from .registry import CommunityRegistry
from .storage import FileStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/community", tags=["Community"])

# Set by configure() during lifespan startup
_registry: CommunityRegistry | None = None
_storage: FileStorage | None = None


def configure(
    registry: CommunityRegistry,
    storage: FileStorage,
) -> None:
    global _registry, _storage
    _registry = registry
    _storage = storage


def _reg() -> CommunityRegistry:
    if _registry is None:
        raise HTTPException(status_code=503, detail="Community service not configured")
    return _registry


def _auto_save(entity_type: str, entity_key: str) -> None:
    """Persist the changed entity to disk after a mutation."""
    if _storage and _registry:
        try:
            contrib = _registry.dump_entity(entity_type, entity_key)
            if contrib:
                _storage.save_entity(entity_type, entity_key, contrib)
        except Exception as e:
            logger.error("Community auto-save failed for %s/%s: %s", entity_type, entity_key, e)


# ---------------------------------------------------------------------------
# Helpers: dataclass -> Pydantic model
# ---------------------------------------------------------------------------

def _flag_model(f) -> FlagModel:
    return FlagModel(
        id=f.id, entity_type=f.entity_type, entity_key=f.entity_key,
        flag_type=f.flag_type, comment=f.comment, author=f.author,
        status=f.status, resolved_by=f.resolved_by, resolved_at=f.resolved_at,
        created_at=f.created_at, updated_at=f.updated_at,
    )


def _suggestion_model(s) -> SuggestionModel:
    return SuggestionModel(
        id=s.id, entity_type=s.entity_type, entity_key=s.entity_key,
        field_name=s.field_name, current_value=s.current_value,
        proposed_value=s.proposed_value, reason=s.reason, author=s.author,
        status=s.status, reviewed_by=s.reviewed_by,
        review_comment=s.review_comment, reviewed_at=s.reviewed_at,
        created_at=s.created_at, updated_at=s.updated_at,
    )


def _annotation_model(a) -> AnnotationModel:
    return AnnotationModel(
        id=a.id, entity_type=a.entity_type, entity_key=a.entity_key,
        annotation_type=a.annotation_type, content=a.content, author=a.author,
        upvote_count=a.upvote_count,
        votes=[VoteModel(voter=v.voter, created_at=v.created_at) for v in a.votes],
        created_at=a.created_at, updated_at=a.updated_at,
    )


def _reply_model(r) -> ReplyModel:
    return ReplyModel(
        id=r.id, parent_reply_id=r.parent_reply_id,
        content=r.content, author=r.author,
        created_at=r.created_at, updated_at=r.updated_at,
    )


def _discussion_model(d) -> DiscussionModel:
    return DiscussionModel(
        id=d.id, entity_type=d.entity_type, entity_key=d.entity_key,
        title=d.title, author=d.author, reply_count=len(d.replies),
        created_at=d.created_at, updated_at=d.updated_at,
    )


def _discussion_detail_model(d) -> DiscussionDetailModel:
    return DiscussionDetailModel(
        id=d.id, entity_type=d.entity_type, entity_key=d.entity_key,
        title=d.title, author=d.author,
        replies=[_reply_model(r) for r in d.replies],
        created_at=d.created_at, updated_at=d.updated_at,
    )


# ===================================================================
# Flags
# ===================================================================

@router.get("/flags", response_model=list[FlagModel])
async def get_flags(
    entityType: str = Query(...),
    entityKey: str = Query(...),
):
    return [_flag_model(f) for f in _reg().get_flags(entityType, entityKey)]


@router.post("/flags", response_model=FlagModel, status_code=201)
async def create_flag(body: CreateFlagRequest):
    flag = _reg().create_flag(
        entity_type=body.entity_type,
        entity_key=body.entity_key,
        flag_type=body.flag_type,
        author=body.author,
        comment=body.comment,
    )
    _auto_save(body.entity_type, body.entity_key)
    return _flag_model(flag)


@router.get("/flags/summary", response_model=FlagSummaryModel)
async def get_flag_summary(
    entityType: str = Query(...),
    entityKey: str = Query(...),
):
    summary = _reg().get_flag_summary(entityType, entityKey)
    return FlagSummaryModel(total=summary["total"], by_type=summary["byType"])


@router.patch("/flags/{flag_id}/status", response_model=FlagModel)
async def update_flag_status(flag_id: str, body: UpdateFlagStatusRequest):
    flag = _reg().update_flag_status(flag_id, body.status, body.resolved_by)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    _auto_save(flag.entity_type, flag.entity_key)
    return _flag_model(flag)


# ===================================================================
# Suggestions
# ===================================================================

@router.get("/suggestions", response_model=list[SuggestionModel])
async def get_suggestions(
    entityType: str = Query(...),
    entityKey: str = Query(...),
):
    return [_suggestion_model(s) for s in _reg().get_suggestions(entityType, entityKey)]


@router.post("/suggestions", response_model=SuggestionModel, status_code=201)
async def create_suggestion(body: CreateSuggestionRequest):
    s = _reg().create_suggestion(
        entity_type=body.entity_type,
        entity_key=body.entity_key,
        field_name=body.field_name,
        proposed_value=body.proposed_value,
        author=body.author,
        current_value=body.current_value,
        reason=body.reason,
    )
    _auto_save(body.entity_type, body.entity_key)
    return _suggestion_model(s)


@router.post("/suggestions/{suggestion_id}/approve", response_model=SuggestionModel)
async def approve_suggestion(suggestion_id: str, body: ReviewSuggestionRequest):
    s = _reg().approve_suggestion(suggestion_id, body.reviewed_by, body.review_comment)
    if not s:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    _auto_save(s.entity_type, s.entity_key)
    return _suggestion_model(s)


@router.post("/suggestions/{suggestion_id}/reject", response_model=SuggestionModel)
async def reject_suggestion(suggestion_id: str, body: ReviewSuggestionRequest):
    s = _reg().reject_suggestion(suggestion_id, body.reviewed_by, body.review_comment)
    if not s:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    _auto_save(s.entity_type, s.entity_key)
    return _suggestion_model(s)


# ===================================================================
# Annotations
# ===================================================================

@router.get("/annotations", response_model=list[AnnotationModel])
async def get_annotations(
    entityType: str = Query(...),
    entityKey: str = Query(...),
):
    return [_annotation_model(a) for a in _reg().get_annotations(entityType, entityKey)]


@router.post("/annotations", response_model=AnnotationModel, status_code=201)
async def create_annotation(body: CreateAnnotationRequest):
    a = _reg().create_annotation(
        entity_type=body.entity_type,
        entity_key=body.entity_key,
        annotation_type=body.annotation_type,
        content=body.content,
        author=body.author,
    )
    _auto_save(body.entity_type, body.entity_key)
    return _annotation_model(a)


@router.post("/annotations/{annotation_id}/upvote", status_code=200)
async def upvote_annotation(annotation_id: str, body: UpvoteRequest):
    added = _reg().upvote_annotation(annotation_id, body.voter)
    if not added:
        # Idempotent — already voted or annotation not found
        pass
    # Find entity to auto-save
    result = _reg()._find_entity_for_id("annotations", annotation_id)
    if result:
        (et, ek), _ = result
        _auto_save(et, ek)
    return {"ok": True}


@router.delete("/annotations/{annotation_id}/upvote", status_code=200)
async def remove_upvote(annotation_id: str, body: UpvoteRequest):
    _reg().remove_upvote(annotation_id, body.voter)
    result = _reg()._find_entity_for_id("annotations", annotation_id)
    if result:
        (et, ek), _ = result
        _auto_save(et, ek)
    return {"ok": True}


# ===================================================================
# Discussions
# ===================================================================

@router.get("/discussions", response_model=list[DiscussionModel])
async def get_discussions(
    entityType: str = Query(...),
    entityKey: str = Query(...),
):
    return [_discussion_model(d) for d in _reg().get_discussions(entityType, entityKey)]


@router.post("/discussions", response_model=DiscussionModel, status_code=201)
async def create_discussion(body: CreateDiscussionRequest):
    d = _reg().create_discussion(
        entity_type=body.entity_type,
        entity_key=body.entity_key,
        title=body.title,
        author=body.author,
    )
    _auto_save(body.entity_type, body.entity_key)
    return _discussion_model(d)


@router.get("/discussions/{discussion_id}", response_model=DiscussionDetailModel)
async def get_discussion(discussion_id: str):
    d = _reg().get_discussion(discussion_id)
    if not d:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return _discussion_detail_model(d)


@router.post("/discussions/{discussion_id}/replies", response_model=ReplyModel, status_code=201)
async def add_reply(discussion_id: str, body: CreateReplyRequest):
    reply = _reg().add_reply(
        discussion_id=discussion_id,
        content=body.content,
        author=body.author,
        parent_reply_id=body.parent_reply_id,
    )
    if not reply:
        raise HTTPException(status_code=404, detail="Discussion not found")
    # Find entity to auto-save
    disc = _reg().get_discussion(discussion_id)
    if disc:
        _auto_save(disc.entity_type, disc.entity_key)
    return _reply_model(reply)


# ===================================================================
# Helpful votes
# ===================================================================

@router.get("/helpful", response_model=HelpfulSummaryModel)
async def get_helpful_summary(
    entityType: str = Query(...),
    entityKey: str = Query(...),
):
    summary = _reg().get_helpful_summary(entityType, entityKey)
    return HelpfulSummaryModel(
        helpful=summary["helpful"],
        not_helpful=summary["notHelpful"],
        total=summary["total"],
    )


@router.post("/helpful", status_code=201)
async def submit_helpful_vote(body: HelpfulVoteRequest):
    _reg().submit_helpful_vote(
        entity_type=body.entity_type,
        entity_key=body.entity_key,
        helpful=body.helpful,
        comment=body.comment,
        author=body.author,
    )
    _auto_save(body.entity_type, body.entity_key)
    return {"ok": True}


# ===================================================================
# Activity summary
# ===================================================================

@router.get("/activity", response_model=ActivitySummaryModel)
async def get_activity(
    entityType: str = Query(...),
    entityKey: str = Query(...),
):
    summary = _reg().get_activity_summary(entityType, entityKey)
    return ActivitySummaryModel(**summary)
