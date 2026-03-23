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
            "moniker://fixed.income/mbs/pools/FNMA/30Y/ALL",
            caller
        )

        assert result.source.source_type == "excel"
        assert result.binding_path == "fixed.income/mbs/pools"

    @pytest.mark.asyncio
    async def test_resolve_prepay(self, service, caller):
        """Prepayment moniker should resolve."""
        result = await service.resolve(
            "moniker://fixed.income/mbs/prepay/FNMA/30Y/ALL",
            caller
        )

        assert result.source.source_type == "excel"

    @pytest.mark.asyncio
    async def test_confidential_classification(self, service, caller, catalog_registry):
        """MBS data should be classified as confidential."""
        node = catalog_registry.get("fixed.income/mbs")
        assert node is not None
        assert node.classification == "confidential"


@pytest.mark.mortgages
@pytest.mark.integration
class TestMbsGovernance:
    """Test MBS governance roles."""

    @pytest.mark.asyncio
    async def test_governance_roles_set(self, service, caller, catalog_registry):
        """Fixed income should have formal governance roles at domain level."""
        result = await service.resolve(
            "moniker://fixed.income/mbs/pools/FNMA/30Y/ALL",
            caller
        )

        # Resolution returns source binding info
        assert result.source.source_type == "excel"

        # Governance roles are defined at parent level (fixed.income)
        fi_node = catalog_registry.get("fixed.income")
        assert fi_node is not None
        assert fi_node.ownership.adop is not None
        assert fi_node.ownership.ads is not None

    def test_documentation_available(self, catalog_registry):
        """Fixed income domain should have documentation links."""
        node = catalog_registry.get("fixed.income")
        assert node is not None
        assert node.documentation is not None
        assert node.documentation.glossary_url is not None
        assert node.documentation.data_dictionary_url is not None
