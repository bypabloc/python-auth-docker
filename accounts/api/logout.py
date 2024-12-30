from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from accounts.models.user_token import UserToken
from utils.custom_response import CustomResponse
from utils.custom_response import ResponseConfig
from utils.decorators.log_api import log_api
from utils.logger import logger


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_api
def post(
    request: Request,
) -> CustomResponse:
    """Logout the user."""
    if request.token_payload.get(
        "is_temporary",
        False,
    ):
        logger.error(
            "Invalid token type",
            extra={
                "request": request,
                "request.token_payload": request.token_payload,
            },
        )
        return CustomResponse(
            ResponseConfig(
                errors={
                    "error": "Invalid token type",
                },
                status=400,
                code="invalid_token",
            ),
        )

    UserToken.objects.filter(
        user=request.user,
        token=request.auth,
        is_valid=True,
    ).update(
        is_valid=False,
    )

    return CustomResponse(
        ResponseConfig(
            message="Logged out successfully",
            status=200,
        ),
    )
