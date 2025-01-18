from __future__ import annotations

from typing import Any

from shared.cache import cache as cache_instance
from shared.utils.logger import logger


class CachePatterns:
    """Cache key patterns for invalidation."""

    # Proyectos
    USER_PROJECTS = "user_projects_{user_id}"
    PROJECT_DETAIL = "project_detail_{project_id}_{user_id}"
    PROJECT_STATS = "project_stats_{project_id}"

    # Tareas
    PROJECT_TASKS = "project_tasks_{project_id}"
    TASK_DETAIL = "task_detail_{task_id}_{project_id}"
    TASK_COMMENTS = "task_comments_{task_id}"

    # Usuarios
    USER_STATS = "user_stats_{user_id}"

    # MFA
    MFA_METHODS = "mfa_methods"


def invalidate_cache_patterns(*patterns: str, **kwargs: Any) -> None:
    """Invalidate multiple cache patterns with dynamic parameters.

    Args:
        *patterns: Cache patterns to invalidate
        **kwargs: Parameters to format patterns

    Example:
        invalidate_cache_patterns(
            CachePatterns.USER_PROJECTS,
            CachePatterns.PROJECT_DETAIL,
            user_id=1,
            project_id=2
        )
    """
    try:
        for pattern in patterns:
            try:
                # Format pattern with provided parameters
                key = pattern.format(**kwargs)
                cache_instance.delete(key)
                logger.info(
                    "Cache invalidated",
                    extra={"pattern": pattern, "key": key, "params": kwargs},
                )
            except KeyError as e:
                # Log missing parameters for pattern
                logger.error(
                    "Missing parameter for cache invalidation",
                    extra={
                        "pattern": pattern,
                        "params": kwargs,
                        "missing_param": str(e),
                    },
                )
            except Exception as e:
                logger.error(
                    "Error invalidating cache pattern",
                    extra={
                        "pattern": pattern,
                        "params": kwargs,
                        "error": str(e),
                        "traceback": True,
                    },
                )
    except Exception as e:
        logger.error(
            "Error in cache invalidation",
            extra={
                "patterns": patterns,
                "params": kwargs,
                "error": str(e),
                "traceback": True,
            },
        )
