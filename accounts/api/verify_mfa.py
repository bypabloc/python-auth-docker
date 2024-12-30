from __future__ import annotations

from enum import Enum

from django.utils import timezone
from pyotp import TOTP
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from accounts.models.custom_user import CustomUser
from accounts.models.mfa_method import MFAMethod
from accounts.models.mfa_verification import MFAVerification
from accounts.models.user_mfa import UserMFA
from accounts.serializers.mfa_verification import (
    MFAVerification as MFAVerificationSerializer,
)
from accounts.utils.generate_token_for_user import generate_token_for_user
from utils.custom_response import CustomResponse
from utils.custom_response import ResponseConfig
from utils.decorators.log_api import log_api


class TypeCodes(Enum):
    """Enum for OTP and backup code lengths."""

    otp = 6
    backup = 8


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_api
def post(
    request: Request,
) -> CustomResponse:
    """Verify MFA code during login."""
    serializer = MFAVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return CustomResponse(
            ResponseConfig(
                errors=serializer.errors.__dict__,
                status=400,
            ),
        )

    user = request.user
    data: dict = request.data
    code: str = str(data.get("code", ""))

    try:
        mfa_config: UserMFA = user.mfa_config
        method: MFAMethod = mfa_config.default_method

        verified_status = False
        verified_msg = ""
        if method.name == "otp":
            verified_status, verified_msg = _verify_otp(code, mfa_config)
        else:  # email
            verified_status, verified_msg = _verify_email(code, user, method)

        if not verified_status:
            return CustomResponse(
                ResponseConfig(
                    data={"error": verified_msg},
                    code="invalid_code",
                    status=400,
                ),
            )

        mfa_config.is_enabled = True
        mfa_config.save()

        result_generate_token_for_user = generate_token_for_user(
            user,
            request,
            is_temporary=False,
        )
        if result_generate_token_for_user.is_error:
            return CustomResponse(
                ResponseConfig(
                    errors={"error": "Failed to generate token"},
                    status=500,
                ),
            )

        token = result_generate_token_for_user.value["token"]

        return CustomResponse(
            ResponseConfig(
                data={"token": token},
                message="MFA verification successful",
            ),
        )
    except UserMFA.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "MFA not configured"},
                status=400,
            )
        )


def _verify_otp(
    code: str,
    mfa_config: UserMFA,
) -> tuple[bool, str | None]:
    """Verify OTP or backup code.

    Args:
        code: The OTP or backup code to verify
        mfa_config: The user's MFA configuration

    Returns:
        bool: True if verification succeeds, False otherwise
    """
    backup_codes = mfa_config.backup_codes or []
    if len(code) == TypeCodes.backup.value and code in backup_codes:
        backup_codes.remove(code)
        mfa_config.backup_codes = backup_codes
        mfa_config.save()
        return True, None

    if len(code) == TypeCodes.otp.value and mfa_config.otp_secret:
        totp = TOTP(mfa_config.otp_secret)
        return totp.verify(code), None

    return False, "Invalid code"


def _verify_email(
    code: str,
    user: CustomUser,
    method: MFAMethod,
) -> tuple[bool, str | None]:
    """Verify email verification code.

    Args:
        code: The verification code to check
        user: The user attempting verification
        method: The MFA method being used

    Returns:
        Union[Response, bool]: Either a Response object with an error,
        or True if verification succeeds
    """
    verification = MFAVerification.objects.filter(
        user=user,
        method=method,
        code=code,
        is_verified=False,
        expires_at__gt=timezone.now(),
    ).first()

    if not verification:
        return False, "Invalid or expired code"

    verification.is_verified = True
    verification.verified_at = timezone.now()
    verification.save()
    return True, None
