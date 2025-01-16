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
def tasks(project: Project, user: CustomUser) -> list[Task]:
    """Create test tasks with different statuses and priorities."""
    tasks = []

    # Create tasks with different combinations
    statuses = ["pending", "in_progress", "completed"]
    priorities = ["low", "medium", "high"]

    for task_status in statuses:
        for priority in priorities:
            task = Task.objects.create(
                title=fake.sentence(),
                description=fake.text(),
                status=task_status,
                priority=priority,
                project=project,
                created_by=user,
                assignee=user if fake.boolean() else None,
            )
            tasks.append(task)

    return tasks


@pytest_mark.django_db
class TestListTasks:
    """Test suite for listing tasks."""

    def test_list_all_tasks(
        self, api_client: APIClient, token: str, project: Project, tasks: list[Task]
    ):
        """Test listing all tasks in project."""
        url = reverse("tasks:list-tasks", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["tasks"]) == len(tasks)

    def test_filter_by_status(
        self, api_client: APIClient, token: str, project: Project, tasks: list[Task]
    ):
        """Test filtering tasks by status."""
        url = reverse("tasks:list-tasks", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Test each task status
        for task_status in ["pending", "in_progress", "completed"]:
            response = api_client.get(f"{url}?status={task_status}")

            assert response.status_code == status.HTTP_200_OK
            assert all(
                task["status"] == task_status for task in response.data["data"]["tasks"]
            )

    def test_filter_by_priority(
        self, api_client: APIClient, token: str, project: Project, tasks: list[Task]
    ):
        """Test filtering tasks by priority."""
        url = reverse("tasks:list-tasks", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Test each priority
        for priority in ["low", "medium", "high"]:
            response = api_client.get(f"{url}?priority={priority}")

            assert response.status_code == status.HTTP_200_OK
            assert all(
                task["priority"] == priority for task in response.data["data"]["tasks"]
            )

    def test_filter_by_assignee(
        self,
        api_client: APIClient,
        token: str,
        user: CustomUser,
        project: Project,
        tasks: list[Task],
    ):
        """Test filtering tasks by assignee."""
        url = reverse("tasks:list-tasks", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Test assigned to me
        response = api_client.get(f"{url}?assignee=me")
        assert response.status_code == status.HTTP_200_OK
        assert all(
            task["assignee"]["id"] == user.id for task in response.data["data"]["tasks"]
        )

        # Test unassigned
        response = api_client.get(f"{url}?assignee=unassigned")
        assert response.status_code == status.HTTP_200_OK
        assert all(task["assignee"] is None for task in response.data["data"]["tasks"])

    def test_search_tasks(
        self, api_client: APIClient, token: str, project: Project, user: CustomUser
    ):
        """Test searching tasks by title/description."""
        # Create specific task for search
        search_term = "unique_search_term"
        Task.objects.create(
            title=f"Task with {search_term}",
            description="Regular description",
            project=project,
            created_by=user,
        )
        Task.objects.create(
            title="Regular title",
            description=f"Description with {search_term}",
            project=project,
            created_by=user,
        )

        url = reverse("tasks:list-tasks", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(f"{url}?search={search_term}")

        assert response.status_code == status.HTTP_200_OK
        expected_task_count = 2
        assert (
            len(response.data["data"]["tasks"]) == expected_task_count
        )  # Should find both tasks

    def test_list_tasks_without_auth(self, api_client: APIClient, project: Project):
        """Test listing tasks without authentication."""
        url = reverse("tasks:list-tasks", args=[project.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_tasks_nonexistent_project(self, api_client: APIClient, token: str):
        """Test listing tasks for nonexistent project."""
        url = reverse("tasks:list-tasks", args=[999])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
