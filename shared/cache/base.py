from __future__ import annotations

from typing import TypeVar

from django.conf import settings

from shared.utils.logger import logger

T = TypeVar("T")


class CacheBase:
    """Base class for caching operations."""

    def get(self, key: str) -> str | int | float | list | dict | bool | None:
        """Get value from cache.

        Returns None if the key is not found or an error occurs.
        Supports common JSON-serializable types.
        """
        try:
            return self.backend.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}", extra={"traceback": True})
            return None

    def set(
        self,
        key: str,
        value: str | int | float | list | dict | bool,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache.

        Supports common JSON-serializable types.
        Uses default TTL if not specified.
        """
        try:
            return self.backend.set(key, value, ttl or settings.CACHE_TTL)
        except Exception as e:
            logger.error(f"Cache set error: {e}", extra={"traceback": True})
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return self.backend.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}", extra={"traceback": True})
            return False

    def clear(self) -> bool:
        """Clear all cache."""
        try:
            return self.backend.clear()
        except Exception as e:
            logger.error(f"Cache clear error: {e}", extra={"traceback": True})
            return False
