# tests/stats/test_user_stats.py
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
from shared.cache import cache as cache_instance
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
def projects(user: CustomUser) -> list[Project]:
    """Create test projects for user."""
    projects = []
    for _ in range(3):
        project = Project.objects.create(
            name=fake.company(),
            description=fake.text(),
            owner=user,
            is_active=True,
        )
        # Add as admin member
        project.project_members.create(user=user, role="admin")
        projects.append(project)
    return projects


@pytest_fixture
def tasks(projects: list[Project], user: CustomUser) -> list[Task]:
    """Create test tasks for user."""
    tasks = []
    for project in projects:
        # Create tasks with different statuses
        for task_status in ["pending", "in_progress", "completed"]:
            task = Task.objects.create(
                title=fake.sentence(),
                description=fake.text(),
                project=project,
                created_by=user,
                assignee=user,
                status=task_status,
            )
            tasks.append(task)
    return tasks


@pytest_mark.django_db
class TestUserStats:
    """Test suite for user statistics."""

    def test_get_user_stats(
        self,
        api_client: APIClient,
        token: str,
        user: CustomUser,
        projects: list[Project],
        tasks: list[Task],
    ):
        """Test getting user statistics."""
        url = reverse("stats:user-stats")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        stats = response.data["data"]

        # Verify stats calculations
        assert stats["total_projects"] == len(projects)
        assert stats["owned_projects"] == len(projects)  # All projects are owned
        assert stats["assigned_tasks"] == len(tasks)  # All tasks are assigned
        assert stats["created_tasks"] == len(tasks)  # All tasks are created
        assert stats["completed_tasks"] == len(
            [task for task in tasks if task.status == "completed"]
        )

    def test_get_user_stats_empty(self, api_client: APIClient, token: str):
        """Test getting stats for user with no activity."""
        url = reverse("stats:user-stats")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        stats = response.data["data"]

        # Verify all stats are zero
        assert stats["total_projects"] == 0
        assert stats["owned_projects"] == 0
        assert stats["assigned_tasks"] == 0
        assert stats["created_tasks"] == 0
        assert stats["completed_tasks"] == 0

    def test_get_stats_without_auth(self, api_client: APIClient):
        """Test getting stats without authentication."""
        url = reverse("stats:user-stats")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_stats_cache_invalidation(
        self,
        api_client: APIClient,
        token: str,
        user: CustomUser,
        projects: list[Project],
    ):
        """Test that stats cache is properly invalidated."""
        url = reverse("stats:user-stats")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # First request should cache the result
        first_response = api_client.get(url)
        assert first_response.status_code == status.HTTP_200_OK
        initial_projects = first_response.data["data"]["total_projects"]

        # Create new project through the API
        create_project_url = reverse("projects:create-project")
        project_data = {
            "name": fake.company(),
            "description": fake.text(),
            "is_active": True,
        }
        response = api_client.post(create_project_url, project_data)
        assert response.status_code == status.HTTP_201_CREATED

        cache_key = f"user_stats_{user.id}"
        cache_instance.delete(cache_key)

        # Second request should get updated results
        second_response = api_client.get(url)
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["data"]["total_projects"] == initial_projects + 1
