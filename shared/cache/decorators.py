from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from hashlib import sha256
from inspect import signature
from typing import ParamSpec
from typing import TypeVar

from django.conf import settings

from shared.cache import cache as cache_instance

P = ParamSpec("P")
R = TypeVar("R")


def cached(
    ttl: int | None = None,
    key_prefix: str | None = None,
    key_pattern: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        key_pattern: Pattern string with format placeholders

    Returns:
        A decorator function that caches results
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not settings.CACHE_ENABLED:
                return func(*args, **kwargs)

            # If key_pattern is provided, use it to format the key
            if key_pattern:
                sig = signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                params = dict(bound_args.arguments)
                cache_key = key_pattern.format(**params)
            else:
                # Use old key generation logic as fallback
                base_prefix = key_prefix or func.__name__
                cache_key_parts = []

                if args:
                    cache_key_parts.extend(str(arg) for arg in args)

                if kwargs:
                    cache_key_parts.extend(
                        f"{k}:{v}" for k, v in sorted(kwargs.items())
                    )

                key_string = (
                    f"{base_prefix}_{'.'.join(cache_key_parts)}"
                    if cache_key_parts
                    else base_prefix
                )
                cache_key = f"cache_{sha256(key_string.encode()).hexdigest()[:32]}"

            # Try to get from cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Calculate and cache result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator
