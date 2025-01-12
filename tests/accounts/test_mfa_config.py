from __future__ import annotations

from django.urls import reverse
from faker import Faker
from pytest import fixture as pytest_fixture
from pytest import mark as pytest_mark
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models.custom_user import CustomUser
from accounts.models.mfa_method import MFAMethod
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


@pytest_mark.django_db
class TestMFAConfiguration:
    """Test suite for MFA configuration functionality."""

    def test_list_mfa_methods(self, api_client, permanent_token):
        """Test listing available MFA methods."""
        url = reverse("accounts:mfa-methods")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "methods" in response.data["data"]
        methods = response.data["data"]["methods"]
        assert len(methods) > 0

        # Verify expected methods exist
        method_names = {method["name"] for method in methods}
        assert "otp" in method_names
        assert "email" in method_names

    def test_configure_totp_mfa(self, api_client, permanent_token):
        """Test configuring TOTP-based MFA."""
        url = reverse("accounts:configure-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")

        # Get TOTP method ID
        totp_method = MFAMethod.objects.get(name="otp")

        data = {"is_enabled": True, "default_method": totp_method.id}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "secret" in response.data["data"]
        assert "provisioning_uri" in response.data["data"]
        assert "qr_code" in response.data["data"]
        assert "backup_codes" in response.data["data"]

        # Verify backup codes format
        backup_codes = response.data["data"]["backup_codes"]
        backup_codes_count = 5
        assert len(backup_codes) == backup_codes_count
        backup_code_length = 8
        assert all(len(code) == backup_code_length for code in backup_codes)

    def test_configure_email_mfa(self, api_client, permanent_token):
        """Test configuring email-based MFA."""
        url = reverse("accounts:configure-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")

        # Get email method ID
        email_method = MFAMethod.objects.get(name="email")

        data = {"is_enabled": True, "default_method": email_method.id}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "verification" in response.data["data"]
        assert (
            response.data["data"]["message"] == "Verification code sent to your email"
        )

    def test_get_mfa_config_when_not_configured(self, api_client, permanent_token):
        """Test getting MFA configuration when not yet configured."""
        url = reverse("accounts:configure-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["is_enabled"] is False
        assert response.data["data"]["default_method"] is None

    def test_configure_mfa_without_authentication(self, api_client):
        """Test attempting to configure MFA without authentication."""
        url = reverse("accounts:configure-mfa")

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_configure_mfa_with_invalid_method(self, api_client, permanent_token):
        """Test configuring MFA with an invalid method ID."""
        url = reverse("accounts:configure-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")

        data = {"is_enabled": True, "default_method": 999}  # Invalid method ID

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "default_method" in str(response.data["errors"])
