from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from projects.models import Project
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api
from tasks.serializers import TaskSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_api
def post(request: Request, project_id: int) -> CustomResponse:
    """Create a new task in a project."""
    try:
        project = Project.objects.get(
            id=project_id,
            members=request.user,
            is_active=True,
        )
    except Project.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Project not found"},
                status=404,
            )
        )

    # Check if user is at least a member
    if not project.project_members.filter(user=request.user).exists():
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Permission denied"},
                status=403,
            )
        )

    serializer = TaskSerializer(data=request.data)
    if not serializer.is_valid():
        return CustomResponse(
            ResponseConfig(
                errors=dict(serializer.errors),
                status=400,
            )
        )

    # Create task
    task = serializer.save(
        project=project,
        created_by=request.user,
    )

    return CustomResponse(
        ResponseConfig(
            data=TaskSerializer(task).data,
            message="Task created successfully",
            status=201,
        )
    )
