"""Test configuration module."""

from __future__ import annotations

from warnings import simplefilter as warnings_simplefilter

from pytest import Config as pytestConfig
from pytest import fixture
from rest_framework.test import APIClient

from accounts.models.custom_user import CustomUser


def pytest_configure(config: pytestConfig):
    """Configure pytest."""
    warnings_simplefilter("ignore", DeprecationWarning)


@fixture(autouse=True)
def enable_db_access_for_all_tests(db: pytestConfig) -> None:
    """Enable DB access for all tests."""
    pass


@fixture
def api_client() -> APIClient:
    """Create API client."""
    return APIClient()


@fixture
def create_verified_user() -> CustomUser:
    """Create a verified user for testing."""
    return CustomUser.objects.create_user(
        username="testuser",
        email="test@test.com",
        password="test123",
        is_verified=True,
    )


@fixture
def create_unverified_user() -> CustomUser:
    """Create an unverified user for testing."""
    return CustomUser.objects.create_user(
        username="unverified",
        email="unverified@test.com",
        password="test123",
        is_verified=False,
    )
