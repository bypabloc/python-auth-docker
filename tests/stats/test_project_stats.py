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
    token = generate_token_for_user(
        user=user,
        request=api_client.post("/").wsgi_request,
        is_temporary=False,
    ).value["token"]
    return token


@pytest_fixture
def project(user: CustomUser) -> Project:
    """Create test project."""
    project = Project.objects.create(
        name=fake.company(),
        description=fake.text(),
        owner=user,
        is_active=True,
    )
    project.project_members.create(user=user, role="admin")
    return project


@pytest_fixture
def tasks(project: Project, user: CustomUser) -> dict[str, list[Task]]:
    """Create test tasks with different statuses."""
    tasks_by_status = {
        "pending": [],
        "in_progress": [],
        "completed": [],
    }

    for task_status, task_list in tasks_by_status.items():
        for _ in range(3):
            task = Task.objects.create(
                title=fake.sentence(),
                description=fake.text(),
                project=project,
                created_by=user,
                assignee=user,
                status=task_status,
            )
            task_list.append(task)

    return tasks_by_status


@pytest_mark.django_db
class TestProjectStats:
    """Test suite for project statistics."""

    def test_get_project_stats(
        self,
        api_client: APIClient,
        token: str,
        project: Project,
        tasks: dict[str, list[Task]],
    ):
        """Test getting project statistics."""
        url = reverse("stats:project-stats", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        stats = response.data["data"]

        # Verify stats calculations
        total_tasks = sum(len(tasks_list) for tasks_list in tasks.values())
        assert stats["total_tasks"] == total_tasks
        assert stats["completed_tasks"] == len(tasks["completed"])
        assert stats["pending_tasks"] == len(tasks["pending"])
        assert stats["in_progress_tasks"] == len(tasks["in_progress"])

    def test_get_project_stats_empty(
        self, api_client: APIClient, token: str, project: Project
    ):
        """Test getting stats for project with no tasks."""
        url = reverse("stats:project-stats", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        stats = response.data["data"]

        # Verify all task counts are zero
        assert stats["total_tasks"] == 0
        assert stats["completed_tasks"] == 0
        assert stats["pending_tasks"] == 0
        assert stats["in_progress_tasks"] == 0

    def test_get_stats_nonexistent_project(self, api_client: APIClient, token: str):
        """Test getting stats for nonexistent project."""
        url = reverse("stats:project-stats", args=[999])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_stats_without_auth(self, api_client: APIClient, project: Project):
        """Test getting stats without authentication."""
        url = reverse("stats:project-stats", args=[project.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_stats_cache_invalidation(
        self,
        api_client: APIClient,
        token: str,
        project: Project,
        user: CustomUser,
        tasks: dict[str, list[Task]],
    ):
        """Test that stats cache is properly invalidated."""
        url = reverse("stats:project-stats", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # First request should cache the result
        first_response = api_client.get(url)
        assert first_response.status_code == status.HTTP_200_OK
        initial_total = first_response.data["data"]["total_tasks"]
        initial_completed = first_response.data["data"]["completed_tasks"]

        # Create new completed task
        Task.objects.create(
            title=fake.sentence(),
            description=fake.text(),
            project=project,
            created_by=user,
            assignee=user,
            status="completed",
        )

        # Second request should get updated results
        second_response = api_client.get(url)
        assert second_response.status_code == status.HTTP_200_OK
        assert second_response.data["data"]["total_tasks"] == initial_total + 1
        assert second_response.data["data"]["completed_tasks"] == initial_completed + 1

    def test_get_stats_with_non_member_user(
        self, api_client: APIClient, project: Project
    ):
        """Test getting project stats by non-member user."""
        # Create non-member user
        non_member = CustomUser.objects.create_user(
            username=fake.user_name(),
            email=fake.email(),
            password="testpass123",
        )
        non_member.is_verified = True
        non_member.save()

        # Generate token for non-member
        result = generate_token_for_user(
            user=non_member,
            request=api_client.post("/").wsgi_request,
            is_temporary=False,
        )
        token = result.value["token"]

        url = reverse("stats:project-stats", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
