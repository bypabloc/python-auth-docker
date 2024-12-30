from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from accounts.models.mfa_verification import MFAVerification
from accounts.models.user_mfa import UserMFA
from accounts.serializers.login import Login as LoginSerializer
from accounts.serializers.user import User as UserSerializer
from accounts.utils.email import generate_verification_code
from accounts.utils.email import send_verification_email
from accounts.utils.generate_token_for_user import generate_token_for_user
from utils.custom_response import CustomResponse
from utils.custom_response import ResponseConfig
from utils.decorators.log_api import log_api


@api_view(["POST"])
@permission_classes([AllowAny])
@log_api
def post(
    request: Request,
) -> CustomResponse:
    """Login the user."""
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return CustomResponse(
            ResponseConfig(
                errors=serializer.errors.__dict__,
                status=400,
            )
        )

    email = request.data.get("email")
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(
        username=email or username,
        password=password,
    )

    if not user:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Invalid credentials"},
                status=401,
            ),
        )

    # Check if user is verified
    if not user.is_verified:
        # For unverified users, send verification code and temporary token
        token, _ = generate_token_for_user(user, request, is_temporary=True)
        data_verify_email = send_verification_email(user, "login")

        response_data = {
            "user": UserSerializer(user).data,
            "token": token,
            "requires_verification": True,
            "verification_type": "email",
        }

        if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
            response_data["verification"] = data_verify_email

        return CustomResponse(
            ResponseConfig(
                data=response_data,
                code="email_not_verified",
                status=400,
                message="Please verify your email first.",
            ),
        )

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

            return CustomResponse(
                ResponseConfig(
                    data=response_data,
                    code="mfa_verification_required",
                ),
            )

    except UserMFA.DoesNotExist:
        pass

    # Si no hay MFA o no está habilitado, generar token permanente
    token, user_token = generate_token_for_user(user, request, is_temporary=False)

    return CustomResponse(
        ResponseConfig(
            data={
                "user": UserSerializer(user).data,
                "token": token,
                "requires_verification": False,
            },
            message="Login successful",
        ),
    )
