"""Integration tests for commodities.energy domain.

Tests resolution for energy commodities.
"""

import pytest


@pytest.mark.integration
class TestEnergyResolution:
    """Test energy commodity moniker resolution."""

    @pytest.mark.asyncio
    async def test_resolve_crude(self, service, caller):
        """Crude oil moniker should resolve to REST source."""
        result = await service.resolve(
            "moniker://commodities.energy/CL/SPOT/ALL",
            caller
        )

        assert result.source.source_type == "rest"
        assert result.binding_path == "commodities.energy"

    @pytest.mark.asyncio
    async def test_resolve_natgas(self, service, caller):
        """Natural gas moniker should resolve."""
        result = await service.resolve(
            "moniker://commodities.energy/NG/F1/ALL",
            caller
        )

        assert result.source.source_type == "rest"
