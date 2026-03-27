"""
Pydantic models for Application API.

Provides request/response models for the application endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ApplicationModel(BaseModel):
    """Application representation for API responses."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "murex",
                "display_name": "Murex",
                "description": "Cross-asset trading and risk management platform",
                "category": "Trading",
                "color": "#8E44AD",
                "status": "active",
                "owner": "trading-tech@firm.com",
                "tech_lead": "murex-support@firm.com",
                "support_channel": "#murex-support",
                "datasets": ["prices.*/*", "risk.cvar/*/*"],
                "fields": ["risk.analytics/dv01", "risk.analytics/var"],
                "documentation_url": "https://confluence.firm.com/display/TECH/Murex",
                "wiki_link": "",
            }
        }
    )

    key: str = Field(..., description="Application identifier")
    display_name: str = Field("", description="Human-readable name for UI display")
    description: str = Field("", description="Application description")
    category: str = Field("", description="Application category (e.g., Trading, Risk Management)")
    color: str = Field("#6B7280", description="Hex color code for UI display")
    status: str = Field("active", description="Lifecycle status: active, planned, decommissioned")
    owner: str = Field("", description="Business owner")
    tech_lead: str = Field("", description="Technical lead")
    support_channel: str = Field("", description="Support channel (Teams/Slack)")
    datasets: List[str] = Field(default_factory=list, description="Dataset glob patterns")
    fields: List[str] = Field(default_factory=list, description="Field/model paths")
    documentation_url: str = Field("", description="Link to documentation")
    wiki_link: str = Field("", description="Link to wiki page")


class CreateApplicationRequest(BaseModel):
    """Request model for creating a new application."""

    key: str = Field(..., description="Application identifier (must be unique)")
    display_name: str = Field("", description="Human-readable display name")
    description: str = Field("", description="Application description")
    category: str = Field("", description="Application category")
    color: str = Field("#6B7280", description="Hex color code")
    status: str = Field("active", description="Lifecycle status")
    owner: str = Field("", description="Business owner")
    tech_lead: str = Field("", description="Technical lead")
    support_channel: str = Field("", description="Support channel")
    datasets: List[str] = Field(default_factory=list, description="Dataset glob patterns")
    fields: List[str] = Field(default_factory=list, description="Field/model paths")
    documentation_url: str = Field("", description="Documentation link")
    wiki_link: str = Field("", description="Wiki link")


class UpdateApplicationRequest(BaseModel):
    """Request model for updating an application (all fields optional)."""

    display_name: Optional[str] = Field(None, description="Human-readable display name")
    description: Optional[str] = Field(None, description="Application description")
    category: Optional[str] = Field(None, description="Application category")
    color: Optional[str] = Field(None, description="Hex color code")
    status: Optional[str] = Field(None, description="Lifecycle status")
    owner: Optional[str] = Field(None, description="Business owner")
    tech_lead: Optional[str] = Field(None, description="Technical lead")
    support_channel: Optional[str] = Field(None, description="Support channel")
    datasets: Optional[List[str]] = Field(None, description="Dataset glob patterns")
    fields: Optional[List[str]] = Field(None, description="Field/model paths")
    documentation_url: Optional[str] = Field(None, description="Documentation link")
    wiki_link: Optional[str] = Field(None, description="Wiki link")


class ApplicationListResponse(BaseModel):
    """Response model for listing all applications."""

    applications: List[ApplicationModel] = Field(..., description="List of all applications")
    count: int = Field(..., description="Total number of applications")


class ApplicationDetailResponse(BaseModel):
    """Response model for an application with resolved dataset/field info."""

    application: ApplicationModel = Field(..., description="Application details")
    dataset_count: int = Field(0, description="Number of dataset patterns")
    field_count: int = Field(0, description="Number of field references")


class ApplicationsForDatasetResponse(BaseModel):
    """Response model for applications that reference a dataset."""

    dataset_path: str = Field(..., description="The queried dataset path")
    applications: List[ApplicationModel] = Field(..., description="Applications matching this dataset")
    count: int = Field(..., description="Number of matching applications")


class ApplicationsForFieldResponse(BaseModel):
    """Response model for applications that reference a field."""

    field_path: str = Field(..., description="The queried field path")
    applications: List[ApplicationModel] = Field(..., description="Applications matching this field")
    count: int = Field(..., description="Number of matching applications")


class SaveResponse(BaseModel):
    """Response model for save operations."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    file_path: Optional[str] = Field(None, description="Path to saved file")


class ReloadResponse(BaseModel):
    """Response model for reload operations."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message")
    applications_loaded: int = Field(0, description="Number of applications loaded")
