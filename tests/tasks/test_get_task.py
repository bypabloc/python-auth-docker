# tests/tasks/test_get_task.py
from __future__ import annotations

from django.urls import reverse
from faker import Faker
from pytest import fixture as pytest_fixture
from pytest import mark as pytest_mark
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import CustomUser
from accounts.utils.generate_token_for_user import generate_token_for_user
from projects.models import Project
from tasks.models import Task
from tasks.models import TaskComment

fake = Faker()


@pytest_fixture
def api_client() -> APIClient:
    """Create a test client."""
    return APIClient()


@pytest_fixture
def user() -> CustomUser:
    """Create a verified user for testing."""
    user = CustomUser.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password="testpass123",
    )
    user.is_verified = True
    user.save()
    return user


@pytest_fixture
def token(user: CustomUser, api_client: APIClient) -> str:
    """Generate a token for testing."""
    result = generate_token_for_user(
        user=user,
        request=api_client.post("/").wsgi_request,
        is_temporary=False,
    )
    return result.value["token"]


@pytest_fixture
def project(user: CustomUser) -> Project:
    """Create a test project."""
    project = Project.objects.create(
        name=fake.company(),
        description=fake.text(),
        owner=user,
        is_active=True,
    )
    project.project_members.create(user=user, role="admin")
    return project


@pytest_fixture
def task(project: Project, user: CustomUser) -> Task:
    """Create a test task."""
    return Task.objects.create(
        title=fake.sentence(),
        description=fake.text(),
        project=project,
        created_by=user,
        assignee=user,
    )


@pytest_fixture
def comments(task: Task, user: CustomUser) -> list[TaskComment]:
    """Create test comments."""
    return [
        TaskComment.objects.create(
            task=task,
            author=user,
            content=fake.text(),
        )
        for _ in range(3)
    ]


@pytest_mark.django_db
class TestGetTask:
    """Test suite for getting task details."""

    def test_get_task_details(
        self,
        api_client: APIClient,
        token: str,
        project: Project,
        task: Task,
        comments: list[TaskComment],
    ):
        """Test getting task details successfully."""
        url = reverse("tasks:get-task", args=[project.id, task.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Test without comments
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["id"] == task.id
        assert response.data["data"]["title"] == task.title
        assert "comments" not in response.data["data"]

        # Test with comments included
        response = api_client.get(f"{url}?include_comments=true")
        assert response.status_code == status.HTTP_200_OK
        assert "comments" in response.data["data"]
        assert len(response.data["data"]["comments"]) == len(comments)

    def test_get_nonexistent_task(
        self, api_client: APIClient, token: str, project: Project
    ):
        """Test getting a nonexistent task."""
        url = reverse("tasks:get-task", args=[project.id, 999])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in str(response.data["errors"])

    def test_get_task_without_auth(
        self, api_client: APIClient, project: Project, task: Task
    ):
        """Test getting task without authentication."""
        url = reverse("tasks:get-task", args=[project.id, task.id])

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
