"""Integration tests for fixed.income/govies/treasury domain.

Tests resolution for US Treasury securities.
"""

import pytest


@pytest.mark.govies
@pytest.mark.integration
class TestTreasuryResolution:
    """Test Treasury moniker resolution."""

    @pytest.mark.asyncio
    async def test_resolve_treasury(self, service, caller):
        """Treasury moniker should resolve to Snowflake source."""
        result = await service.resolve(
            "moniker://fixed.income/govies/treasury/US/10Y/ALL",
            caller
        )

        assert result.source.source_type == "snowflake"
        assert result.binding_path == "fixed.income/govies/treasury"

    @pytest.mark.asyncio
    async def test_ownership_and_governance(self, service, caller, catalog_registry):
        """Govies should have proper governance roles at domain level."""
        result = await service.resolve(
            "moniker://fixed.income/govies/treasury/US/10Y/ALL",
            caller
        )

        # Resolution returns source binding info
        assert result.source.source_type == "snowflake"

        # Governance roles are defined at parent level (govies)
        govies_node = catalog_registry.get("govies")
        assert govies_node is not None
        assert govies_node.ownership.adop is not None
        assert govies_node.ownership.ads is not None
        assert govies_node.ownership.adal is not None
