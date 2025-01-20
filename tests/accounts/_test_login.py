from __future__ import annotations

from django.urls import reverse
from faker import Faker
from pytest import fixture as pytest_fixture
from pytest import mark as pytest_mark
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models.custom_user import CustomUser

fake = Faker()


@pytest_fixture
def api_client():
    """Create a test client."""
    return APIClient()


@pytest_fixture
def verified_user():
    """Create a verified user for testing."""
    user = CustomUser.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password="testpass123",
    )
    user.is_verified = True
    user.save()
    return user


@pytest_fixture
def unverified_user():
    """Create an unverified user for testing."""
    user = CustomUser.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password="testpass123",
    )
    return user


@pytest_mark.django_db
class TestLogin:
    """Test suite for login functionality."""

    def test_successful_login(self, api_client, verified_user):
        """Test successful login with valid credentials."""
        url = reverse("accounts:login")
        data = {
            "email": verified_user.email,
            "password": "testpass123",
        }

        response = api_client.post(
            url,
            data,
        )

        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.data["data"]
        assert response.data["data"]["user"]["email"] == verified_user.email
        assert not response.data["data"]["requires_verification"]

    def test_unverified_user_login(self, api_client, unverified_user):
        """Test login attempt with unverified user."""
        url = reverse("accounts:login")
        data = {
            "email": unverified_user.email,
            "password": "testpass123",
        }

        response = api_client.post(
            url,
            data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "email_not_verified"
        assert "verification" in response.data["data"]
        assert response.data["data"]["requires_verification"]

    def test_invalid_credentials(self, api_client):
        """Test login attempt with invalid credentials."""
        url = reverse("accounts:login")
        data = {
            "email": fake.email(),
            "password": "wrongpass123",
        }

        response = api_client.post(
            url,
            data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in str(response.data["errors"])

    def test_missing_credentials(self, api_client):
        """Test login attempt with missing credentials."""
        url = reverse("accounts:login")
        data = {}

        response = api_client.post(
            url,
            data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in str(response.data["errors"])
        assert "password" in str(response.data["errors"])

    def test_invalid_email_format(self, api_client):
        """Test login attempt with invalid email format."""
        url = reverse("accounts:login")
        data = {
            "email": "invalid-email",
            "password": "testpass123",
        }

        response = api_client.post(
            url,
            data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in str(response.data["errors"])
