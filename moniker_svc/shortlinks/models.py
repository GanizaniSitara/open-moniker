"""Pydantic request/response models for shortlink CRUD API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateShortlinkRequest(BaseModel):
    base_path: str = Field(..., description="Base moniker path (e.g. 'fixed.income/govies/sovereign')")
    filter_segments: list[str] = Field(default_factory=list, description="Filter segments after base path")
    params: dict[str, str] = Field(default_factory=dict, description="Query parameters")
    label: str = Field("", description="Human-readable label")


class ShortlinkModel(BaseModel):
    id: str
    base_path: str
    filter_segments: list[str]
    params: dict[str, str] = {}
    label: str = ""
    created_by: str = ""
    created_at: str = ""
    resolve_path: str = ""  # e.g. "fixed.income/govies/sovereign/filter@xK9f2p"
    expanded_path: str = ""  # e.g. "fixed.income/govies/sovereign/US/10Y/SHORT_DATED?format=json"


class ShortlinkListResponse(BaseModel):
    shortlinks: list[ShortlinkModel]
    count: int


class DeleteResponse(BaseModel):
    success: bool
    message: str
