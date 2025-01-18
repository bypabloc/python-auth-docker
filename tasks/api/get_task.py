from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from shared.cache.decorators import cached
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api
from tasks.models import Task
from tasks.serializers import TaskCommentSerializer
from tasks.serializers import TaskSerializer


@cached(ttl=60, key_prefix="task_detail")
def get_task_detail(task_id: int, project_id: int, user_id: int) -> Task:
    """Cache task details.

    Args:
        task_id: ID of the task to retrieve
        project_id: ID of the project the task belongs to
        user_id: ID of the user requesting the task

    Returns:
        Task: The requested task object
    """
    return Task.objects.get(
        id=task_id,
        project_id=project_id,
        project__members=user_id,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get(request: Request, project_id: int, task_id: int) -> CustomResponse:
    """Get task details."""
    try:
        task = get_task_detail(
            task_id=task_id,
            project_id=project_id,
            user_id=request.user.id,
        )
    except Task.DoesNotExist:
        return CustomResponse(
            ResponseConfig(
                errors={"error": "Task not found"},
                status=404,
            )
        )

    # Get comments if requested
    include_comments = request.GET.get("include_comments", "").lower() == "true"
    response_data = TaskSerializer(task).data

    if include_comments:
        comments = task.comments.all()
        response_data["comments"] = TaskCommentSerializer(comments, many=True).data

    return CustomResponse(
        ResponseConfig(
            data=response_data,
        )
    )
