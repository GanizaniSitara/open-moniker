"""
Application data model.

An Application represents a business application that consumes or produces
datasets and fields in the moniker catalog.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass(frozen=True)
class Application:
    """
    A business application that interacts with catalog datasets and fields.

    Applications track which systems consume or produce data, with metadata
    about ownership, status, and support contacts.
    """

    # Required: application identifier (YAML key)
    key: str

    # Display and identification
    display_name: str = ""
    description: str = ""
    category: str = ""
    color: str = "#6B7280"

    # Lifecycle
    status: str = "active"  # active, planned, decommissioned

    # Ownership and contact
    owner: str = ""
    tech_lead: str = ""
    support_channel: str = ""

    # Data linkage (glob patterns for datasets, model paths for fields)
    datasets: List[str] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)

    # Documentation
    documentation_url: str = ""
    wiki_link: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, key: str, data: dict) -> "Application":
        """
        Create an Application from a dictionary.

        Args:
            key: The application identifier (YAML key)
            data: Dictionary of application attributes

        Returns:
            Application instance
        """
        return cls(
            key=key,
            display_name=data.get("display_name") or key,
            description=data.get("description", ""),
            category=data.get("category", ""),
            color=data.get("color", "#6B7280"),
            status=data.get("status", "active"),
            owner=data.get("owner", ""),
            tech_lead=data.get("tech_lead", ""),
            support_channel=data.get("support_channel", ""),
            datasets=data.get("datasets") or [],
            fields=data.get("fields") or [],
            documentation_url=data.get("documentation_url", ""),
            wiki_link=data.get("wiki_link", ""),
        )


# Valid status values
APPLICATION_STATUSES = ["active", "planned", "decommissioned"]
