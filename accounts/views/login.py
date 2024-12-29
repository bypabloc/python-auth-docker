from __future__ import annotations

from datetime import timedelta
from typing import ClassVar

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models.mfa_verification import MFAVerification
from accounts.models.user_mfa import UserMFA
from accounts.serializers.login import Login as LoginSerializer
from accounts.serializers.user import User as UserSerializer
from accounts.utils.email import generate_verification_code
from accounts.utils.email import send_verification_email
from accounts.utils.generate_token_for_user import generate_token_for_user


class LoginView(APIView):
    """Handle user login."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [AllowAny]

    def post(self, request: Request) -> Response:
        """Login the user."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = request.data.get("email")
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(
            username=email or username,
            password=password,
        )

        if not user:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Check if user is verified
        if not user.is_verified:
            # For unverified users, send verification code and temporary token
            token, _ = generate_token_for_user(user, request, is_temporary=True)
            data_verify_email = send_verification_email(user, "login")

            response_data = {
                "message": "Please verify your email first.",
                "user": UserSerializer(user).data,
                "token": token,
                "requires_verification": True,
                "verification_type": "email",
            }

            if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
                response_data["verification"] = data_verify_email

            return Response(response_data)

        # Check if MFA is enabled
        try:
            mfa_config = user.mfa_config

            if mfa_config.is_enabled:
                # Generate temporary token for MFA
                token, _ = generate_token_for_user(user, request, is_temporary=True)

                response_data = {
                    "message": "MFA verification required",
                    "token": token,
                    "requires_verification": True,
                    "verification_type": "mfa",
                    "mfa_method": mfa_config.default_method.name,
                }

                if mfa_config.default_method.name == "email":
                    # Generate verification code
                    code = generate_verification_code()

                    # Create verification record
                    verification = MFAVerification.objects.create(
                        user=user,
                        method=mfa_config.default_method,
                        code=code,
                        expires_at=timezone.now() + timedelta(minutes=10),
                        session_key=token,
                    )

                    # Send email with code
                    send_verification_email(user, "mfa")

                    # Include verification info in response if enabled
                    if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
                        response_data["verification"] = {
                            "code": code,
                            "expires_at": verification.expires_at,
                        }

                return Response(response_data)

        except UserMFA.DoesNotExist:
            pass

        # Si no hay MFA o no está habilitado, generar token permanente
        token, user_token = generate_token_for_user(user, request, is_temporary=False)

        return Response(
            {
                "message": "Login successful",
                "user": UserSerializer(user).data,
                "token": token,
                "requires_verification": False,
            }
        )
