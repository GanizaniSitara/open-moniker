"""Tests for governance: rate limiter + circuit breaker.

Run: C:/Anaconda3/envs/python312/python.exe -m pytest tests/test_governance.py -v
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from moniker_svc.governance.rate_limiter import (
    RateLimiter,
    RateLimiterConfig,
    RateLimitExceeded,
    _TokenBucket,
)
from moniker_svc.governance.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitState,
)


# ===================================================================
# TokenBucket (internal)
# ===================================================================

class TestTokenBucket:
    def test_consume_within_capacity(self):
        bucket = _TokenBucket(capacity=10, refill_rate=1.0, tokens=10)
        assert bucket.consume() is True
        assert bucket.consume(5) is True

    def test_consume_over_capacity(self):
        bucket = _TokenBucket(capacity=10, refill_rate=1.0, tokens=0)
        # Force last_refill to now so no refill occurs
        bucket.last_refill = time.monotonic()
        assert bucket.consume() is False

    def test_tokens_refill_over_time(self):
        bucket = _TokenBucket(capacity=10, refill_rate=100.0, tokens=0)
        bucket.last_refill = time.monotonic() - 0.1  # 0.1s ago → 10 tokens refilled
        assert bucket.consume(5) is True

    def test_tokens_capped_at_capacity(self):
        bucket = _TokenBucket(capacity=10, refill_rate=1000.0, tokens=0)
        bucket.last_refill = time.monotonic() - 100  # way in the past
        bucket.consume(0)  # trigger refill
        # Even after massive refill, tokens capped at capacity (10)
        assert bucket.consume(10) is True
        assert bucket.consume(1) is False

    def test_retry_after(self):
        bucket = _TokenBucket(capacity=10, refill_rate=10.0, tokens=0)
        bucket.last_refill = time.monotonic()
        assert bucket.retry_after > 0
        assert bucket.retry_after <= 0.1  # 1 token / 10 per sec = 0.1s

    def test_retry_after_when_tokens_available(self):
        bucket = _TokenBucket(capacity=10, refill_rate=1.0, tokens=5)
        assert bucket.retry_after == 0.0


# ===================================================================
# RateLimiter — basic
# ===================================================================

class TestRateLimiterBasic:
    def test_allows_under_limit(self):
        rl = RateLimiter(config=RateLimiterConfig(
            requests_per_second=100, burst_capacity=100,
            global_requests_per_second=1000, global_burst_capacity=1000,
        ))
        # Should not raise for first few requests
        for _ in range(50):
            rl.check("app1")

    def test_disabled_always_allows(self):
        rl = RateLimiter(config=RateLimiterConfig(enabled=False))
        for _ in range(1000):
            rl.check("app1")  # never raises

    def test_blocks_over_per_caller_limit(self):
        rl = RateLimiter(config=RateLimiterConfig(
            requests_per_second=10, burst_capacity=5,
            global_requests_per_second=10000, global_burst_capacity=10000,
        ))
        # Exhaust the burst
        for _ in range(5):
            rl.check("app1")
        # Next one should fail
        with pytest.raises(RateLimitExceeded) as exc_info:
            rl.check("app1")
        assert "app1" in str(exc_info.value)
        assert exc_info.value.retry_after_seconds > 0

    def test_blocks_over_global_limit(self):
        rl = RateLimiter(config=RateLimiterConfig(
            requests_per_second=10000, burst_capacity=10000,
            global_requests_per_second=10, global_burst_capacity=3,
        ))
        for _ in range(3):
            rl.check("app1")
        with pytest.raises(RateLimitExceeded) as exc_info:
            rl.check("app2")
        assert "Global" in str(exc_info.value)


# ===================================================================
# RateLimiter — caller independence
# ===================================================================

class TestRateLimiterCallers:
    def test_independent_callers(self):
        rl = RateLimiter(config=RateLimiterConfig(
            requests_per_second=10, burst_capacity=3,
            global_requests_per_second=10000, global_burst_capacity=10000,
        ))
        # Exhaust app1
        for _ in range(3):
            rl.check("app1")
        with pytest.raises(RateLimitExceeded):
            rl.check("app1")
        # app2 should still be fine
        rl.check("app2")

    def test_new_caller_gets_full_burst(self):
        rl = RateLimiter(config=RateLimiterConfig(
            requests_per_second=10, burst_capacity=5,
            global_requests_per_second=10000, global_burst_capacity=10000,
        ))
        # New caller starts with full burst capacity
        for _ in range(5):
            rl.check("brand_new_caller")


# ===================================================================
# RateLimiter — refill
# ===================================================================

class TestRateLimiterRefill:
    def test_blocked_caller_unblocks_over_time(self):
        rl = RateLimiter(config=RateLimiterConfig(
            requests_per_second=100, burst_capacity=2,
            global_requests_per_second=10000, global_burst_capacity=10000,
        ))
        rl.check("app1")
        rl.check("app1")
        with pytest.raises(RateLimitExceeded):
            rl.check("app1")

        # Simulate time passing — bucket refills at 100/s, need 1 token → 0.01s
        time.sleep(0.05)
        rl.check("app1")  # should succeed now


# ===================================================================
# RateLimiter — stats & cleanup
# ===================================================================

class TestRateLimiterStats:
    def test_stats_initial(self):
        rl = RateLimiter()
        s = rl.stats
        assert s["enabled"] is True
        assert s["active_callers"] == 0
        assert s["total_requests"] == 0
        assert s["total_limited"] == 0

    def test_stats_after_requests(self):
        rl = RateLimiter(config=RateLimiterConfig(
            requests_per_second=10, burst_capacity=2,
            global_requests_per_second=10000, global_burst_capacity=10000,
        ))
        rl.check("app1")
        rl.check("app1")
        try:
            rl.check("app1")
        except RateLimitExceeded:
            pass
        s = rl.stats
        assert s["total_requests"] == 3
        assert s["total_limited"] == 1
        assert s["active_callers"] == 1

    def test_cleanup_idle_callers(self):
        rl = RateLimiter(config=RateLimiterConfig(
            requests_per_second=10, burst_capacity=10,
            global_requests_per_second=10000, global_burst_capacity=10000,
            idle_timeout_seconds=0.05,
        ))
        rl.check("app1")
        rl.check("app2")
        assert rl.stats["active_callers"] == 2

        # Wait for idle timeout, then trigger cleanup
        time.sleep(0.15)
        rl._last_cleanup = time.monotonic() - 120  # force _maybe_cleanup to run
        rl.check("app3")  # triggers _maybe_cleanup; app1/app2 now stale
        # app1 and app2 cleaned up, only app3 remains
        assert rl.stats["active_callers"] == 1


# ===================================================================
# CircuitBreaker — state transitions
# ===================================================================

class TestCircuitBreakerStates:
    def _make_cb(self, **overrides):
        defaults = dict(failure_threshold=3, success_threshold=2, timeout_seconds=0.1)
        defaults.update(overrides)
        return CircuitBreaker(config=CircuitBreakerConfig(**defaults))

    def test_starts_allowing(self):
        cb = self._make_cb()
        cb.check("source1")  # no exception — no circuit exists yet

    def test_stays_closed_on_success(self):
        cb = self._make_cb()
        cb.record_failure("source1")
        cb.record_success("source1")
        cb.check("source1")  # still closed

    def test_opens_after_threshold_failures(self):
        cb = self._make_cb(failure_threshold=3)
        for _ in range(3):
            cb.record_failure("source1")
        with pytest.raises(CircuitBreakerOpen) as exc_info:
            cb.check("source1")
        assert exc_info.value.source_key == "source1"
        assert exc_info.value.retry_after_seconds > 0

    def test_does_not_open_below_threshold(self):
        cb = self._make_cb(failure_threshold=5)
        for _ in range(4):
            cb.record_failure("source1")
        cb.check("source1")  # should not raise — only 4 failures, need 5

    def test_transitions_to_half_open_after_timeout(self):
        cb = self._make_cb(failure_threshold=2, timeout_seconds=0.05)
        cb.record_failure("s1")
        cb.record_failure("s1")
        with pytest.raises(CircuitBreakerOpen):
            cb.check("s1")

        time.sleep(0.06)  # wait for timeout
        cb.check("s1")  # should now be half-open (no exception)

        health = cb.get_source_health()
        assert health["s1"]["state"] == "half_open"

    def test_half_open_closes_on_success(self):
        cb = self._make_cb(failure_threshold=2, success_threshold=2, timeout_seconds=0.05)
        cb.record_failure("s1")
        cb.record_failure("s1")
        time.sleep(0.06)
        cb.check("s1")  # transitions to half_open

        cb.record_success("s1")
        cb.record_success("s1")  # meets success_threshold

        health = cb.get_source_health()
        assert health["s1"]["state"] == "closed"

    def test_half_open_reopens_on_failure(self):
        cb = self._make_cb(failure_threshold=2, timeout_seconds=0.05)
        cb.record_failure("s1")
        cb.record_failure("s1")
        time.sleep(0.06)
        cb.check("s1")  # half_open

        cb.record_failure("s1")  # fail during half_open → reopen

        with pytest.raises(CircuitBreakerOpen):
            cb.check("s1")


# ===================================================================
# CircuitBreaker — disabled
# ===================================================================

class TestCircuitBreakerDisabled:
    def test_disabled_never_blocks(self):
        cb = CircuitBreaker(config=CircuitBreakerConfig(enabled=False, failure_threshold=1))
        for _ in range(100):
            cb.record_failure("s1")
        cb.check("s1")  # no exception

    def test_disabled_ignores_success(self):
        cb = CircuitBreaker(config=CircuitBreakerConfig(enabled=False))
        cb.record_success("s1")  # no error


# ===================================================================
# CircuitBreaker — independent sources
# ===================================================================

class TestCircuitBreakerSources:
    def test_sources_tracked_independently(self):
        cb = CircuitBreaker(config=CircuitBreakerConfig(failure_threshold=2))
        cb.record_failure("snowflake")
        cb.record_failure("snowflake")
        # snowflake is open
        with pytest.raises(CircuitBreakerOpen):
            cb.check("snowflake")
        # oracle is fine
        cb.check("oracle")

    def test_multiple_sources_in_stats(self):
        cb = CircuitBreaker(config=CircuitBreakerConfig(failure_threshold=2))
        cb.record_failure("s1")
        cb.record_failure("s1")
        cb.record_failure("s2")
        s = cb.stats
        assert s["tracked_sources"] == 2
        assert s["states"]["open"] == 1      # s1
        assert s["states"]["closed"] == 1    # s2 (only 1 failure)


# ===================================================================
# CircuitBreaker — stats & health
# ===================================================================

class TestCircuitBreakerStats:
    def test_stats_initial(self):
        cb = CircuitBreaker()
        s = cb.stats
        assert s["enabled"] is True
        assert s["tracked_sources"] == 0
        assert s["states"] == {"closed": 0, "open": 0, "half_open": 0}

    def test_get_source_health(self):
        cb = CircuitBreaker(config=CircuitBreakerConfig(failure_threshold=3))
        cb.record_failure("s1")
        cb.record_failure("s1")
        health = cb.get_source_health()
        assert "s1" in health
        assert health["s1"]["state"] == "closed"
        assert health["s1"]["failure_count"] == 2

    def test_get_source_health_empty(self):
        cb = CircuitBreaker()
        assert cb.get_source_health() == {}
