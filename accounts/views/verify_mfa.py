import pyotp
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import MFAVerification, UserMFA
from accounts.serializers.mfa_verification import (
    MFAVerification as MFAVerificationSerializer,
)
from accounts.utils.generate_token_for_user import generate_token_for_user


class VerifyMFAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Verificar código MFA durante login"""
        serializer = MFAVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        code = serializer.validated_data["code"]

        try:
            mfa_config = user.mfa_config
            method = mfa_config.default_method

            if method.name == "otp":
                # Verificar si es un código de respaldo
                if (
                    len(code) == 8 and code in mfa_config.backup_codes
                ):  # Agregamos verificación de longitud
                    mfa_config.backup_codes.remove(code)
                    mfa_config.save()
                    verified = True
                elif len(code) == 6:  # Si es código OTP
                    # Verificar código TOTP
                    totp = pyotp.TOTP(mfa_config.otp_secret)
                    verified = totp.verify(code)
                else:
                    verified = False
            else:  # email
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
                verified = True

            if verified:
                # Enable MFA
                mfa_config.is_enabled = True
                mfa_config.save()

                # Generar token permanente
                token, _ = generate_token_for_user(user, request, is_temporary=False)
                return Response(
                    {"message": "MFA verification successful", "token": token}
                )
            else:
                return Response(
                    {"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST
                )

        except UserMFA.DoesNotExist:
            return Response(
                {"error": "MFA not configured"}, status=status.HTTP_400_BAD_REQUEST
            )
