from collections import OrderedDict
from threading import Lock
from time import monotonic


class SimpleTTLCache:
    def __init__(self, default_ttl_seconds=900, max_entries=256):
        self.default_ttl = default_ttl_seconds
        self.max_entries = max_entries
        self._cache = OrderedDict()
        self._lock = Lock()

    def get(self, key):
        with self._lock:
            entry = self._cache.pop(key, None)
            if entry and entry[0] > monotonic():
                self._cache[key] = entry
                return entry[1]
        return None

    def set(self, key, value, ttl_seconds=None):
        ttl = self.default_ttl if ttl_seconds is None else ttl_seconds
        with self._lock:
            self._cache[key] = (monotonic() + ttl, value)
            self._cache.move_to_end(key)
            if len(self._cache) > self.max_entries:
                self._cache.popitem(last=False)

    def clear(self):
        with self._lock:
            self._cache.clear()


search_cache = SimpleTTLCache()
