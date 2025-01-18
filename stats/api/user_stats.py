from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from projects.models import Project
from shared.cache.decorators import cached
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api
from tasks.models import Task


@cached(ttl=300, key_prefix="user_stats")
def get_user_statistics(user_id: int) -> dict:
    """Get cached user statistics."""
    return {
        "total_projects": Project.objects.filter(members=user_id).count(),
        "owned_projects": Project.objects.filter(owner_id=user_id).count(),
        "assigned_tasks": Task.objects.filter(assignee_id=user_id).count(),
        "created_tasks": Task.objects.filter(created_by_id=user_id).count(),
        "completed_tasks": Task.objects.filter(
            assignee_id=user_id, status="completed"
        ).count(),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get_stats(request: Request) -> CustomResponse:
    """Get user statistics."""
    stats = get_user_statistics(request.user.id)

    return CustomResponse(
        ResponseConfig(
            data=stats,
        )
    )
