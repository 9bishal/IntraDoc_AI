"""
Lightweight In-Memory LRU Cache for RAG queries.

Designed for 8GB RAM systems — caps memory usage with configurable limits.
Provides:
    - Query result caching (avoids redundant FAISS searches)
    - Embedding caching (avoids re-computing for recent queries)
    - TTL-based expiry (stale results auto-evict)
"""

import hashlib
import logging
import time
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe LRU cache with TTL expiry.

    Memory-conscious: enforces max entry count.
    On 8GB RAM, 500 cached queries ≈ ~5MB overhead (negligible).
    """

    def __init__(self, max_size=500, ttl_seconds=600):
        """
        Args:
            max_size: Maximum number of entries.
            ttl_seconds: Time-to-live for entries (default 10 minutes).
        """
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _make_key(self, query, departments):
        """Create a deterministic cache key from query + departments."""
        raw = f"{query.strip().lower()}|{'|'.join(sorted(departments))}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, query, departments):
        """
        Retrieve cached result if fresh.

        Args:
            query: The search query.
            departments: List of department names.

        Returns:
            Cached result or None if miss/expired.
        """
        key = self._make_key(query, departments)

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                # Check TTL
                if time.time() - entry['time'] < self.ttl:
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    self._hits += 1
                    logger.debug(f"Cache HIT for query key={key[:8]}...")
                    return entry['data']
                else:
                    # Expired
                    del self._cache[key]

            self._misses += 1
            return None

    def put(self, query, departments, data):
        """
        Store a result in cache.

        Args:
            query: The search query.
            departments: List of department names.
            data: The result data to cache.
        """
        key = self._make_key(query, departments)

        with self._lock:
            # Evict oldest if full
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = {
                'data': data,
                'time': time.time(),
            }

    def invalidate(self, department=None):
        """
        Invalidate cache entries.

        Args:
            department: If given, invalidate only entries involving this department.
                        If None, clear entire cache.
        """
        with self._lock:
            if department is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cache fully cleared ({count} entries)")
            else:
                # For department-specific invalidation, we clear everything
                # since cache keys are hashed and we can't selectively filter
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cache cleared for department '{department}' ({count} entries)")

    def stats(self):
        """Return cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'entries': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.1f}%",
                'ttl_seconds': self.ttl,
            }


# ---- Singleton caches ----
_search_cache = None
_embedding_cache = None


def get_search_cache():
    """Return singleton search result cache."""
    global _search_cache
    if _search_cache is None:
        _search_cache = LRUCache(max_size=500, ttl_seconds=600)
    return _search_cache


def get_embedding_cache():
    """Return singleton embedding cache (smaller, shorter TTL)."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = LRUCache(max_size=200, ttl_seconds=300)
    return _embedding_cache
