from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api
from tasks.models import Task


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@log_api
def delete(request: Request, project_id: int, task_id: int) -> CustomResponse:
    """Delete a task."""
    try:
        task = Task.objects.get(
            id=task_id,
            project_id=project_id,
            project__members=request.user,
        )
    except Task.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Task not found"},
                status=404,
            )
        )

    # Check if user has permission to delete
    if (
        request.user != task.created_by
        and not task.project.project_members.filter(
            user=request.user, role="admin"
        ).exists()
    ):
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Permission denied"},
                status=403,
            )
        )

    # Delete task and all related comments
    task.delete()

    return CustomResponse(
        ResponseConfig(
            message="Task deleted successfully",
        )
    )
