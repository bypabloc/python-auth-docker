from __future__ import annotations

from django.urls import reverse
from faker import Faker
from pytest import fixture as pytest_fixture
from pytest import mark as pytest_mark
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models.custom_user import CustomUser
from accounts.models.user_token import UserToken
from accounts.utils.generate_token_for_user import generate_token_for_user

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
def permanent_token(verified_user: CustomUser, api_client: APIClient) -> str:
    """Generate a permanent token for testing."""
    result = generate_token_for_user(
        user=verified_user,
        request=api_client.post("/").wsgi_request,
        is_temporary=False,
    )
    return result.value["token"]


@pytest_fixture
def temp_token(verified_user: CustomUser, api_client: APIClient) -> str:
    """Generate a temporary token for testing."""
    result = generate_token_for_user(
        user=verified_user,
        request=api_client.post("/").wsgi_request,
        is_temporary=True,
    )
    return result.value["token"]


@pytest_mark.django_db
class TestLogout:
    """Test suite for logout functionality."""

    def test_successful_logout(self, api_client, verified_user, permanent_token):
        """Test successful logout with valid permanent token."""
        url = reverse("accounts:logout")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Logged out successfully"

        # Verify token was invalidated
        token_obj = UserToken.objects.get(token=permanent_token)
        assert not token_obj.is_valid

    def test_logout_with_invalid_token(self, api_client):
        """Test logout attempt with invalid token."""
        url = reverse("accounts:logout")
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in str(response.data["detail"])

    def test_logout_with_temporary_token(self, api_client, temp_token):
        """Test logout attempt with temporary token."""
        url = reverse("accounts:logout")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_token"
        assert "Invalid token type" in str(response.data["errors"])

    def test_logout_with_already_invalidated_token(
        self, api_client, verified_user, permanent_token
    ):
        """Test logout attempt with an already invalidated token."""
        # Invalidate token first
        UserToken.objects.filter(token=permanent_token).update(is_valid=False)

        url = reverse("accounts:logout")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token not found" in str(response.data["detail"])

    def test_logout_without_authentication(self, api_client):
        """Test logout attempt without authentication."""
        url = reverse("accounts:logout")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication credentials were not provided" in str(
            response.data["detail"]
        )
