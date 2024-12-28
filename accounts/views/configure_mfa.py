import base64
import io
from datetime import timedelta

import pyotp
import qrcode
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import MFAVerification, UserMFA
from accounts.serializers.user_mfa import UserMFA as UserMFASerializer
from accounts.utils.email import generate_verification_code


class ConfigureMFAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtener configuración actual de MFA"""
        try:
            mfa_config = request.user.mfa_config
            return Response(UserMFASerializer(mfa_config).data)
        except UserMFA.DoesNotExist:
            return Response({"is_enabled": False, "default_method": None})

    def post(self, request):
        """Configurar MFA"""
        serializer = UserMFASerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        method = serializer.validated_data["default_method"]
        mfa_config, created = UserMFA.objects.get_or_create(
            user=request.user, defaults={"is_enabled": False}
        )

        # Configurar según el método
        if method.name == "otp":
            if not mfa_config.otp_secret:
                # Generar nuevo secreto OTP si no existe
                mfa_config.otp_secret = pyotp.random_base32()
                # Generar códigos de respaldo
                mfa_config.backup_codes = [pyotp.random_base32()[:8] for _ in range(5)]

            totp = pyotp.TOTP(mfa_config.otp_secret)
            provisioning_uri = totp.provisioning_uri(
                request.user.email, issuer_name="app"
            )

            # Crear QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            # Crear imagen
            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Convertir a base64
            buffer = io.BytesIO()
            qr_image.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()

            response_data = {
                "secret": mfa_config.otp_secret,
                "provisioning_uri": provisioning_uri,
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "backup_codes": mfa_config.backup_codes,
            }
        else:  # email
            # Generar y enviar código de verificación
            code = generate_verification_code()

            # Invalidar verificaciones anteriores
            MFAVerification.objects.filter(
                user=request.user, method=method, is_verified=False
            ).delete()

            # Crear nueva verificación
            verification = MFAVerification.objects.create(
                user=request.user,
                method=method,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=10),
                session_key=f"mfa_setup_{request.user.id}",
            )

            # Enviar email con el código

            response_data = {"message": "Verification code sent to your email"}

            if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
                response_data["verification"] = {
                    "code": code,
                    "expires_at": verification.expires_at,
                }

        # Actualizar configuración
        mfa_config.default_method = method
        mfa_config.save()

        # Actualizar estado MFA del usuario
        request.user.has_mfa = True
        request.user.save()

        return Response(response_data)
