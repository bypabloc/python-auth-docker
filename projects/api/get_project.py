from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from projects.models import Project
from projects.serializers import ProjectSerializer
from shared.cache.decorators import cached
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api


@cached(
    ttl=300,
    key_prefix="project_detail",
)
def get_project_detail(
    project_id: int,
    user_id: int,
) -> Project:
    """Cache project details."""
    return Project.objects.get(
        id=project_id,
        members=user_id,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get(request: Request, project_id: int) -> CustomResponse:
    """Get details of a specific project."""
    try:
        project = get_project_detail(
            project_id,
            request.user.id,
        )
    except Project.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Project not found"},
                status=404,
            )
        )

    serializer = ProjectSerializer(
        project,
        context={"request": request},
    )

    return CustomResponse(
        ResponseConfig(
            data=serializer.data,
        )
    )
