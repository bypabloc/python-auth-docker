from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from projects.serializers import ProjectSerializer
from shared.cache import cache as cache_instance
from shared.cache.utils import CachePatterns
from shared.cache.utils import invalidate_cache_patterns
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@log_api
def post(request: Request) -> CustomResponse:
    """Create a new project."""
    serializer = ProjectSerializer(
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

    # Create project with current user as owner
    project = serializer.save(owner=request.user)

    # Add owner as admin member
    project.project_members.create(
        user=request.user,
        role="admin",
    )

    # Invalidar tanto el listado de proyectos como las estadísticas del usuario
    invalidate_cache_patterns(
        CachePatterns.USER_PROJECTS,
        CachePatterns.USER_STATS,
        CachePatterns.PROJECT_STATS,
        user_id=request.user.id,
        project_id=project.id,
    )

    cache_instance.delete(f"user_stats_{request.user.id}")
    cache_instance.delete(f"user_projects_{request.user.id}")
    cache_instance.delete(f"project_stats_{project.id}")

    return CustomResponse(
        ResponseConfig(
            data=serializer.data,
            status=201,
            message="Project created successfully",
        )
    )
