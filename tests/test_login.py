"""Test module for login functionality."""

from __future__ import annotations

from django.urls import reverse
from pytest import mark as pytest_mark
from rest_framework import status

from accounts.models.mfa_method import MFAMethod
from accounts.models.user_mfa import UserMFA
from utils.logger import logger


@pytest_mark.django_db
class TestLogin:
    """Test class for login functionality."""

    def test_successful_login(
        self,
        api_client,
        create_verified_user,
    ):
        """Test successful login with verified user."""
        # Prepare
        url = reverse("accounts:login")
        data = {
            "email": "test@test.com",
            "username": "test",
            "password": "test123",
        }

        # Execute
        response = api_client.post(
            url,
            data,
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        assert response.data["code"] == "success"
        assert "data" in response.data

        response_data = response.data.get("data", {})
        assert "user" in response_data
        assert "token" in response_data
        assert not response_data.get("requires_verification")

        user_data = response_data.get("user", {})
        assert user_data.get("email") == data["email"]
        assert user_data.get("is_verified") is True

    def test_successful_login_with_mfa(
        self,
        api_client,
        create_verified_user,
    ):
        """Test successful login that requires MFA."""
        # Get the existing email MFA method
        email_method = MFAMethod.objects.get(name="email")

        # Configure MFA for user
        UserMFA.objects.create(
            user=create_verified_user,
            is_enabled=True,
            default_method=email_method,
        )

        # Configure test data
        url = reverse("accounts:login")
        data = {"email": "test@test.com", "password": "test123"}

        # Execute
        response = api_client.post(url, data, format="json")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["code"] == "mfa_verification_required"

        response_data = response.data.get("data", {})
        assert "token" in response_data
        assert response_data.get("requires_verification") is True
        assert response_data.get("verification_type") == "mfa"
        assert response_data.get("mfa_method") == "email"

    def test_unverified_user_login(
        self,
        api_client,
        create_unverified_user,
    ):
        """Test login attempt with unverified user."""
        # Prepare
        url = reverse("accounts:login")
        data = {"email": "unverified@test.com", "password": "test123"}

        # Execute
        response = api_client.post(url, data, format="json")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "email_not_verified"

        response_data = response.data.get("data", {})
        assert "token" in response_data
        assert response_data.get("requires_verification") is True
        assert response_data.get("verification_type") == "email"

        user_data = response_data.get("user", {})
        assert user_data.get("is_verified") is False

    def test_invalid_credentials(
        self,
        api_client,
    ):
        """Test login with invalid credentials."""
        url = reverse("accounts:login")
        data = {
            "email": "nonexistent@test.com",
            "password": "wrong_password",
        }

        response = api_client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "errors" in response.data

    def test_missing_credentials(
        self,
        api_client,
    ):
        """Test login with missing credentials."""
        url = reverse("accounts:login")
        data = {
            "email": "test@test.com",
        }  # Missing password

        response = api_client.post(
            url,
            data,
            format="json",
        )

        logger.info(
            "response",
            extra={
                "response": response,
                # "data": response.data,
                # "status_code": response.status_code,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data

    def test_invalid_email_format(
        self,
        api_client,
    ):
        """Test login with invalid email format."""
        url = reverse("accounts:login")
        data = {
            "email": "invalid_email",
            "password": "test123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "errors" in response.data
