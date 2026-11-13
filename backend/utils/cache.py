import time
from functools import wraps
from typing import Dict, Any, Tuple

class SimpleMemoryCache:
    def __init__(self):
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        if key in self._cache:
            expires_at, value = self._cache[key]
            if time.time() < expires_at:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        expires_at = time.time() + ttl_seconds
        self._cache[key] = (expires_at, value)

    def clear(self) -> None:
        self._cache.clear()

memory_cache = SimpleMemoryCache()

def cache_response(ttl_seconds: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create unique cache key from function name and arguments
            cache_key = f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
            cached_val = memory_cache.get(cache_key)
            if cached_val is not None:
                return cached_val

            result = func(*args, **kwargs)
            memory_cache.set(cache_key, result, ttl_seconds)
            return result
        return wrapper
    return decorator
