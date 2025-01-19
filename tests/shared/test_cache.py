from __future__ import annotations

from time import sleep
from typing import Any

from django.conf import settings
from faker import Faker
from pytest import fixture as pytest_fixture
from pytest import mark as pytest_mark

from shared.cache import cache as cache_instance
from shared.cache.backends import AWSElastiCacheBackend
from shared.cache.backends import RedisCacheBackend
from shared.cache.backends import UpstashCacheBackend
from shared.cache.decorators import cached
from shared.cache.utils import CachePatterns
from shared.cache.utils import invalidate_cache_patterns

fake = Faker()


# Test data fixtures
@pytest_fixture
def sample_data() -> dict[str, Any]:
    """Create sample data for testing."""
    return {
        "string": "test_string",
        "integer": 42,
        "float": 3.14,
        "list": [1, 2, 3],
        "dict": {"key": "value"},
        "boolean": True,
    }


@pytest_fixture
def complex_data() -> dict[str, Any]:
    """Create more complex nested data for testing."""
    return {
        "users": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "settings": {"notifications": True, "theme": "dark"},
            },
            {
                "id": 2,
                "name": "Jane Doe",
                "email": "jane@example.com",
                "settings": {"notifications": False, "theme": "light"},
            },
        ],
        "metadata": {"version": "1.0", "timestamp": "2024-01-01T00:00:00Z"},
    }


# Basic cache operations tests
@pytest_mark.django_db
class TestBasicCacheOperations:
    """Test basic cache operations."""

    def test_set_get_operations(self, sample_data: dict):
        """Test basic set and get operations for different data types."""
        for key, value in sample_data.items():
            # Test setting values
            assert cache_instance.set(f"test_{key}", value)

            # Test getting values
            assert cache_instance.get(f"test_{key}") == value

    def test_delete_operation(self, sample_data: dict):
        """Test delete operation."""
        key = "test_delete"

        # Set and verify value
        assert cache_instance.set(key, sample_data["string"])
        assert cache_instance.get(key) == sample_data["string"]

        # Delete and verify removal
        assert cache_instance.delete(key)
        assert cache_instance.get(key) is None

    def test_ttl_expiration(self):
        """Test that cached values expire after TTL."""
        key = "test_ttl"
        value = "test_value"
        ttl = 1  # 1 second TTL

        # Set with short TTL
        assert cache_instance.set(key, value, ttl)
        assert cache_instance.get(key) == value

        # Wait for expiration
        sleep(ttl + 0.1)
        assert cache_instance.get(key) is None

    def test_complex_data_serialization(self, complex_data: dict):
        """Test caching complex nested data structures."""
        key = "test_complex"

        # Set complex data
        assert cache_instance.set(key, complex_data)

        # Retrieve and verify
        cached_data = cache_instance.get(key)
        assert cached_data == complex_data
        assert cached_data["users"][0]["settings"]["theme"] == "dark"


# Cache decorator tests
@pytest_mark.django_db
class TestCacheDecorator:
    """Test cache decorator functionality."""

    def test_basic_caching(self):
        """Test basic function caching."""
        call_count = 0

        @cached(ttl=10)
        def cached_function(param: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"Result for {param}"

        # First call should cache
        result1 = cached_function("test")
        initial_count = call_count
        assert result1 == "Result for test"
        assert initial_count == 1

        # Second call should use cache
        result2 = cached_function("test")
        assert result2 == "Result for test"
        assert call_count == initial_count  # Count shouldn't increase

        # Different param should trigger new cache
        result3 = cached_function("test2")
        assert result3 == "Result for test2"
        assert call_count == initial_count + 1  # Count should increase

    def test_different_params(self):
        """Test caching with different parameters."""
        call_count = 0

        @cached(ttl=10)
        def cached_function(param: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"Result for {param}"

        # Different params should trigger different cache keys
        result1 = cached_function("param1")
        result2 = cached_function("param2")

        assert result1 == "Result for param1"
        assert result2 == "Result for param2"
        expected_call_count = 2
        assert (
            call_count == expected_call_count
        )  # Should be called twice for different params

    def test_cache_key_prefix(self):
        """Test cache key prefix functionality."""
        call_count = 0

        @cached(ttl=10, key_prefix="custom_prefix")
        def cached_function(param: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"Result for {param}"

        test_param = "test"
        result = cached_function(test_param)
        assert result == f"Result for {test_param}"

        # Calculate the expected cache key
        from hashlib import sha256

        key_string = f"custom_prefix_{test_param}"
        expected_key = f"cache_{sha256(key_string.encode()).hexdigest()[:32]}"

        # Verify the value exists in cache with the correct key
        cached_value = cache_instance.get(expected_key)
        assert cached_value == f"Result for {test_param}"

    def test_cache_key_variations(self):
        """Test different variations of cache key generation."""
        call_count = 0

        @cached(ttl=10, key_prefix="test_prefix")
        def cached_function(
            param1: str | None = None, param2: int | None = None
        ) -> str:
            nonlocal call_count
            call_count += 1
            return f"Result for {param1 or 'default'} and {param2 or 0}"

        # Test with no parameters
        result1 = cached_function()
        initial_count = call_count
        assert result1 == "Result for default and 0"

        # Should use cache for same call with no parameters
        result2 = cached_function()
        assert result2 == "Result for default and 0"
        assert call_count == initial_count

        # Test with one parameter
        result3 = cached_function(param1="test")
        assert result3 == "Result for test and 0"
        assert call_count == initial_count + 1

        # Test with multiple parameters
        result4 = cached_function(param1="test", param2=42)
        assert result4 == "Result for test and 42"
        assert call_count == initial_count + 2

        # Verify cache is working with same parameters
        result5 = cached_function(param1="test", param2=42)
        assert result5 == "Result for test and 42"
        assert call_count == initial_count + 2  # Count shouldn't increase


# Cache pattern invalidation tests
@pytest_mark.django_db
class TestCachePatternInvalidation:
    """Test cache pattern invalidation."""

    def test_single_pattern_invalidation(self):
        """Test invalidating a single cache pattern."""
        # Set up some cached values
        cache_instance.set(
            CachePatterns.USER_PROJECTS.format(user_id=1), ["project1", "project2"]
        )

        # Invalidate the pattern
        invalidate_cache_patterns(CachePatterns.USER_PROJECTS, user_id=1)

        # Verify the cache was invalidated
        assert cache_instance.get(CachePatterns.USER_PROJECTS.format(user_id=1)) is None

    def test_multiple_patterns_invalidation(self):
        """Test invalidating multiple cache patterns."""
        # Set up cached values
        cache_instance.set(
            CachePatterns.USER_PROJECTS.format(user_id=1), ["project1", "project2"]
        )
        cache_instance.set(
            CachePatterns.PROJECT_STATS.format(project_id=1), {"total_tasks": 5}
        )

        # Invalidate multiple patterns
        invalidate_cache_patterns(
            CachePatterns.USER_PROJECTS,
            CachePatterns.PROJECT_STATS,
            user_id=1,
            project_id=1,
        )

        # Verify all caches were invalidated
        assert cache_instance.get(CachePatterns.USER_PROJECTS.format(user_id=1)) is None
        assert (
            cache_instance.get(CachePatterns.PROJECT_STATS.format(project_id=1)) is None
        )


# Backend-specific tests
@pytest_mark.django_db
class TestCacheBackends:
    """Test specific cache backend functionality."""

    def test_redis_backend(self):
        """Test Redis cache backend."""
        backend = RedisCacheBackend(settings.REDIS_URL)

        # Test basic operations
        assert backend.set("test_key", "test_value")
        assert backend.get("test_key") == "test_value"
        assert backend.delete("test_key")

    def test_upstash_backend(self):
        """Test Upstash cache backend if configured."""
        if settings.UPSTASH_URL and settings.UPSTASH_TOKEN:
            backend = UpstashCacheBackend(settings.UPSTASH_URL, settings.UPSTASH_TOKEN)

            # Test basic operations
            assert backend.set("test_key", "test_value")
            assert backend.get("test_key") == "test_value"
            assert backend.delete("test_key")

    def test_elasticache_backend(self):
        """Test AWS ElastiCache backend if configured."""
        if settings.AWS_ELASTICACHE_URL:
            backend = AWSElastiCacheBackend(settings.AWS_ELASTICACHE_URL)

            # Test basic operations
            assert backend.set("test_key", "test_value")
            assert backend.get("test_key") == "test_value"
            assert backend.delete("test_key")
