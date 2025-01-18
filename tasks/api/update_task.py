from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from shared.cache.utils import CachePatterns
from shared.cache.utils import invalidate_cache_patterns
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api
from tasks.models import Task
from tasks.serializers import TaskSerializer


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@log_api
def put(request: Request, project_id: int, task_id: int) -> CustomResponse:
    """Update a task."""
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

    # Check if user has permission to update
    if (
        request.user not in {task.created_by, task.assignee}
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

    serializer = TaskSerializer(task, data=request.data, partial=True)
    if not serializer.is_valid():
        return CustomResponse(
            ResponseConfig(
                errors=dict(serializer.errors),
                status=400,
            )
        )

    task = serializer.save()

    # Invalidar múltiples patrones de caché
    invalidate_cache_patterns(
        CachePatterns.PROJECT_TASKS,
        CachePatterns.TASK_DETAIL,
        CachePatterns.PROJECT_STATS,
        project_id=project_id,
        task_id=task_id,
    )

    # Si hay cambio de asignación, invalidar stats de usuarios
    if "assignee" in request.data:
        invalidate_cache_patterns(
            CachePatterns.USER_STATS, user_id=request.data["assignee"]
        )

    return CustomResponse(
        ResponseConfig(
            data=TaskSerializer(task).data,
            message="Task updated successfully",
        )
    )
