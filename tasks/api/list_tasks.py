from __future__ import annotations

from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from projects.models import Project
from shared.custom_response import CustomResponse
from shared.custom_response import ResponseConfig
from shared.decorators.log_api import log_api
from tasks.models import Task
from tasks.serializers import TaskSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@log_api
def get(request: Request, project_id: int) -> CustomResponse:
    """List all tasks in a project."""
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

    # Get filter parameters
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    assignee = request.GET.get("assignee")
    is_active = request.GET.get("is_active", "true").lower() == "true"

    # Base queryset
    tasks = Task.objects.filter(project=project)

    # Apply filters
    if status:
        tasks = tasks.filter(status=status)
    if priority:
        tasks = tasks.filter(priority=priority)
    if assignee:
        if assignee == "me":
            tasks = tasks.filter(assignee=request.user)
        elif assignee == "unassigned":
            tasks = tasks.filter(assignee=None)
        else:
            tasks = tasks.filter(assignee__id=assignee)
    if is_active is not None:
        tasks = tasks.filter(is_active=is_active)

    # Search by title/description if provided
    search = request.GET.get("search")
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    serializer = TaskSerializer(tasks, many=True)
    return CustomResponse(
        ResponseConfig(
            data={
                "tasks": serializer.data,
                "total_count": tasks.count(),
            },
        )
    )
