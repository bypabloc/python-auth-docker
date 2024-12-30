from __future__ import annotations

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from accounts.models.user_token import UserToken
from accounts.models.verification_code import VerificationCode
from accounts.serializers.user import User as UserSerializer
from accounts.serializers.verification_code import (
    VerificationCode as VerificationCodeSerializer,
)
from accounts.utils.generate_token_for_user import generate_token_for_user
from utils.custom_response import CustomResponse
from utils.custom_response import ResponseConfig
from utils.decorators.log_api import log_api


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_api
def post(
    request: Request,
) -> CustomResponse:
    """Verify the verification code."""
    # Check if token is temporary
    if not request.token_payload.get("is_temporary", False):
        return CustomResponse(
            ResponseConfig(
                code="invalid_token_type",
                status=400,
                message="Invalid token type",
            ),
        )

    serializer = VerificationCodeSerializer(
        data={
            "code": request.data.get("code"),
            "email": request.token_payload["email"],
        }
    )

    if not serializer.is_valid():
        return CustomResponse(
            ResponseConfig(
                errors=serializer.errors.__dict__,
                status=400,
            ),
        )

    code = request.data.get("code")

    user = request.user
    verification = (
        VerificationCode.objects.filter(
            user=user,
            code=code,
            is_used=False,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )

    if not verification:
        return CustomResponse(
            ResponseConfig(
                code="invalid_verification_code",
                status=400,
                message="Invalid or expired verification code",
            ),
        )

    # Mark code as used
    verification.is_used = True
    verification.save()

    # Handle registration verification
    if verification.type == "registration":
        user.is_verified = True
        user.save()

    # Generate permanent token
    token, user_token = generate_token_for_user(user, request, is_temporary=False)

    # Invalidate temporary token
    UserToken.objects.filter(user=user, token=request.auth, is_valid=True).update(
        is_valid=False
    )

    if not user.is_verified:
        user.is_verified = True
        user.save()

    # delete all verification codes for the user
    VerificationCode.objects.filter(user=user).delete()

    return CustomResponse(
        ResponseConfig(
            message="Verification successful",
            data={
                "token": token,
                "user": UserSerializer(user).data,
            },
        ),
    )
