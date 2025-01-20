import pytest

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory

from accounts.factories.custom_user import CustomUserFactory
from accounts.utils.generate_token_for_user import generate_token_for_user
from accounts.models.user_token import UserToken


@pytest.fixture
def api_client():
    """Create a test client."""
    return APIClient()


@pytest.fixture
def mock_request(api_client):
    """Create a mock request with user agent."""
    factory = APIRequestFactory()
    request = factory.post("/")
    request.META["HTTP_USER_AGENT"] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    )
    return request


@pytest.mark.django_db
class TestLogout:
    """Test suite for logout functionality."""

    def test_successful_logout(self, api_client, mock_request):
        """Test successful logout with valid permanent token."""
        user = CustomUserFactory.create_verified()
        token_result = generate_token_for_user(
            user=user, request=mock_request, is_temporary=False
        )
        token = token_result.value["token"]

        url = reverse("accounts:logout")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Logged out successfully"

        # Verify token was invalidated
        token_obj = UserToken.objects.get(token=token)
        assert not token_obj.is_valid

    def test_logout_with_invalid_token(self, api_client):
        """Test logout attempt with invalid token."""
        url = reverse("accounts:logout")
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in str(response.data["detail"])

    def test_logout_with_temporary_token(self, api_client, mock_request):
        """Test logout attempt with temporary token."""
        user = CustomUserFactory.create_verified()
        token_result = generate_token_for_user(
            user=user, request=mock_request, is_temporary=True
        )
        token = token_result.value["token"]

        url = reverse("accounts:logout")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_token"
        assert "Invalid token type" in str(response.data["errors"])

    def test_logout_with_already_invalidated_token(self, api_client, mock_request):
        """Test logout attempt with an already invalidated token."""
        user = CustomUserFactory.create_verified()
        token_result = generate_token_for_user(
            user=user, request=mock_request, is_temporary=False
        )
        token = token_result.value["token"]

        # Invalidate token
        UserToken.objects.filter(token=token).update(is_valid=False)

        url = reverse("accounts:logout")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

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

    def test_logout_with_multiple_devices(self, api_client, mock_request):
        """Test logout from one device doesn't affect other devices."""
        user = CustomUserFactory.create_verified()

        # Create tokens for multiple devices with different user agents
        mock_request.META["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
        )
        web_token_result = generate_token_for_user(
            user=user, request=mock_request, is_temporary=False
        )
        web_token = web_token_result.value["token"]

        mock_request.META["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6) AppleWebKit/605.1.15 Safari/604.1"
        )
        mobile_token_result = generate_token_for_user(
            user=user, request=mock_request, is_temporary=False
        )
        mobile_token = mobile_token_result.value["token"]

        # Logout from web device
        url = reverse("accounts:logout")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {web_token}")
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Verify web token was invalidated but mobile token remains valid
        web_token_obj = UserToken.objects.get(token=web_token)
        mobile_token_obj = UserToken.objects.get(token=mobile_token)
        assert not web_token_obj.is_valid
        assert mobile_token_obj.is_valid
