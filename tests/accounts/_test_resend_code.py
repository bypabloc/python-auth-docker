from __future__ import annotations

from datetime import timedelta

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
def temp_token(unverified_user: CustomUser, api_client: APIClient) -> str:
    """Generate a temporary token for testing."""
    result = generate_token_for_user(
        user=unverified_user,
        request=api_client.post("/").wsgi_request,
        is_temporary=True,
    )
    return result.value["token"]


@pytest_mark.django_db
class TestResendCode:
    """Test suite for code resend functionality."""

    def test_successful_resend(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
        temp_token: str,
    ):
        """Test successful code resend."""
        # Create initial verification code
        VerificationCode.objects.create(
            user=unverified_user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
            type="registration",
        )

        url = reverse("accounts:resend-code")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert "verification" in response.data["data"]
        assert (
            response.data["data"]["message"]
            == "New verification code sent successfully"
        )

        # Verify new code was created
        latest_code = VerificationCode.objects.filter(
            user=unverified_user,
            is_used=False,
        ).latest("created_at")

        assert latest_code is not None
        assert latest_code.code == response.data["data"]["verification"]["code"]

    def test_resend_with_permanent_token(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
    ):
        """Test resend attempt with permanent token instead of temporary."""
        # Create initial verification code
        VerificationCode.objects.create(
            user=unverified_user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
            type="registration",
        )

        # Generate permanent token
        result = generate_token_for_user(
            user=unverified_user,
            request=api_client.post("/").wsgi_request,
            is_temporary=False,
        )
        permanent_token = result.value["token"]

        url = reverse("accounts:resend-code")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {permanent_token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid token type" in str(response.data["errors"])

    def test_resend_without_pending_verification(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
        temp_token: str,
    ):
        """Test resend attempt when there's no pending verification."""
        url = reverse("accounts:resend-code")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No pending verification found" in str(response.data["errors"])

    def test_resend_with_expired_code(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
        temp_token: str,
    ):
        """Test resend with expired verification code."""
        # Create expired verification code
        VerificationCode.objects.create(
            user=unverified_user,
            code="123456",
            expires_at=timezone.now() - timedelta(minutes=1),
            type="registration",
        )

        url = reverse("accounts:resend-code")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert "verification" in response.data["data"]
        assert (
            response.data["data"]["message"]
            == "New verification code sent successfully"
        )

        # Verify new code was created with future expiration
        latest_code = VerificationCode.objects.filter(
            user=unverified_user,
            is_used=False,
        ).latest("created_at")

        assert latest_code is not None
        assert latest_code.expires_at > timezone.now()

    def test_resend_with_used_code(
        self,
        api_client: APIClient,
        unverified_user: CustomUser,
        temp_token: str,
    ):
        """Test resend with used verification code."""
        # Create used verification code
        VerificationCode.objects.create(
            user=unverified_user,
            code="123456",
            expires_at=timezone.now() + timedelta(minutes=10),
            type="registration",
            is_used=True,
        )

        url = reverse("accounts:resend-code")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {temp_token}")

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No pending verification found" in str(response.data["errors"])
