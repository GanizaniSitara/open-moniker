"""Integration tests for domain mapping (OM-6).

Tests the domain mapping feature where catalog nodes can be associated
with governance domains via the 'domain' field. The domain dropdown in
the config UI allows mapping catalog paths to domains.

Key behaviors tested:
1. Catalog nodes can have a domain field set
2. Domain mapping is independent of path hierarchy
3. Domain info is correctly retrieved and displayed
4. Domain validation works (only existing domains can be mapped)
"""

import pytest
from moniker_svc.catalog.registry import CatalogRegistry
from moniker_svc.catalog.types import CatalogNode, Ownership, SourceBinding, SourceType
from moniker_svc.domains.registry import DomainRegistry
from moniker_svc.domains.types import Domain


@pytest.fixture
def domain_registry() -> DomainRegistry:
    """Create a domain registry with test domains."""
    registry = DomainRegistry()

    # Create test domains with different categories
    registry.register(Domain(
        name="risk",
        id=1,
        display_name="Risk Analytics",
        short_code="RSK",
        data_category="Analytics",
        color="#D0002B",
        owner="risk-governance@firm.com",
        tech_custodian="risk-tech@firm.com",
        business_steward="risk-steward@firm.com",
        confidentiality="confidential",
        pii=False,
        help_channel="#risk-data",
        wiki_link="https://wiki.firm.com/risk",
    ))

    registry.register(Domain(
        name="indices",
        id=2,
        display_name="Market Indices",
        short_code="IDX",
        data_category="Market Data",
        color="#005587",
        owner="market-data@firm.com",
        tech_custodian="market-tech@firm.com",
        business_steward="market-steward@firm.com",
        confidentiality="internal",
        pii=False,
        help_channel="#market-data",
        wiki_link="https://wiki.firm.com/indices",
    ))

    registry.register(Domain(
        name="reference",
        id=3,
        display_name="Reference Data",
        short_code="REF",
        data_category="Reference Data",
        color="#789D4A",
        owner="ref-data@firm.com",
        tech_custodian="ref-tech@firm.com",
        business_steward="ref-steward@firm.com",
        confidentiality="internal",
        pii=False,
        help_channel="#ref-data",
        wiki_link="https://wiki.firm.com/reference",
    ))

    return registry


@pytest.fixture
def catalog_with_domains() -> CatalogRegistry:
    """Create a catalog with domain mappings."""
    registry = CatalogRegistry()

    # Top-level node with domain mapping
    registry.register(CatalogNode(
        path="risk.cvar",
        display_name="CVaR Risk Measures",
        description="Daily CVaR calculations",
        domain="risk",  # Mapped to risk domain
        ownership=Ownership(
            accountable_owner="cvar-owner@firm.com",
        ),
        source_binding=SourceBinding(
            source_type=SourceType.ORACLE,
            config={"query": "SELECT * FROM risk_cvar"},
        ),
    ))

    # Child node inherits domain from path structure
    registry.register(CatalogNode(
        path="risk.cvar/portfolio",
        display_name="Portfolio CVaR",
        description="Portfolio-level CVaR",
        # No explicit domain - should use parent's
    ))

    # Node with different domain than its path suggests
    registry.register(CatalogNode(
        path="analytics.custom",
        display_name="Custom Analytics",
        description="Custom analytics that belongs to indices domain",
        domain="indices",  # Cross-domain mapping
        ownership=Ownership(
            data_specialist="analytics-team@firm.com",
        ),
    ))

    # Node without domain mapping
    registry.register(CatalogNode(
        path="legacy.data",
        display_name="Legacy Data",
        description="Legacy data without domain governance",
        # No domain - should have no domain fallback
    ))

    return registry


@pytest.mark.integration
class TestDomainMapping:
    """Test domain mapping for catalog nodes."""

    def test_node_has_domain_field(self, catalog_with_domains):
        """Catalog nodes should have a domain field."""
        node = catalog_with_domains.get("risk.cvar")

        assert node is not None
        assert node.domain == "risk"

    def test_domain_mapping_independent_of_path(self, catalog_with_domains):
        """Domain mapping should be independent of path hierarchy."""
        # analytics.custom is mapped to indices, not analytics
        node = catalog_with_domains.get("analytics.custom")

        assert node is not None
        assert node.domain == "indices"

    def test_node_without_domain_mapping(self, catalog_with_domains):
        """Nodes without domain mapping should have None domain."""
        node = catalog_with_domains.get("legacy.data")

        assert node is not None
        assert node.domain is None

    def test_child_node_no_domain_inheritance(self, catalog_with_domains):
        """Child nodes don't automatically inherit parent's domain field."""
        # Domain field is not inherited - only ownership is inherited
        child = catalog_with_domains.get("risk.cvar/portfolio")

        assert child is not None
        assert child.domain is None  # Domain field not inherited


@pytest.mark.integration
class TestDomainRegistry:
    """Test domain registry operations."""

    def test_get_domain(self, domain_registry):
        """Should retrieve domain by name."""
        domain = domain_registry.get("risk")

        assert domain is not None
        assert domain.name == "risk"
        assert domain.display_name == "Risk Analytics"
        assert domain.short_code == "RSK"

    def test_get_nonexistent_domain(self, domain_registry):
        """Should return None for nonexistent domain."""
        domain = domain_registry.get("nonexistent")

        assert domain is None

    def test_domain_exists(self, domain_registry):
        """Should check domain existence."""
        assert domain_registry.exists("risk") is True
        assert domain_registry.exists("nonexistent") is False

    def test_all_domains(self, domain_registry):
        """Should return all domains sorted by name."""
        domains = domain_registry.all_domains()

        assert len(domains) == 3
        assert domains[0].name == "indices"
        assert domains[1].name == "reference"
        assert domains[2].name == "risk"

    def test_domain_names(self, domain_registry):
        """Should return sorted list of domain names."""
        names = domain_registry.domain_names()

        assert names == ["indices", "reference", "risk"]

    def test_get_domain_for_path(self, domain_registry):
        """Should extract domain from path and look it up."""
        # Path starting with 'risk' should find risk domain
        domain = domain_registry.get_domain_for_path("risk/portfolio/123")

        assert domain is not None
        assert domain.name == "risk"

    def test_get_domain_for_path_no_match(self, domain_registry):
        """Should return None if path's first segment isn't a domain."""
        domain = domain_registry.get_domain_for_path("unknown/path/here")

        assert domain is None

    def test_get_domain_for_empty_path(self, domain_registry):
        """Should handle empty path gracefully."""
        domain = domain_registry.get_domain_for_path("")

        assert domain is None


@pytest.mark.integration
class TestDomainProperties:
    """Test domain property access and governance metadata."""

    def test_domain_governance_fields(self, domain_registry):
        """Domain should have all governance fields."""
        domain = domain_registry.get("risk")

        assert domain.owner == "risk-governance@firm.com"
        assert domain.tech_custodian == "risk-tech@firm.com"
        assert domain.business_steward == "risk-steward@firm.com"
        assert domain.confidentiality == "confidential"
        assert domain.pii is False
        assert domain.help_channel == "#risk-data"
        assert domain.wiki_link == "https://wiki.firm.com/risk"

    def test_domain_display_properties(self, domain_registry):
        """Domain should have display properties."""
        domain = domain_registry.get("indices")

        assert domain.display_name == "Market Indices"
        assert domain.short_code == "IDX"
        assert domain.data_category == "Market Data"
        assert domain.color == "#005587"

    def test_domain_to_dict(self, domain_registry):
        """Domain should serialize to dictionary."""
        domain = domain_registry.get("reference")
        domain_dict = domain.to_dict()

        assert domain_dict["name"] == "reference"
        assert domain_dict["display_name"] == "Reference Data"
        assert domain_dict["short_code"] == "REF"
        assert domain_dict["owner"] == "ref-data@firm.com"


@pytest.mark.integration
class TestDomainRegistryCRUD:
    """Test domain registry CRUD operations."""

    def test_register_new_domain(self):
        """Should register a new domain."""
        registry = DomainRegistry()

        domain = Domain(name="new_domain", display_name="New Domain")
        registry.register(domain)

        assert registry.exists("new_domain")
        assert registry.get("new_domain").display_name == "New Domain"

    def test_register_duplicate_raises(self):
        """Should raise when registering duplicate domain."""
        registry = DomainRegistry()

        domain = Domain(name="test", display_name="Test")
        registry.register(domain)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(domain)

    def test_register_or_update(self):
        """Should update existing domain with register_or_update."""
        registry = DomainRegistry()

        # Register initial
        domain1 = Domain(name="test", display_name="Original")
        registry.register(domain1)

        # Update via register_or_update
        domain2 = Domain(name="test", display_name="Updated")
        registry.register_or_update(domain2)

        assert registry.get("test").display_name == "Updated"

    def test_delete_domain(self):
        """Should delete a domain."""
        registry = DomainRegistry()

        domain = Domain(name="to_delete", display_name="Delete Me")
        registry.register(domain)

        assert registry.exists("to_delete")

        result = registry.delete("to_delete")

        assert result is True
        assert registry.exists("to_delete") is False

    def test_delete_nonexistent_returns_false(self):
        """Should return False when deleting nonexistent domain."""
        registry = DomainRegistry()

        result = registry.delete("nonexistent")

        assert result is False

    def test_clear_domains(self):
        """Should clear all domains."""
        registry = DomainRegistry()

        registry.register(Domain(name="a", display_name="A"))
        registry.register(Domain(name="b", display_name="B"))

        assert registry.count() == 2

        registry.clear()

        assert registry.count() == 0

    def test_domain_count(self, domain_registry):
        """Should return correct count."""
        assert domain_registry.count() == 3
        assert len(domain_registry) == 3

    def test_domain_contains(self, domain_registry):
        """Should support 'in' operator."""
        assert "risk" in domain_registry
        assert "nonexistent" not in domain_registry

    def test_domain_iteration(self, domain_registry):
        """Should support iteration."""
        names = [d.name for d in domain_registry]

        assert "risk" in names
        assert "indices" in names
        assert "reference" in names


@pytest.mark.integration
class TestResolveDomain:
    """Test resolve_domain (ancestor walk) and resolve_domain_with_fallback."""

    @pytest.fixture
    def catalog_with_hierarchy(self, domain_registry):
        """Build a catalog with nested nodes and domain overrides at various depths."""
        reg = CatalogRegistry()

        # Top-level: 'portfolios' with domain 'risk'
        reg.register(CatalogNode(
            path="portfolios",
            display_name="Portfolios",
            domain="risk",
        ))
        # Child: inherits domain from parent
        reg.register(CatalogNode(
            path="portfolios/exposures",
            display_name="Exposures",
        ))
        # Grandchild: overrides domain
        reg.register(CatalogNode(
            path="portfolios/exposures/fx",
            display_name="FX Exposure",
            domain="reference",
        ))
        # Great-grandchild: should inherit the override
        reg.register(CatalogNode(
            path="portfolios/exposures/fx/spot",
            display_name="FX Spot Exposure",
        ))
        # Node with no domain ancestry at all
        reg.register(CatalogNode(
            path="unowned",
            display_name="Unowned",
        ))
        # Leaf under unowned
        reg.register(CatalogNode(
            path="unowned/data",
            display_name="Unowned Data",
        ))

        return reg

    def test_resolve_domain_explicit(self, catalog_with_hierarchy):
        """Node with explicit domain should resolve to it."""
        assert catalog_with_hierarchy.resolve_domain("portfolios") == "risk"

    def test_resolve_domain_inherited_from_parent(self, catalog_with_hierarchy):
        """Child inherits domain from parent."""
        assert catalog_with_hierarchy.resolve_domain("portfolios/exposures") == "risk"

    def test_resolve_domain_override_at_depth(self, catalog_with_hierarchy):
        """Child can override parent's domain."""
        assert catalog_with_hierarchy.resolve_domain("portfolios/exposures/fx") == "reference"

    def test_resolve_domain_inherited_override(self, catalog_with_hierarchy):
        """Grandchild inherits the overridden domain, not the root domain."""
        assert catalog_with_hierarchy.resolve_domain("portfolios/exposures/fx/spot") == "reference"

    def test_resolve_domain_no_domain_in_chain(self, catalog_with_hierarchy):
        """Node with no domain in its ancestry returns None."""
        assert catalog_with_hierarchy.resolve_domain("unowned") is None
        assert catalog_with_hierarchy.resolve_domain("unowned/data") is None

    def test_resolve_domain_unknown_path(self, catalog_with_hierarchy):
        """Unknown path returns None."""
        assert catalog_with_hierarchy.resolve_domain("nonexistent/path") is None

    def test_resolve_domain_with_fallback_uses_hierarchy_first(
        self, catalog_with_hierarchy, domain_registry
    ):
        """Fallback method should prefer hierarchy resolution."""
        result = catalog_with_hierarchy.resolve_domain_with_fallback(
            "portfolios/exposures", domain_registry
        )
        assert result == "risk"

    def test_resolve_domain_with_fallback_uses_registry(
        self, catalog_with_hierarchy, domain_registry
    ):
        """When hierarchy returns None, fall back to domain registry first-segment lookup."""
        # 'risk' is a registered domain, so 'risk/some_child' should resolve via registry
        reg = CatalogRegistry()
        reg.register(CatalogNode(path="risk/some_child", display_name="Child"))
        result = reg.resolve_domain_with_fallback("risk/some_child", domain_registry)
        assert result == "risk"

    def test_resolve_domain_with_fallback_no_match(
        self, catalog_with_hierarchy, domain_registry
    ):
        """Returns None when neither hierarchy nor registry matches."""
        result = catalog_with_hierarchy.resolve_domain_with_fallback(
            "unowned/data", domain_registry
        )
        assert result is None

    def test_resolve_domain_with_fallback_no_registry(self, catalog_with_hierarchy):
        """Without a registry, only hierarchy resolution is used."""
        assert catalog_with_hierarchy.resolve_domain_with_fallback("portfolios/exposures") == "risk"
        assert catalog_with_hierarchy.resolve_domain_with_fallback("unowned/data") is None
