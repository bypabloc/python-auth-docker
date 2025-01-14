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


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@log_api
def put(request: Request, project_id: int) -> CustomResponse:
    """Update a specific project."""
    try:
        project = Project.objects.get(
            id=project_id,
            members=request.user,
        )
    except Project.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Project not found"},
                status=404,
            )
        )

    # Check if user is admin
    if not project.project_members.filter(
        user=request.user,
        role="admin",
    ).exists():
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Permission denied"},
                status=403,
            )
        )

    serializer = ProjectSerializer(
        project,
        data=request.data,
        context={"request": request},
    )

    if not serializer.is_valid():
        return CustomResponse(
            ResponseConfig(
                errors=dict(serializer.errors),
                status=400,
            )
        )

    serializer.save()

    return CustomResponse(
        ResponseConfig(
            data=serializer.data,
            message="Project updated successfully",
        )
    )
