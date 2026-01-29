"""Catalog types - ownership, source bindings, and catalog nodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    """Supported data source types."""
    SNOWFLAKE = "snowflake"
    ORACLE = "oracle"
    REST = "rest"
    STATIC = "static"
    EXCEL = "excel"
    BLOOMBERG = "bloomberg"
    REFINITIV = "refinitiv"
    OPENSEARCH = "opensearch"  # OpenSearch/Elasticsearch
    # Synthetic/computed sources
    COMPOSITE = "composite"  # Combines multiple sources
    DERIVED = "derived"      # Computed from other monikers


@dataclass(frozen=True, slots=True)
class Ownership:
    """
    Ownership triple for a catalog node.

    This can be partially defined - each field inherits independently
    from ancestors if not set.
    """
    accountable_owner: str | None = None  # Executive accountable for the data
    data_specialist: str | None = None    # Technical SME / data expert
    support_channel: str | None = None    # Slack/Teams channel for help

    def merge_with_parent(self, parent: Ownership) -> Ownership:
        """
        Merge this ownership with a parent, using parent values for any
        fields not set on this instance.
        """
        return Ownership(
            accountable_owner=self.accountable_owner or parent.accountable_owner,
            data_specialist=self.data_specialist or parent.data_specialist,
            support_channel=self.support_channel or parent.support_channel,
        )

    def is_complete(self) -> bool:
        """Check if all ownership fields are defined."""
        return all([
            self.accountable_owner,
            self.data_specialist,
            self.support_channel,
        ])

    def is_empty(self) -> bool:
        """Check if no ownership fields are defined."""
        return not any([
            self.accountable_owner,
            self.data_specialist,
            self.support_channel,
        ])


@dataclass(frozen=True, slots=True)
class SourceBinding:
    """
    Binding to an actual data source.

    The config dictionary contains source-specific connection details.
    """
    source_type: SourceType
    config: dict[str, Any] = field(default_factory=dict)

    # Optional: restrict what operations are allowed
    # If None, all operations are allowed
    allowed_operations: frozenset[str] | None = None

    # Optional: schema definition for the data
    schema: dict[str, Any] | None = None

    # Is this source read-only?
    read_only: bool = True


@dataclass(slots=True)
class CatalogNode:
    """
    A node in the catalog hierarchy.

    Each node represents a data asset or category of assets.
    Nodes can have:
    - Ownership (inheritable triple)
    - Source binding (how to fetch data)
    - Data quality info
    - SLA info
    - Freshness info
    - Children (sub-paths)
    - Metadata
    """
    path: str  # Full path string (e.g., "market-data/prices/equity")
    display_name: str = ""
    description: str = ""

    # Ownership (inherits from ancestors if not set)
    ownership: Ownership = field(default_factory=Ownership)

    # Source binding (only leaf nodes typically have this)
    source_binding: SourceBinding | None = None

    # Data governance
    data_quality: DataQuality | None = None
    sla: SLA | None = None
    freshness: Freshness | None = None

    # Data classification (for governance)
    classification: str = "internal"

    # Arbitrary tags for searchability
    tags: frozenset[str] = field(default_factory=frozenset)

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Is this a leaf node (actual data) or category (contains children)?
    is_leaf: bool = False

    def __post_init__(self):
        if not self.display_name:
            # Default display name from last path segment
            segments = self.path.split("/")
            self.display_name = segments[-1] if segments else ""


@dataclass(frozen=True, slots=True)
class ResolvedOwnership:
    """
    Ownership resolved through the hierarchy, with provenance.

    Shows the effective ownership and where each field came from.
    """
    accountable_owner: str | None = None
    accountable_owner_source: str | None = None  # Path where this was defined

    data_specialist: str | None = None
    data_specialist_source: str | None = None

    support_channel: str | None = None
    support_channel_source: str | None = None

    @property
    def ownership(self) -> Ownership:
        """Get as simple Ownership (without provenance)."""
        return Ownership(
            accountable_owner=self.accountable_owner,
            data_specialist=self.data_specialist,
            support_channel=self.support_channel,
        )


@dataclass(frozen=True, slots=True)
class DataQuality:
    """Data quality information for a catalog node."""
    # DQ owner/steward responsible for data quality
    dq_owner: str | None = None

    # Quality score (0-100) if measured
    quality_score: float | None = None

    # Validation rules applied
    validation_rules: tuple[str, ...] = ()

    # Known issues or caveats
    known_issues: tuple[str, ...] = ()

    # Last DQ check timestamp (ISO format)
    last_validated: str | None = None


@dataclass(frozen=True, slots=True)
class SLA:
    """Service level agreement for a data source."""
    # Expected freshness (e.g., "T+1", "15min", "real-time")
    freshness: str | None = None

    # Availability target (e.g., "99.9%")
    availability: str | None = None

    # Support hours (e.g., "24/7", "business hours ET")
    support_hours: str | None = None

    # Escalation contact for SLA breaches
    escalation_contact: str | None = None


@dataclass(frozen=True, slots=True)
class Freshness:
    """Data freshness information."""
    # When the data was last loaded/refreshed (ISO format)
    last_loaded: str | None = None

    # Scheduled refresh time (e.g., "06:00 ET daily")
    refresh_schedule: str | None = None

    # Source system the data comes from
    source_system: str | None = None

    # Upstream dependencies
    upstream_dependencies: tuple[str, ...] = ()
