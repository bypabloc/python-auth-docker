from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from accounts.models.mfa_method import MFAMethod
from accounts.serializers.mfa_method import MFAMethod as MFAMethodSerializer
from shared.cache.decorators import cached
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api


@cached(ttl=3600)
def get_mfa_methods() -> QuerySet[MFAMethod]:
    """List all active MFA methods."""
    return MFAMethod.objects.filter(is_active=True)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get(request: Request) -> CustomResponse:
    """List all active MFA methods."""
    queryset = get_mfa_methods()
    serializer = MFAMethodSerializer(queryset, many=True)
    serializer_data: dict[str, Any] = {
        "methods": serializer.data,
    }
    return CustomResponse(
        ResponseConfig(
            data=serializer_data,
        ),
    )
