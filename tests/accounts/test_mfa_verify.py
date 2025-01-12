from __future__ import annotations

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from faker import Faker
from pyotp import TOTP
from pyotp import random_base32
from pytest import fixture as pytest_fixture
from pytest import mark as pytest_mark
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models.custom_user import CustomUser
from accounts.models.mfa_method import MFAMethod
from accounts.models.mfa_verification import MFAVerification
from accounts.models.user_mfa import UserMFA
from accounts.utils.generate_token_for_user import generate_token_for_user

fake = Faker()


@pytest_fixture
def setup_mfa_methods():
    """Ensure MFA methods exist for testing.
    Creates methods if they don't exist, returns existing ones otherwise."""
    # Create or get OTP method
    otp_method, _ = MFAMethod.objects.get_or_create(
        name="otp", defaults={"is_active": True}
    )

    # Create or get Email method
    email_method, _ = MFAMethod.objects.get_or_create(
        name="email", defaults={"is_active": True}
    )

    return {"otp": otp_method, "email": email_method}


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
    user.has_mfa = True
    user.save()
    return user


@pytest_fixture
def temp_token(verified_user: CustomUser, api_client: APIClient) -> str:
    """Generate a temporary token for testing."""
    result = generate_token_for_user(
        user=verified_user,
        request=api_client.post("/").wsgi_request,
        is_temporary=True,
    )
    return result.value["token"]


@pytest_fixture
def totp_config(verified_user: CustomUser, setup_mfa_methods) -> dict:
    """Create TOTP configuration for testing."""
    totp_method = MFAMethod.objects.get(name="otp")
    totp_secret = random_base32()

    mfa_config = UserMFA.objects.create(
        user=verified_user,
        is_enabled=True,
        default_method=totp_method,
        otp_secret=totp_secret,
        backup_codes=["12345678", "87654321"],
    )

    return {"config": mfa_config, "secret": totp_secret}


@pytest_fixture
def email_config(verified_user: CustomUser, setup_mfa_methods) -> UserMFA:
    """Create email MFA configuration for testing."""
    email_method = MFAMethod.objects.get(
        name="email"
    )  # Ahora funcionará porque setup_mfa_methods lo crea

    return UserMFA.objects.create(
        user=verified_user, is_enabled=True, default_method=email_method
    )


@pytest_mark.django_db(transaction=True)
class TestMFAVerification:
    """Test suite for MFA verification functionality."""

    def test_verify_valid_totp(
        self, api_client, verified_user, temp_token, totp_config
    ):
        """Test verifying a valid TOTP code."""
        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        # Generate valid TOTP code
        totp = TOTP(totp_config["secret"])
        valid_code = totp.now()

        response = api_client.post(url, {"code": valid_code})

        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.data["data"]
        assert response.data["message"] == "MFA verification successful"

    def test_verify_valid_backup_code(
        self, api_client, verified_user, temp_token, totp_config
    ):
        """Test verifying a valid backup code."""
        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        backup_code = totp_config["config"].backup_codes[0]
        response = api_client.post(url, {"code": backup_code})

        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.data["data"]

        # Verify backup code was removed
        totp_config["config"].refresh_from_db()
        assert backup_code not in totp_config["config"].backup_codes

    def test_verify_invalid_totp(
        self, api_client, verified_user, temp_token, totp_config
    ):
        """Test verifying an invalid TOTP code."""
        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        response = api_client.post(url, {"code": "000000"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_code"

    def test_verify_valid_email_code(
        self, api_client, verified_user, temp_token, email_config
    ):
        """Test verifying a valid email verification code."""
        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        # Create verification code
        verification = MFAVerification.objects.create(
            user=verified_user,
            method=email_config.default_method,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
            session_key=temp_token,
        )

        response = api_client.post(url, {"code": verification.code})

        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.data["data"]

        # Verify code was marked as used
        verification.refresh_from_db()
        assert verification.is_verified

    def test_verify_expired_email_code(
        self, api_client, verified_user, temp_token, email_config
    ):
        """Test verifying an expired email verification code."""
        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        # Create expired verification
        verification = MFAVerification.objects.create(
            user=verified_user,
            method=email_config.default_method,
            code="123456",
            expires_at=timezone.now() - timedelta(minutes=1),
            session_key=temp_token,
        )

        response = api_client.post(url, {"code": verification.code})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_code"

    def test_verify_without_mfa_configured(self, api_client, verified_user, temp_token):
        """Test verification attempt without MFA configured."""
        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        response = api_client.post(url, {"code": "123456"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "MFA not configured" in str(response.data["errors"])

    def test_verify_with_permanent_token(self, api_client, verified_user, totp_config):
        """Test verification attempt with permanent token instead of temporary."""
        # Generate permanent token
        result = generate_token_for_user(
            user=verified_user,
            request=api_client.post("/").wsgi_request,
            is_temporary=False,
        )
        permanent_token = result.value["token"]

        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")

        totp = TOTP(totp_config["secret"])
        valid_code = totp.now()

        response = api_client.post(url, {"code": valid_code})

        # Should still work since MFA verification is allowed with permanent token
        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.data["data"]

    def test_verify_with_invalid_session_key(
        self,
        api_client: APIClient,
        verified_user: CustomUser,
        temp_token: str,
        email_config: UserMFA,
    ):
        """Test verification with invalid session key."""
        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        # Create verification with wrong session key
        verification = MFAVerification.objects.create(
            user=verified_user,
            method=email_config.default_method,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
            session_key="wrong_session_key",  # Different from temp_token
        )

        # Also create a verification with the correct session key but different code
        verification_valid_session = MFAVerification.objects.create(
            user=verified_user,
            method=email_config.default_method,
            code="789012",
            expires_at=timezone.now() + timedelta(minutes=10),
            session_key=temp_token,  # Correct session key
        )

        # Try to use code from wrong session
        response = api_client.post(url, {"code": verification.code})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_code"
        assert "Invalid or expired code" in str(response.data["data"])

        # Verify both verifications still exist and are not marked as verified
        verification.refresh_from_db()
        verification_valid_session.refresh_from_db()
        assert not verification.is_verified
        assert not verification_valid_session.is_verified

    def test_verify_used_backup_code(
        self,
        api_client: APIClient,
        verified_user: CustomUser,
        temp_token: str,
        totp_config: dict,
    ):
        """Test verification with an already used backup code."""
        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        # Use a backup code once
        backup_code = totp_config["config"].backup_codes[0]
        first_response = api_client.post(url, {"code": backup_code})
        assert first_response.status_code == status.HTTP_200_OK

        # Try to use the same backup code again
        second_response = api_client.post(url, {"code": backup_code})
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
        assert second_response.data["code"] == "invalid_code"

        # Verify the backup code was removed
        totp_config["config"].refresh_from_db()
        assert backup_code not in totp_config["config"].backup_codes

    def test_verify_with_disabled_mfa(
        self,
        api_client: APIClient,
        verified_user: CustomUser,
        temp_token: str,
        totp_config: dict,
    ):
        """Test verification when MFA is disabled."""
        # Disable MFA
        mfa_config = totp_config["config"]
        mfa_config.is_enabled = False
        mfa_config.save()

        url = reverse("accounts:verify-mfa")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        # Try to verify with TOTP code
        response = api_client.post(url, {"code": "123456"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "MFA not configured" in str(response.data["errors"])
