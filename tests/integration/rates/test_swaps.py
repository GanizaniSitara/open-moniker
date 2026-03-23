"""Integration tests for rates.swap domain.

Tests resolution for interest rate swaps.
"""

import pytest


@pytest.mark.rates
@pytest.mark.integration
class TestSwapResolution:
    """Test swap rate moniker resolution."""

    @pytest.mark.asyncio
    async def test_resolve_swap_rates(self, service, caller):
        """Swap moniker should resolve to Snowflake source."""
        result = await service.resolve(
            "moniker://rates.swap/USD/10Y/ALL",
            caller
        )

        assert result.source.source_type == "snowflake"
        assert result.binding_path == "rates.swap"

    @pytest.mark.asyncio
    async def test_resolve_all_currencies(self, service, caller):
        """Should support ALL currencies query."""
        result = await service.resolve(
            "moniker://rates.swap/ALL/5Y/ALL",
            caller
        )

        assert result.source.source_type == "snowflake"
        # filter[N] template replaces ALL with 1=1 (no-op filter)
        assert "1=1" in result.source.query or "'ALL' = 'ALL'" in result.source.query or "ALL" in result.source.query


@pytest.mark.rates
@pytest.mark.integration
class TestSofrResolution:
    """Test SOFR rate resolution."""

    @pytest.mark.asyncio
    async def test_resolve_sofr(self, service, caller):
        """SOFR moniker should resolve."""
        result = await service.resolve(
            "moniker://rates.sofr/USD/ON/ALL",
            caller
        )

        assert result.source.source_type == "snowflake"
