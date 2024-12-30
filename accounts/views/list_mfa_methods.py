from __future__ import annotations

from typing import Any

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from accounts.models.mfa_method import MFAMethod
from accounts.serializers.mfa_method import MFAMethod as MFAMethodSerializer
from utils.custom_response import CustomResponse
from utils.custom_response import ResponseConfig
from utils.decorators.log_api import log_api


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get(request: Request) -> CustomResponse:
    """List all active MFA methods."""
    queryset = MFAMethod.objects.filter(is_active=True)
    serializer = MFAMethodSerializer(queryset, many=True)
    serializer_data: dict[str, Any] = {
        "methods": serializer.data,
    }
    return CustomResponse(
        ResponseConfig(
            data=serializer_data,
        ),
    )
