from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec
from typing import TypeVar

from django.conf import settings

from shared.cache.backends import get_cache_backend

P = ParamSpec("P")
R = TypeVar("R")


def cached(
    ttl: int | None = None, key_prefix: str | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key

    Returns:
        A decorator function that caches results
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not settings.CACHE_ENABLED:
                return func(*args, **kwargs)

            # Create cache key
            cache_key = key_prefix or func.__name__
            if args:
                cache_key += "_" + "_".join(str(arg) for arg in args)
            if kwargs:
                cache_key += "_" + "_".join(
                    f"{k}_{v}" for k, v in sorted(kwargs.items())
                )

            cache = get_cache_backend()
            cached_value = cache.get(cache_key)

            if cached_value is not None:
                return cached_value  # type: ignore[no-any-return]

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator
