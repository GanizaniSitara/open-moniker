"""Tests for the resolution cache layer (InMemoryCache + RedisCache).

Run: C:/Anaconda3/envs/python312/python.exe -m pytest tests/test_cache.py -v
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from moniker_svc.cache.memory import CacheEntry, InMemoryCache
from moniker_svc.cache.redis import CachedData, RedisCache
from moniker_svc.config import RedisConfig


# ===================================================================
# CacheEntry
# ===================================================================

class TestCacheEntry:
    def test_not_expired(self):
        entry = CacheEntry(value="x", created_at=time.time(), ttl_seconds=60, key="k")
        assert not entry.is_expired

    def test_expired(self):
        entry = CacheEntry(value="x", created_at=time.time() - 100, ttl_seconds=10, key="k")
        assert entry.is_expired

    def test_age_seconds(self):
        entry = CacheEntry(value="x", created_at=time.time() - 5, ttl_seconds=60, key="k")
        assert 4.5 < entry.age_seconds < 6.0


# ===================================================================
# InMemoryCache — basic operations
# ===================================================================

class TestInMemoryCacheBasic:
    @pytest.fixture
    def cache(self):
        return InMemoryCache(max_size=100, default_ttl_seconds=60.0)

    def test_get_miss_returns_none(self, cache):
        assert cache.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_set_and_get_roundtrip(self, cache):
        await cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_set_multiple_keys(self, cache):
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.set("c", 3)
        assert cache.get("a") == 1
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.size == 3

    @pytest.mark.asyncio
    async def test_overwrite_existing_key(self, cache):
        await cache.set("key", "old")
        await cache.set("key", "new")
        assert cache.get("key") == "new"
        assert cache.size == 1


# ===================================================================
# InMemoryCache — TTL expiration
# ===================================================================

class TestInMemoryCacheTTL:
    @pytest.mark.asyncio
    async def test_entry_expires_after_ttl(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=0.1)
        await cache.set("key", "value")
        assert cache.get("key") == "value"
        await asyncio.sleep(0.15)
        assert cache.get("key") is None

    @pytest.mark.asyncio
    async def test_custom_ttl_per_entry(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=60.0)
        await cache.set("short", "gone soon", ttl_seconds=0.1)
        await cache.set("long", "stays", ttl_seconds=60.0)
        await asyncio.sleep(0.15)
        assert cache.get("short") is None
        assert cache.get("long") == "stays"

    @pytest.mark.asyncio
    async def test_get_entry_returns_none_when_expired(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=0.1)
        await cache.set("key", "value")
        await asyncio.sleep(0.15)
        assert cache.get_entry("key") is None

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=0.1)
        await cache.set("a", 1)
        await cache.set("b", 2)
        await asyncio.sleep(0.15)
        await cache.set("c", 3, ttl_seconds=60.0)  # this one stays
        removed = await cache.cleanup_expired()
        assert removed == 2
        assert cache.size == 1
        assert cache.get("c") == 3


# ===================================================================
# InMemoryCache — LRU eviction
# ===================================================================

class TestInMemoryCacheLRU:
    @pytest.mark.asyncio
    async def test_evicts_oldest_when_full(self):
        cache = InMemoryCache(max_size=3, default_ttl_seconds=60.0)
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.set("c", 3)
        # Cache is full (3/3), adding one more should evict "a"
        await cache.set("d", 4)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("d") == 4
        assert cache.size == 3

    @pytest.mark.asyncio
    async def test_access_order_updates_on_set(self):
        cache = InMemoryCache(max_size=3, default_ttl_seconds=60.0)
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.set("c", 3)
        # Re-set "a" — it moves to end of access order
        await cache.set("a", 10)
        # Now "b" is oldest
        await cache.set("d", 4)
        assert cache.get("b") is None  # evicted
        assert cache.get("a") == 10    # kept (was refreshed)


# ===================================================================
# InMemoryCache — delete / clear
# ===================================================================

class TestInMemoryCacheDeleteClear:
    @pytest.mark.asyncio
    async def test_delete_existing_key(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=60.0)
        await cache.set("key", "value")
        result = await cache.delete("key")
        assert result is True
        assert cache.get("key") is None
        assert cache.size == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=60.0)
        result = await cache.delete("nope")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=60.0)
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.set("c", 3)
        await cache.clear()
        assert cache.size == 0
        assert cache.get("a") is None


# ===================================================================
# InMemoryCache — stats
# ===================================================================

class TestInMemoryCacheStats:
    @pytest.mark.asyncio
    async def test_stats_initial(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=60.0)
        s = cache.stats
        assert s["size"] == 0
        assert s["hits"] == 0
        assert s["misses"] == 0
        assert s["hit_rate_percent"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_hits_and_misses(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=60.0)
        await cache.set("key", "value")
        cache.get("key")       # hit
        cache.get("key")       # hit
        cache.get("missing")   # miss
        s = cache.stats
        assert s["hits"] == 2
        assert s["misses"] == 1
        assert s["hit_rate_percent"] == pytest.approx(66.67, abs=0.1)

    @pytest.mark.asyncio
    async def test_expired_entry_counts_as_miss(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=0.1)
        await cache.set("key", "value")
        cache.get("key")  # hit
        await asyncio.sleep(0.15)
        cache.get("key")  # miss (expired)
        s = cache.stats
        assert s["hits"] == 1
        assert s["misses"] == 1


# ===================================================================
# InMemoryCache — get_or_load / refresh / atomic_replace_all
# ===================================================================

class TestInMemoryCacheAdvanced:
    @pytest.mark.asyncio
    async def test_get_or_load_cache_miss(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=60.0)
        loader = AsyncMock(return_value="loaded_value")
        result = await cache.get_or_load("key", loader)
        assert result == "loaded_value"
        loader.assert_called_once()
        # Second call should use cache
        result2 = await cache.get_or_load("key", loader)
        assert result2 == "loaded_value"
        loader.assert_called_once()  # not called again

    @pytest.mark.asyncio
    async def test_refresh_replaces_value(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=60.0)
        await cache.set("key", "old")
        loader = AsyncMock(return_value="new")
        result = await cache.refresh("key", loader)
        assert result == "new"
        assert cache.get("key") == "new"

    @pytest.mark.asyncio
    async def test_atomic_replace_all(self):
        cache = InMemoryCache(max_size=100, default_ttl_seconds=60.0)
        await cache.set("old1", 1)
        await cache.set("old2", 2)
        await cache.atomic_replace_all({"new1": 10, "new2": 20})
        assert cache.get("old1") is None
        assert cache.get("old2") is None
        assert cache.get("new1") == 10
        assert cache.get("new2") == 20
        assert cache.size == 2


# ===================================================================
# CachedData — JSON serialization
# ===================================================================

class TestCachedData:
    def test_roundtrip(self):
        original = CachedData(
            data=[{"col1": "a", "col2": 1}],
            row_count=1,
            last_refresh=datetime(2026, 3, 21, 12, 0, 0),
            refresh_duration_ms=42.5,
            columns=["col1", "col2"],
        )
        json_str = original.to_json()
        restored = CachedData.from_json(json_str)
        assert restored.data == original.data
        assert restored.row_count == original.row_count
        assert restored.last_refresh == original.last_refresh
        assert restored.refresh_duration_ms == original.refresh_duration_ms
        assert restored.columns == original.columns

    def test_roundtrip_no_columns(self):
        original = CachedData(
            data=[],
            row_count=0,
            last_refresh=datetime(2026, 1, 1),
            refresh_duration_ms=0.0,
            columns=None,
        )
        restored = CachedData.from_json(original.to_json())
        assert restored.columns is None
        assert restored.row_count == 0


# ===================================================================
# RedisCache — without real Redis (mocked)
# ===================================================================

class TestRedisCacheDisconnected:
    def _make_cache(self, enabled=True):
        config = RedisConfig(enabled=enabled)
        return RedisCache(config)

    @pytest.mark.asyncio
    async def test_connect_returns_false_when_disabled(self):
        cache = self._make_cache(enabled=False)
        result = await cache.connect()
        assert result is False
        assert not cache.is_connected

    @pytest.mark.asyncio
    async def test_get_returns_none_when_disconnected(self):
        cache = self._make_cache()
        result = await cache.get("any/path")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_returns_false_when_disconnected(self):
        cache = self._make_cache()
        data = CachedData(data=[], row_count=0, last_refresh=datetime.now(), refresh_duration_ms=0)
        result = await cache.set("path", data)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_disconnected(self):
        cache = self._make_cache()
        result = await cache.delete("path")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_cached_paths_empty_when_disconnected(self):
        cache = self._make_cache()
        result = await cache.list_cached_paths()
        assert result == []

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self):
        cache = self._make_cache()
        health = await cache.health_check()
        assert health["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_connect_returns_false_when_redis_unreachable(self):
        config = RedisConfig(enabled=True, host="127.0.0.1", port=59999)
        cache = RedisCache(config)
        result = await cache.connect()
        assert result is False
        assert not cache.is_connected

    @pytest.mark.asyncio
    async def test_key_format(self):
        config = RedisConfig(prefix="test:cache:")
        cache = RedisCache(config)
        assert cache._key("risk.cvar") == "test:cache:risk.cvar"

    @pytest.mark.asyncio
    async def test_close_when_no_client(self):
        cache = self._make_cache()
        await cache.close()  # should not raise
        assert not cache.is_connected


# ===================================================================
# RedisCache — with mocked Redis client
# ===================================================================

class TestRedisCacheMocked:
    @pytest.fixture
    def cache_with_client(self):
        config = RedisConfig(enabled=True, prefix="moniker:cache:")
        cache = RedisCache(config)
        mock_client = AsyncMock()
        cache._client = mock_client
        cache._connected = True
        return cache, mock_client

    @pytest.mark.asyncio
    async def test_get_hit(self, cache_with_client):
        cache, mock_client = cache_with_client
        data = CachedData(
            data=[{"x": 1}], row_count=1,
            last_refresh=datetime(2026, 1, 1), refresh_duration_ms=5.0,
        )
        mock_client.get.return_value = data.to_json()
        result = await cache.get("risk.cvar")
        mock_client.get.assert_called_once_with("moniker:cache:risk.cvar")
        assert result is not None
        assert result.data == [{"x": 1}]

    @pytest.mark.asyncio
    async def test_get_miss(self, cache_with_client):
        cache, mock_client = cache_with_client
        mock_client.get.return_value = None
        result = await cache.get("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_without_ttl(self, cache_with_client):
        cache, mock_client = cache_with_client
        data = CachedData(
            data=[], row_count=0,
            last_refresh=datetime(2026, 1, 1), refresh_duration_ms=0,
        )
        result = await cache.set("path", data)
        assert result is True
        mock_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache_with_client):
        cache, mock_client = cache_with_client
        data = CachedData(
            data=[], row_count=0,
            last_refresh=datetime(2026, 1, 1), refresh_duration_ms=0,
        )
        result = await cache.set("path", data, ttl_seconds=300)
        assert result is True
        mock_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self, cache_with_client):
        cache, mock_client = cache_with_client
        result = await cache.delete("path")
        assert result is True
        mock_client.delete.assert_called_once_with("moniker:cache:path")

    @pytest.mark.asyncio
    async def test_get_ttl(self, cache_with_client):
        cache, mock_client = cache_with_client
        mock_client.ttl.return_value = 120
        result = await cache.get_ttl("path")
        assert result == 120

    @pytest.mark.asyncio
    async def test_get_ttl_no_key(self, cache_with_client):
        cache, mock_client = cache_with_client
        mock_client.ttl.return_value = -2
        result = await cache.get_ttl("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_handles_exception(self, cache_with_client):
        cache, mock_client = cache_with_client
        mock_client.get.side_effect = Exception("connection lost")
        result = await cache.get("path")
        assert result is None  # graceful degradation

    @pytest.mark.asyncio
    async def test_set_handles_exception(self, cache_with_client):
        cache, mock_client = cache_with_client
        mock_client.set.side_effect = Exception("connection lost")
        data = CachedData(
            data=[], row_count=0,
            last_refresh=datetime(2026, 1, 1), refresh_duration_ms=0,
        )
        result = await cache.set("path", data)
        assert result is False  # graceful degradation
