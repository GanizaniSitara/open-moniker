"""Integration tests for risk.cvar domain.

Tests the full resolution flow.
These tests validate CONTRACT behavior, not implementation details.
"""

import pytest
from moniker_svc.service import AccessDeniedError


@pytest.mark.risk
@pytest.mark.integration
class TestCvarResolution:
    """Test CVaR moniker resolution."""

    @pytest.mark.asyncio
    async def test_resolve_specific_security(self, service, caller):
        """Fully specified path should resolve to Oracle source."""
        result = await service.resolve(
            "moniker://risk.cvar/758-A/USD/B0YHY8V7",
            caller
        )

        # Validate contract
        assert result.source.source_type == "oracle"
        assert result.binding_path == "risk.cvar"
        assert result.sub_path == "758-A/USD/B0YHY8V7"

        # Query should contain filters
        assert "758-A" in result.source.query
        assert "USD" in result.source.query
        assert "B0YHY8V7" in result.source.query

    @pytest.mark.asyncio
    async def test_resolve_all_currencies(self, service, caller):
        """ALL on currency dimension should generate wildcard query."""
        result = await service.resolve(
            "moniker://risk.cvar/758-A/ALL/B0YHY8V7",
            caller
        )

        assert result.source.source_type == "oracle"
        # Query should have ALL pattern for currency
        assert "'ALL' = 'ALL'" in result.source.query

    @pytest.mark.asyncio
    async def test_ownership_inheritance(self, service, caller):
        """Ownership should inherit from risk domain."""
        result = await service.resolve(
            "moniker://risk.cvar/758-A/USD/B0YHY8V7",
            caller
        )

        # Validate governance roles are inherited
        assert result.ownership.accountable_owner is not None
        assert result.ownership.data_specialist is not None
        assert result.ownership.support_channel is not None

        # ADOP should be set (from risk.cvar definition)
        assert result.ownership.adop is not None


@pytest.mark.risk
@pytest.mark.integration
class TestCvarAccessPolicy:
    """Test access policy enforcement for CVaR."""

    @pytest.mark.asyncio
    async def test_all_all_all_blocked(self, service, caller):
        """ALL/ALL/ALL should be blocked by access policy."""
        with pytest.raises(AccessDeniedError) as exc_info:
            await service.resolve(
                "moniker://risk.cvar/ALL/ALL/ALL",
                caller
            )

        # Validate error details
        assert exc_info.value.estimated_rows is not None
        assert exc_info.value.estimated_rows > 1_000_000_000

    @pytest.mark.asyncio
    async def test_large_query_blocked(self, service, caller):
        """Queries exceeding row limit should be blocked."""
        # Portfolio + currency specified, ALL securities = 200M rows
        with pytest.raises(AccessDeniedError) as exc_info:
            await service.resolve(
                "moniker://risk.cvar/758-A/USD/ALL",
                caller
            )

        error = exc_info.value
        assert error.estimated_rows == 200_000_000

    @pytest.mark.asyncio
    async def test_helpful_error_message(self, service, caller):
        """Access denied should include helpful guidance."""
        with pytest.raises(AccessDeniedError) as exc_info:
            await service.resolve(
                "moniker://risk.cvar/ALL/ALL/ALL",
                caller
            )

        error_msg = str(exc_info.value)
        # Should mention the scale of data
        assert "billion" in error_msg.lower() or "cvar" in error_msg.lower()
