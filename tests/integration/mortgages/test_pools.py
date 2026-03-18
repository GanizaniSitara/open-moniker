"""Integration tests for mortgages.pools domain.

Tests resolution for MBS pool data.
"""

import pytest


@pytest.mark.mortgages
@pytest.mark.integration
class TestMbsResolution:
    """Test MBS moniker resolution."""

    @pytest.mark.asyncio
    async def test_resolve_pools(self, service, caller):
        """MBS pool moniker should resolve to Excel source."""
        result = await service.resolve(
            "moniker://mortgages.pools/FNMA/30Y/ALL",
            caller
        )

        assert result.source.source_type == "excel"
        assert result.binding_path == "mortgages.pools"

    @pytest.mark.asyncio
    async def test_resolve_prepay(self, service, caller):
        """Prepayment moniker should resolve."""
        result = await service.resolve(
            "moniker://mortgages.prepay/FNMA/30Y/ALL",
            caller
        )

        assert result.source.source_type == "excel"

    @pytest.mark.asyncio
    async def test_confidential_classification(self, service, caller):
        """MBS data should be classified as confidential."""
        result = await service.describe(
            "moniker://mortgages",
            caller
        )

        assert result.node.classification == "confidential"


@pytest.mark.mortgages
@pytest.mark.integration
class TestMbsGovernance:
    """Test MBS governance roles."""

    @pytest.mark.asyncio
    async def test_governance_roles_set(self, service, caller, catalog_registry):
        """MBS should have formal governance roles at domain level."""
        result = await service.resolve(
            "moniker://mortgages.pools/FNMA/30Y/ALL",
            caller
        )

        # Resolution returns source binding info
        assert result.source.source_type == "excel"

        # Governance roles are defined at parent level (mortgages)
        mortgages_node = catalog_registry.get("mortgages")
        assert mortgages_node is not None
        assert mortgages_node.ownership.adop is not None
        assert mortgages_node.ownership.ads is not None
        assert mortgages_node.ownership.adal is not None

    def test_documentation_available(self, catalog_registry):
        """MBS domain should have documentation links."""
        node = catalog_registry.get("mortgages")
        assert node is not None
        assert node.documentation is not None
        assert node.documentation.glossary_url is not None
        assert node.documentation.runbook_url is not None
