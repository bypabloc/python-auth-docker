from __future__ import annotations

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from accounts.serializers.user import User as UserSerializer
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
    """Create a new user."""
    serializer = UserSerializer(data=request.data)
    if not serializer.is_valid():
        return CustomResponse(
            ResponseConfig(
                errors=serializer.errors.__dict__,
                status=400,
            ),
        )

    user = serializer.save()

    result_generate_token_for_user = generate_token_for_user(
        user=user,
        request=request,
        is_temporary=True,
    )
    if result_generate_token_for_user.is_error:
        return CustomResponse(
            ResponseConfig(
                errors=result_generate_token_for_user.value,
                status=500,
            ),
        )

    result_send_verification_email = send_verification_email(
        user=user,
        code_type="registration",
    )

    data_verify_email = result_send_verification_email.value

    token = result_generate_token_for_user.value["token"]

    response_data = {
        "message": (
            "User created successfully. "
            "Please check your email for verification code."
        ),
        "user": UserSerializer(user).data,
        "token": token,
    }

    if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
        response_data["verification"] = data_verify_email

    return CustomResponse(
        ResponseConfig(
            data=response_data,
            status=201,
        ),
    )
