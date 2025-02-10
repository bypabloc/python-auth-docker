from __future__ import annotations

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from accounts.models.magic_link import MagicLink
from accounts.serializers.user import User as UserSerializer
from accounts.utils.generate_token_for_user import generate_token_for_user
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api


@api_view(["POST"])
@permission_classes([AllowAny])
@log_api
def verify_magic_link(request: Request) -> CustomResponse:
    """Verify a magic link token.

    Expects:
        - token: The magic link token
        - email: The user's email
    """
    token = request.data.get("token")
    email = request.data.get("email")

    if not token or not email:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Token and email are required"},
                status=400,
            )
        )

    try:
        magic_link = MagicLink.objects.get(
            token=token,
            user__email=email,
            is_used=False,
            expires_at__gt=timezone.now(),
        )
    except MagicLink.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Invalid or expired magic link"},
                status=400,
            )
        )

    user = magic_link.user

    # Mark the magic link as used
    magic_link.is_used = True
    magic_link.save()

    # Verify the user if not already verified
    if not user.is_verified:
        user.is_verified = True
        user.save()

    # Generate authentication token
    result_generate_token = generate_token_for_user(
        user=user,
        request=request,
        is_temporary=False if user.has_password else True,
    )

    if result_generate_token.is_error:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Failed to generate token"},
                status=500,
            )
        )

    token = result_generate_token.value["token"]

    response_data = {
        "token": token,
        "user": UserSerializer(user).data,
    }

    return CustomResponse(
        ResponseConfig(
            message="Magic link verified successfully",
            data=response_data,
        )
    )
