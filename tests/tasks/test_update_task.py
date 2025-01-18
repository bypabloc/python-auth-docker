# tests/tasks/test_update_task.py
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
        status="pending",
        priority="medium",
    )


@pytest_mark.django_db
class TestUpdateTask:
    """Test suite for task updates."""

    def test_successful_update(
        self, api_client: APIClient, token: str, project: Project, task: Task
    ):
        """Test successful task update."""
        url = reverse("tasks:update-task", args=[project.id, task.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        update_data = {
            "title": fake.sentence(),
            "description": fake.text(),
            "status": "in_progress",
            "priority": "high",
        }

        response = api_client.put(url, update_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == update_data["title"]
        assert response.data["data"]["status"] == update_data["status"]
        assert response.data["data"]["priority"] == update_data["priority"]
        assert response.data["message"] == "Task updated successfully"

        # Verify updates in database
        task.refresh_from_db()
        assert task.title == update_data["title"]
        assert task.status == update_data["status"]
        assert task.priority == update_data["priority"]

    def test_update_with_invalid_data(
        self, api_client: APIClient, token: str, project: Project, task: Task
    ):
        """Test update with invalid data."""
        url = reverse("tasks:update-task", args=[project.id, task.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Test with invalid status
        response = api_client.put(url, {"status": "invalid_status"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in str(response.data["errors"])

        # Test with empty title
        response = api_client.put(url, {"title": ""})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "title" in str(response.data["errors"])

    def test_update_nonexistent_task(
        self, api_client: APIClient, token: str, project: Project
    ):
        """Test updating a nonexistent task."""
        url = reverse("tasks:update-task", args=[project.id, 999])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.put(url, {"title": fake.sentence()})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in str(response.data["errors"])

    def test_update_without_auth(
        self, api_client: APIClient, project: Project, task: Task
    ):
        """Test update attempt without authentication."""
        url = reverse("tasks:update-task", args=[project.id, task.id])

        response = api_client.put(url, {"title": fake.sentence()})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
