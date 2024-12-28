from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models.verification_code import VerificationCode
from accounts.utils.email import send_verification_email


class ResendCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Solo permitir reenvío con token temporal
        if not request.token_payload.get("is_temporary", False):
            return Response(
                {"error": "Invalid token type"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar el tipo de código requerido
        code_type = (
            VerificationCode.objects.filter(user=request.user, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not code_type:
            return Response(
                {"error": "No pending verification found"},
                status=status.HTTP_400_BAD_REQUEST,
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

        return Response(response_data)
