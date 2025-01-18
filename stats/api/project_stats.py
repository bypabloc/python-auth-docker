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
from shared.result_as_values import Result
from tasks.models import Task


@cached(ttl=3600, key_prefix="project_stats")
def get_project_statistics(
    project_id: int,
    user_id: int,
) -> Result[dict]:
    """Get cached project statistics."""
    try:
        # First verify project exists and user has access
        project = Project.objects.filter(
            id=project_id,
            members=user_id,
        ).first()
        if not project:
            return Result.fail(
                code="not_found",
                message="Project not found",
            )

        stats = {
            "total_tasks": Task.objects.filter(
                project_id=project_id,
            ).count(),
            "completed_tasks": Task.objects.filter(
                project_id=project_id,
                status="completed",
            ).count(),
            "pending_tasks": Task.objects.filter(
                project_id=project_id,
                status="pending",
            ).count(),
            "in_progress_tasks": Task.objects.filter(
                project_id=project_id,
                status="in_progress",
            ).count(),
        }

        return Result.ok(stats)

    except Exception as e:
        return Result.fail(
            code="error",
            message=str(e),
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get_stats(
    request: Request,
    project_id: int,
) -> CustomResponse:
    """Get project statistics."""
    result = get_project_statistics(
        project_id,
        request.user.id,
    )

    if result.is_error:
        return CustomResponse(
            ResponseConfig(
                errors={"error": result.error.message},
                status=404 if result.error.code == "not_found" else 500,
            )
        )

    return CustomResponse(
        ResponseConfig(
            data=result.value,
        )
    )
