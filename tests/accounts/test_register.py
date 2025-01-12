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
def valid_user_data():
    """Create valid user data for testing."""
    return {
        "email": fake.email(),
        "username": fake.user_name(),
        "password": "TestPass123!",
    }


@pytest_fixture
def existing_user():
    """Create a user in the database."""
    return CustomUser.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password="TestPass123!",
    )


@pytest_mark.django_db
class TestRegistration:
    """Test suite for user registration functionality."""

    def test_successful_registration(self, api_client, valid_user_data):
        """Test successful user registration with valid data."""
        url = reverse("accounts:register")
        response = api_client.post(url, valid_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert "token" in response.data["data"]
        assert response.data["data"]["user"]["email"] == valid_user_data["email"]
        assert response.data["data"]["user"]["username"] == valid_user_data["username"]
        assert "verification" in response.data["data"]

        # Check user was created in database
        user = CustomUser.objects.get(email=valid_user_data["email"])
        assert user.username == valid_user_data["username"]
        assert not user.is_verified
        assert user.check_password(valid_user_data["password"])

    def test_registration_with_existing_email(
        self, api_client, existing_user, valid_user_data
    ):
        """Test registration attempt with an email that already exists."""
        url = reverse("accounts:register")
        valid_user_data["email"] = existing_user.email

        response = api_client.post(url, valid_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "user with this email address already exists" in str(
            response.data["errors"]
        )

    def test_registration_with_existing_username(
        self, api_client, existing_user, valid_user_data
    ):
        """Test registration attempt with a username that already exists."""
        url = reverse("accounts:register")
        valid_user_data["username"] = existing_user.username

        response = api_client.post(url, valid_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "A user with that username already exists" in str(
            response.data["errors"]
        )

    def test_registration_token_is_temporary(self, api_client, valid_user_data):
        """Test that the registration token is marked as temporary."""
        url = reverse("accounts:register")
        response = api_client.post(url, valid_user_data)

        assert response.status_code == status.HTTP_201_CREATED

        # Use the token to make a request that requires permanent token
        token = response.data["data"]["token"]
        logout_url = reverse("accounts:logout")
        auth_response = api_client.post(
            logout_url,
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        # Should fail because token is temporary
        assert auth_response.status_code == status.HTTP_400_BAD_REQUEST
        assert auth_response.data["code"] == "invalid_token"

    def test_registration_with_invalid_email_format(self, api_client, valid_user_data):
        """Test registration attempt with invalid email format."""
        url = reverse("accounts:register")
        valid_user_data["email"] = "invalid-email"

        response = api_client.post(url, valid_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Enter a valid email address" in str(response.data["errors"])

    def test_registration_with_short_password(self, api_client, valid_user_data):
        """Test registration attempt with a password that's too short."""
        url = reverse("accounts:register")
        valid_user_data["password"] = "short"  # Too short password

        response = api_client.post(url, valid_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This password is too short" in str(response.data["errors"])

    def test_registration_with_missing_fields(self, api_client):
        """Test registration attempt with missing required fields."""
        url = reverse("accounts:register")
        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in str(response.data["errors"])
        assert "username" in str(response.data["errors"])
        assert "password" in str(response.data["errors"])

    def test_registration_user_starts_unverified(self, api_client, valid_user_data):
        """Test that newly registered users start with unverified status."""
        url = reverse("accounts:register")
        response = api_client.post(url, valid_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert not response.data["data"]["user"]["is_verified"]

        user = CustomUser.objects.get(email=valid_user_data["email"])
        assert not user.is_verified
