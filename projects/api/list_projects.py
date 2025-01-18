from __future__ import annotations

from django.db.models import QuerySet
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from projects.models import Project
from projects.serializers import ProjectSerializer
from shared.cache.decorators import cached
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api


@cached(
    ttl=300,
    key_prefix="user_projects",
)
def get_user_projects(
    user_id: int,
) -> QuerySet[Project]:
    """Cache projects per user."""
    return Project.objects.filter(
        members=user_id,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get(
    request: Request,
) -> CustomResponse:
    """List all projects for the current user."""
    projects = get_user_projects(request.user.id)
    serializer = ProjectSerializer(
        projects,
        many=True,
        context={
            "request": request,
        },
    )

    return CustomResponse(
        ResponseConfig(
            data={"projects": serializer.data},
        )
    )
