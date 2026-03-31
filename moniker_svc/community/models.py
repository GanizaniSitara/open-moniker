"""Pydantic request/response models for community API.

Uses camelCase aliases to match the existing frontend TypeScript types
in contributions-types.ts — zero frontend changes required.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CreateFlagRequest(BaseModel):
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    flag_type: str = Field(alias="flagType")
    comment: str | None = None
    author: str
    model_config = ConfigDict(populate_by_name=True)


class UpdateFlagStatusRequest(BaseModel):
    status: str
    resolved_by: str | None = Field(default=None, alias="resolvedBy")
    model_config = ConfigDict(populate_by_name=True)


class CreateSuggestionRequest(BaseModel):
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    field_name: str = Field(alias="fieldName")
    proposed_value: str = Field(alias="proposedValue")
    author: str
    current_value: str | None = Field(default=None, alias="currentValue")
    reason: str | None = None
    model_config = ConfigDict(populate_by_name=True)


class ReviewSuggestionRequest(BaseModel):
    reviewed_by: str | None = Field(default=None, alias="reviewedBy")
    review_comment: str | None = Field(default=None, alias="reviewComment")
    model_config = ConfigDict(populate_by_name=True)


class CreateAnnotationRequest(BaseModel):
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    annotation_type: str = Field(alias="annotationType")
    content: str
    author: str
    model_config = ConfigDict(populate_by_name=True)


class UpvoteRequest(BaseModel):
    voter: str


class CreateDiscussionRequest(BaseModel):
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    title: str
    author: str
    model_config = ConfigDict(populate_by_name=True)


class CreateReplyRequest(BaseModel):
    content: str
    author: str
    parent_reply_id: str | None = Field(default=None, alias="parentReplyId")
    model_config = ConfigDict(populate_by_name=True)


class HelpfulVoteRequest(BaseModel):
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    helpful: bool
    comment: str | None = None
    author: str | None = None
    model_config = ConfigDict(populate_by_name=True)


class SaveConfigRequest(BaseModel):
    title: str
    description: str = ""


# ---------------------------------------------------------------------------
# Response models (camelCase via by_alias=True)
# ---------------------------------------------------------------------------

class FlagModel(BaseModel):
    id: str
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    flag_type: str = Field(alias="flagType")
    comment: str | None = None
    author: str
    status: str = "open"
    resolved_by: str | None = Field(default=None, alias="resolvedBy")
    resolved_at: str | None = Field(default=None, alias="resolvedAt")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class FlagSummaryModel(BaseModel):
    total: int
    by_type: dict[str, int] = Field(alias="byType")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class SuggestionModel(BaseModel):
    id: str
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    field_name: str = Field(alias="fieldName")
    current_value: str | None = Field(default=None, alias="currentValue")
    proposed_value: str = Field(alias="proposedValue")
    reason: str | None = None
    author: str
    status: str = "pending"
    reviewed_by: str | None = Field(default=None, alias="reviewedBy")
    review_comment: str | None = Field(default=None, alias="reviewComment")
    reviewed_at: str | None = Field(default=None, alias="reviewedAt")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class VoteModel(BaseModel):
    voter: str
    created_at: str = Field(alias="createdAt")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class AnnotationModel(BaseModel):
    id: str
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    annotation_type: str = Field(alias="annotationType")
    content: str
    author: str
    upvote_count: int = Field(alias="upvoteCount")
    votes: list[VoteModel] = []
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class ReplyModel(BaseModel):
    id: str
    parent_reply_id: str | None = Field(default=None, alias="parentReplyId")
    content: str
    author: str
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class DiscussionModel(BaseModel):
    id: str
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    title: str
    author: str
    reply_count: int = Field(alias="replyCount")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class DiscussionDetailModel(BaseModel):
    id: str
    entity_type: str = Field(alias="entityType")
    entity_key: str = Field(alias="entityKey")
    title: str
    author: str
    replies: list[ReplyModel] = []
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class HelpfulSummaryModel(BaseModel):
    helpful: int
    not_helpful: int = Field(alias="notHelpful")
    total: int
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class ActivitySummaryModel(BaseModel):
    flags: int
    suggestions: int
    annotations: int
    discussions: int
    total: int


class ConfigSnapshotModel(BaseModel):
    id: str
    title: str
    description: str = ""
    author: str
    status: str = "draft"
    forked_from: str | None = Field(default=None, alias="forkedFrom")
    moniker_count: int = Field(alias="monikerCount")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    published_at: str | None = Field(default=None, alias="publishedAt")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)
