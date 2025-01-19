# tasks/api/get_comments.py

from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from shared.cache.decorators import cached
from shared.cache.utils import CachePatterns
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api
from tasks.models import Task
from tasks.models import TaskComment
from tasks.serializers import TaskCommentSerializer


@cached(
    ttl=60,
    key_pattern=CachePatterns.TASK_COMMENTS,
)
def get_task_comments(
    task_id: int,
    project_id: int,
) -> dict:
    """Get cached task comments.

    Args:
        task_id: ID of the task
        project_id: ID of the project
    """
    comments = TaskComment.objects.filter(task_id=task_id).order_by("-created_at")
    return {
        "comments": TaskCommentSerializer(comments, many=True).data,
        "total": comments.count(),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get(
    request: Request,
    project_id: int,
    task_id: int,
) -> CustomResponse:
    """Get task comments."""
    # First verify task exists and user has access
    try:
        Task.objects.get(
            id=task_id,
            project_id=project_id,
            project__members=request.user,
            project__is_active=True,  # Check for active project
        )
    except Task.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Task not found"},
                status=404,
            )
        )

    comments_data = get_task_comments(
        task_id=task_id,
        project_id=project_id,
    )

    return CustomResponse(
        ResponseConfig(
            data=comments_data,
        )
    )
