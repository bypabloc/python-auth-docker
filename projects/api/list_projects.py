from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from projects.models import Project
from projects.serializers import ProjectSerializer
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get(request: Request) -> CustomResponse:
    """List all projects for the current user."""
    projects = Project.objects.filter(members=request.user)
    serializer = ProjectSerializer(
        projects,
        many=True,
        context={"request": request},
    )

    return CustomResponse(
        ResponseConfig(
            data={"projects": serializer.data},
        )
    )
