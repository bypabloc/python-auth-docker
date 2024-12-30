from __future__ import annotations

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from accounts.models.verification_code import VerificationCode
from accounts.utils.email import send_verification_email
from utils.custom_response import CustomResponse
from utils.custom_response import ResponseConfig
from utils.decorators.log_api import log_api


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_api
def post(
    request: Request,
) -> CustomResponse:
    """Resend the verification code."""
    # Solo permitir reenvío con token temporal
    if not request.token_payload.get("is_temporary", False):
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Invalid token type"},
                status=400,
            ),
        )

    # Verificar el tipo de código requerido
    code_type = (
        VerificationCode.objects.filter(user=request.user, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not code_type:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "No pending verification found"},
                status=400,
            ),
        )

    # Generar y enviar nuevo código
    data_verify_email = send_verification_email(request.user, code_type.type)

    response_data = {
        "verification": None,
        "message": "New verification code sent successfully",
    }

    # Solo incluir el código en entorno local
    if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
        response_data["verification"] = data_verify_email

    return CustomResponse(
        ResponseConfig(
            data=response_data,
            status=200,
        ),
    )
