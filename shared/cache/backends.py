from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from json import dumps as json_dumps
from json import loads as json_loads
from typing import TypeVar
from urllib.parse import urlparse

from django.conf import settings
from redis import Redis as RedisClient

from shared.utils.logger import logger

# Define a type variable for serializable types
T = TypeVar(
    "T",
    str,
    int,
    float,
    bool,
    list,
    dict,
    type(None),
)


class BaseCacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> str | int | float | bool | list | dict | None:
        """Retrieve a value from the cache by its key.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value if found, otherwise None.
        """
        pass

    @abstractmethod
    def set(
        self,
        key: str,
        value: str | int | float | bool | list | dict,
        ttl: int | None = None,
    ) -> bool:
        """Set a value in the cache.

        Args:
            key: The cache key to set.
            value: The value to store in the cache.
            ttl: Time to live in seconds. If None, uses default TTL.

        Returns:
            True if the value was successfully set, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a key from the cache.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key was successfully deleted, False otherwise.
        """
        pass


class RedisCacheBackend(BaseCacheBackend):
    """Redis cache backend implementation."""

    def __init__(self, url: str):
        """Initialize the Redis cache backend.

        Args:
            url: The connection URL for the Redis server.
        """
        parsed_url = urlparse(url)

        # Ajuste de configuración para mejor manejo de errores
        self.client = RedisClient(
            host=parsed_url.hostname or "localhost",
            port=parsed_url.port or 6379,
            username=parsed_url.username,
            password=parsed_url.password,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
            health_check_interval=30,
        )

        # Verificar conexión
        try:
            self.client.ping()
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")

    def get(self, key: str) -> str | int | float | bool | list | dict | None:
        """Retrieve a value from Redis cache.

        Args:
            key: The cache key to retrieve.

        Returns:
            The deserialized cached value if found, otherwise None.
        """
        value = self.client.get(key)
        if value:
            return json_loads(value)
        return None

    def set(
        self,
        key: str,
        value: str | int | float | bool | list | dict,
        ttl: int | None = None,
    ) -> bool:
        """Set a value in Redis cache.

        Args:
            key: The cache key to set.
            value: The value to store in the cache.
            ttl: Time to live in seconds. If None, uses default TTL.

        Returns:
            True if the value was successfully set, False otherwise.
        """
        try:
            serialized_value = json_dumps(value)
            result = self.client.set(key, serialized_value, ex=ttl)
            return bool(result)  # Redis retorna 'OK' para operaciones exitosas
        except Exception as e:
            logger.error(f"Error setting cache value: {e}", extra={"traceback": True})
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from Redis cache.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key was successfully deleted, False otherwise.
        """
        return bool(self.client.delete(key))


class UpstashCacheBackend(BaseCacheBackend):
    """Upstash cache backend implementation."""

    def __init__(self, url: str, token: str):
        """Initialize the Upstash Redis cache backend.

        Args:
            url: The connection URL for the Upstash Redis server.
            token: Authentication token for the Upstash service.
        """
        self.client = RedisClient.from_url(
            url, username="default", password=token, decode_responses=True, ssl=True
        )

    def get(self, key: str) -> str | int | float | bool | list | dict | None:
        """Retrieve a value from Upstash cache.

        Args:
            key: The cache key to retrieve.

        Returns:
            The deserialized cached value if found, otherwise None.
        """
        value = self.client.get(key)
        if value:
            return json_loads(value)
        return None

    def set(
        self,
        key: str,
        value: str | int | float | bool | list | dict,
        ttl: int | None = None,
    ) -> bool:
        """Set a value in Upstash cache.

        Args:
            key: The cache key to set.
            value: The value to store in the cache.
            ttl: Time to live in seconds. If None, uses default TTL.

        Returns:
            True if the value was successfully set, False otherwise.
        """
        try:
            serialized_value = json_dumps(value)
            return bool(self.client.set(key, serialized_value, ex=ttl))
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from Upstash cache.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key was successfully deleted, False otherwise.
        """
        return bool(self.client.delete(key))


class AWSElastiCacheBackend(BaseCacheBackend):
    """AWS ElastiCache backend implementation."""

    def __init__(self, url: str):
        """Initialize the AWS ElastiCache backend.

        Args:
            url: The connection URL for the AWS ElastiCache server.
        """
        parsed_url = urlparse(url)
        self.client = RedisClient(
            host=parsed_url.hostname,
            port=parsed_url.port or 6379,
            decode_responses=True,
            ssl=True,
            ssl_cert_reqs=None,
        )

    def get(self, key: str) -> str | int | float | bool | list | dict | None:
        """Retrieve a value from AWS ElastiCache.

        Args:
            key: The cache key to retrieve.

        Returns:
            The deserialized cached value if found, otherwise None.
        """
        value = self.client.get(key)
        if value:
            return json_loads(value)
        return None

    def set(
        self,
        key: str,
        value: str | int | float | bool | list | dict,
        ttl: int | None = None,
    ) -> bool:
        """Set a value in AWS ElastiCache.

        Args:
            key: The cache key to set.
            value: The value to store in the cache.
            ttl: Time to live in seconds. If None, uses default TTL.

        Returns:
            True if the value was successfully set, False otherwise.
        """
        try:
            serialized_value = json_dumps(value)
            return bool(self.client.set(key, serialized_value, ex=ttl))
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from AWS ElastiCache.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key was successfully deleted, False otherwise.
        """
        return bool(self.client.delete(key))


def get_cache_backend() -> BaseCacheBackend:
    """Factory function to get the appropriate cache backend.

    Returns:
        An instance of the configured cache backend.

    Raises:
        ValueError: If an invalid cache backend is specified.
    """
    cache_backend = settings.CACHE_BACKEND

    if cache_backend == "redis":
        return RedisCacheBackend(settings.REDIS_URL)
    elif cache_backend == "upstash":
        return UpstashCacheBackend(settings.UPSTASH_URL, settings.UPSTASH_TOKEN)
    elif cache_backend == "elasticache":
        return AWSElastiCacheBackend(settings.AWS_ELASTICACHE_URL)
    else:
        raise ValueError(f"Invalid cache backend: {cache_backend}")
