# tasks/api/create_comment.py
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
from tasks.serializers import TaskCommentSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_api
def post(request: Request, project_id: int, task_id: int) -> CustomResponse:
    """Create a new comment on a task."""
    try:
        task = Task.objects.get(
            id=task_id,
            project_id=project_id,
            project__members=request.user,
            project__is_active=True,  # Added check for active project
        )
    except Task.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Task not found"},
                status=404,
            )
        )

    serializer = TaskCommentSerializer(data=request.data)
    if not serializer.is_valid():
        return CustomResponse(
            ResponseConfig(
                errors=dict(serializer.errors),
                status=400,
            )
        )

    comment = serializer.save(
        task=task,
        author=request.user,
    )

    # Invalidar caché de comentarios
    invalidate_cache_patterns(
        CachePatterns.TASK_COMMENTS,
        task_id=task_id,
    )

    return CustomResponse(
        ResponseConfig(
            data=TaskCommentSerializer(comment).data,
            message="Comment added successfully",
            status=201,
        )
    )
