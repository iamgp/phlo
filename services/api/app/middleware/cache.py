from __future__ import annotations

import functools
import hashlib
import json
import time
from typing import Any, Callable

from app.config import settings

# In-memory cache store
_cache_store: dict[str, tuple[Any, float]] = {}


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a cache key from function name and arguments."""
    # Convert args and kwargs to a stable string representation
    key_data = {
        "func": func_name,
        "args": str(args),
        "kwargs": json.dumps(kwargs, sort_keys=True, default=str),
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int | None = None):
    """
    Decorator to cache function results in memory.

    Args:
        ttl: Time-to-live in seconds. Defaults to settings.cache_default_ttl
    """
    ttl = ttl or settings.cache_default_ttl

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, args, kwargs)

            # Check cache
            if cache_key in _cache_store:
                cached_value, expiry_time = _cache_store[cache_key]
                if time.time() < expiry_time:
                    # Cache hit
                    return cached_value

            # Cache miss - execute function
            result = await func(*args, **kwargs)

            # Store in cache
            expiry_time = time.time() + ttl
            _cache_store[cache_key] = (result, expiry_time)

            return result

        return wrapper

    return decorator


def clear_cache():
    """Clear all cached entries."""
    _cache_store.clear()


def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics."""
    now = time.time()
    total_entries = len(_cache_store)
    expired_entries = sum(1 for _, (_, expiry) in _cache_store.items() if expiry < now)

    return {
        "total_entries": total_entries,
        "active_entries": total_entries - expired_entries,
        "expired_entries": expired_entries,
    }
