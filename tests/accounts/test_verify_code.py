from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.urls import reverse
from django.utils import timezone
from faker import Faker
from pytest import fixture as pytest_fixture
from pytest import mark as pytest_mark
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models.custom_user import CustomUser
from accounts.models.verification_code import VerificationCode
from accounts.utils.generate_token_for_user import generate_token_for_user

fake = Faker()


@pytest_fixture
def api_client():
    """Create a test client."""
    return APIClient()


@pytest_fixture
def unverified_user():
    """Create an unverified user for testing."""
    user = CustomUser.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password="testpass123",
    )
    return user


@pytest_fixture
def verification_code(unverified_user: CustomUser) -> dict[str, Any]:
    """Create a verification code for testing."""
    code = "123456"
    expires_at = timezone.now() + timedelta(minutes=10)

    verification = VerificationCode.objects.create(
        user=unverified_user,
        code=code,
        expires_at=expires_at,
        type="registration",
    )

    return {
        "code": code,
        "verification": verification,
        "expires_at": expires_at,
    }


@pytest_fixture
def temp_token(unverified_user: CustomUser, api_client: APIClient) -> str:
    """Generate a temporary token for testing."""
    result = generate_token_for_user(
        user=unverified_user,
        request=api_client.post("/").wsgi_request,
        is_temporary=True,
    )
    return result.value["token"]


@pytest_mark.django_db
class TestVerifyCode:
    """Test suite for code verification functionality."""

    def test_successful_verification(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
        verification_code: dict[str, Any],
        temp_token: str,
    ):
        """Test successful code verification."""
        url = reverse("accounts:verify-code")

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")
        response = api_client.post(
            url,
            {
                "code": verification_code["code"],
                "email": unverified_user.email,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.data["data"]
        assert response.data["data"]["user"][
            "is_verified"
        ]  # El usuario debe estar verificado después de una verificación exitosa

        # Verify user status was updated
        unverified_user.refresh_from_db()
        assert unverified_user.is_verified

        # All verification codes should be deleted
        assert not VerificationCode.objects.filter(user=unverified_user).exists()

    def test_verification_with_invalid_code(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
        temp_token: str,
    ):
        """Test verification attempt with invalid code."""
        url = reverse("accounts:verify-code")

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")
        response = api_client.post(
            url,
            {
                "code": "999999",
                "email": unverified_user.email,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_verification_code"

        # Verify user status wasn't updated
        unverified_user.refresh_from_db()
        assert not unverified_user.is_verified

    def test_verification_with_expired_code(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
        verification_code: dict[str, Any],
        temp_token: str,
    ):
        """Test verification attempt with expired code."""
        # Set verification code as expired
        verification = verification_code["verification"]
        verification.expires_at = timezone.now() - timedelta(minutes=1)
        verification.save()

        url = reverse("accounts:verify-code")

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")
        response = api_client.post(
            url,
            {
                "code": verification_code["code"],
                "email": unverified_user.email,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_verification_code"

        # Verify user status wasn't updated
        unverified_user.refresh_from_db()
        assert not unverified_user.is_verified

    def test_verification_with_used_code(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
        verification_code: dict[str, Any],
        temp_token: str,
    ):
        """Test verification attempt with already used code."""
        # Mark code as used
        verification = verification_code["verification"]
        verification.is_used = True
        verification.save()

        url = reverse("accounts:verify-code")

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")
        response = api_client.post(
            url,
            {
                "code": verification_code["code"],
                "email": unverified_user.email,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_verification_code"

        # Verify user status wasn't updated
        unverified_user.refresh_from_db()
        assert not unverified_user.is_verified

    def test_verification_with_permanent_token(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
        verification_code: dict[str, Any],
    ):
        """Test verification attempt with permanent token instead of temporary."""
        # Generate permanent token
        result = generate_token_for_user(
            user=unverified_user,
            request=api_client.post("/").wsgi_request,
            is_temporary=False,
        )
        permanent_token = result.value["token"]

        url = reverse("accounts:verify-code")

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")
        response = api_client.post(
            url,
            {
                "code": verification_code["code"],
                "email": unverified_user.email,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "invalid_token_type"

        # Verify user status wasn't updated
        unverified_user.refresh_from_db()
        assert not unverified_user.is_verified
