"""
Production Redis-backed cache with TTL and local LRU fallback.
"""
import json
import hashlib
import logging
from functools import lru_cache
from typing import Optional, Any

logger = logging.getLogger(__name__)

# ── Local LRU Cache (in-process, no Redis needed) ─────────────

_local_cache: dict = {}


@lru_cache()
def get_config():
    """Cached config loader."""
    from app.config import settings
    return settings


def cache_key(*args) -> str:
    """Generate a deterministic cache key from arguments."""
    raw = json.dumps(args, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Redis Cache (optional, graceful fallback) ──────────────────

class RedisCache:
    """
    Production cache backed by Redis.
    Falls back to in-process dict if Redis is unavailable.
    """

    def __init__(self, prefix: str = "cvmatcher"):
        self.prefix = prefix
        self._redis = None
        self._init_redis()

    def _init_redis(self):
        try:
            import redis
            from app.config import settings
            self._redis = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self._redis.ping()
            logger.info("Redis cache connected.")
        except Exception as e:
            logger.warning(f"Redis unavailable, using local cache: {e}")
            self._redis = None

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[str]:
        fk = self._full_key(key)
        if self._redis:
            try:
                return self._redis.get(fk)
            except Exception:
                pass
        return _local_cache.get(fk)

    def set(self, key: str, value: Any, ttl: int = 3600):
        fk = self._full_key(key)
        val = json.dumps(value, default=str) if not isinstance(value, str) else value
        if self._redis:
            try:
                self._redis.setex(fk, ttl, val)
                return
            except Exception:
                pass
        _local_cache[fk] = val

    def delete(self, key: str):
        fk = self._full_key(key)
        if self._redis:
            try:
                self._redis.delete(fk)
            except Exception:
                pass
        _local_cache.pop(fk, None)

    def get_json(self, key: str) -> Optional[dict]:
        val = self.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return None
        return None

    def set_json(self, key: str, value: dict, ttl: int = 3600):
        self.set(key, json.dumps(value, default=str), ttl)
