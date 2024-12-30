from __future__ import annotations

from base64 import b64encode as base64_b64encode
from datetime import timedelta
from io import BytesIO as io_BytesIO
from typing import Any

from django.conf import settings
from django.utils import timezone
from pyotp import TOTP
from pyotp import random_base32 as pyotp_random_base32
from qrcode import QRCode as qrcode_QRCode
from qrcode import constants as qrcode_constants
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from accounts.models.mfa_verification import MFAVerification
from accounts.models.user_mfa import UserMFA
from accounts.serializers.user_mfa import UserMFASerializer
from accounts.utils.email import generate_verification_code
from utils.custom_response import CustomResponse
from utils.custom_response import ResponseConfig
from utils.decorators.log_api import log_api


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def configure_mfa(request: Request) -> CustomResponse:
    """Handle MFA configuration.

    Supports both GET (retrieve configuration) and POST (update configuration) methods.
    """
    if request.method == "GET":
        return get_mfa_config(request)
    return post_mfa_config(request)


@log_api
def get_mfa_config(request: Request) -> CustomResponse:
    """Get current MFA configuration."""
    try:
        mfa_config = request.user.mfa_config
        serializer = UserMFASerializer(mfa_config)
        serializer_data: dict[str, Any] = dict(serializer.data)
        return CustomResponse(
            ResponseConfig(
                data=serializer_data,
            ),
        )
    except UserMFA.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                data={
                    "is_enabled": False,
                    "default_method": None,
                },
            ),
        )


@log_api
def post_mfa_config(request: Request) -> CustomResponse:
    """Configure MFA settings."""
    serializer = UserMFASerializer(data=request.data)
    if not serializer.is_valid():
        return CustomResponse(
            ResponseConfig(
                errors=serializer.errors.__dict__,
                status=400,
            ),
        )

    method = serializer.validated_data.get("default_method")
    mfa_config, created = UserMFA.objects.get_or_create(
        user=request.user,
        defaults={
            "is_enabled": False,
        },
    )

    # Configurar según el método
    if method.name == "otp":
        if not mfa_config.otp_secret:
            # Generar nuevo secreto OTP si no existe
            mfa_config.otp_secret = pyotp_random_base32()
            # Generar códigos de respaldo
            mfa_config.backup_codes = [pyotp_random_base32()[:8] for _ in range(5)]

        totp = TOTP(mfa_config.otp_secret)
        provisioning_uri = totp.provisioning_uri(request.user.email, issuer_name="app")

        # Crear QR
        qr = qrcode_QRCode(
            version=1,
            error_correction=qrcode_constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Crear imagen
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Convertir a base64
        buffer = io_BytesIO()
        qr_image.save(
            buffer,
            format="PNG",
        )
        qr_base64 = base64_b64encode(buffer.getvalue()).decode()

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
            user=request.user,
            method=method,
            is_verified=False,
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
        response_data = {
            "message": "Verification code sent to your email",
            "verification": None,
        }

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

    return CustomResponse(
        ResponseConfig(
            data=response_data,
        ),
    )
