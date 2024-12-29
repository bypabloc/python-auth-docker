from typing import ClassVar

from django.utils import timezone
from pyotp import TOTP
from rest_framework import status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models.custom_user import CustomUser
from accounts.models.mfa_method import MFAMethod
from accounts.models.mfa_verification import MFAVerification
from accounts.models.user_mfa import UserMFA
from accounts.serializers.mfa_verification import (
    MFAVerification as MFAVerificationSerializer,
)
from accounts.utils.generate_token_for_user import generate_token_for_user


class VerifyMFAView(APIView):
    """Handle MFA verification during login process."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Verify MFA code during login."""
        serializer = MFAVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        data: dict = request.data
        code: str = str(data.get("code", ""))

        try:
            mfa_config: UserMFA = user.mfa_config
            method: MFAMethod = mfa_config.default_method

            if method.name == "otp":
                verified = self._verify_otp(code, mfa_config)
            else:  # email
                verified = self._verify_email(code, user, method)

            if not isinstance(verified, bool):
                return verified  # Return error response directly

            if verified:
                # Enable MFA and generate permanent token
                mfa_config.is_enabled = True
                mfa_config.save()

                token, _ = generate_token_for_user(user, request, is_temporary=False)
                return Response(
                    {"message": "MFA verification successful", "token": token}
                )

            return Response(
                {"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST
            )

        except UserMFA.DoesNotExist:
            return Response(
                {"error": "MFA not configured"}, status=status.HTTP_400_BAD_REQUEST
            )

    def _verify_otp(self, code: str, mfa_config: UserMFA) -> bool:
        """Verify OTP or backup code.

        Args:
            code: The OTP or backup code to verify
            mfa_config: The user's MFA configuration

        Returns:
            bool: True if verification succeeds, False otherwise
        """
        backup_codes = mfa_config.backup_codes or []
        if len(code) == 8 and code in backup_codes:
            backup_codes.remove(code)
            mfa_config.backup_codes = backup_codes
            mfa_config.save()
            return True

        if len(code) == 6 and mfa_config.otp_secret:
            totp = TOTP(mfa_config.otp_secret)
            return totp.verify(code)

        return False

    def _verify_email(
        self, code: str, user: CustomUser, method: MFAMethod
    ) -> Response | bool:
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
            return Response(
                {"error": "Invalid or expired code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification.is_verified = True
        verification.verified_at = timezone.now()
        verification.save()
        return True
