# shared/cache/__init__.py
from shared.cache.backends import get_cache_backend
from shared.cache.base import CacheBase


class Cache(CacheBase):
    """Cache implementation."""

    def __init__(self):
        """Initialize cache backend."""
        self.backend = get_cache_backend()


# Create singleton instance
cache = Cache()

# Export cache instance
__all__ = ["cache"]
