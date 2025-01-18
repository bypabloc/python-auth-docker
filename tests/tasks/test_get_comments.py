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
    comments = []
    for _ in range(3):
        comment = TaskComment.objects.create(
            task=task,
            author=user,
            content=fake.text(),
        )
        comments.append(comment)
    return sorted(comments, key=lambda x: x.created_at, reverse=True)


@pytest_mark.django_db
class TestGetComments:
    """Test suite for getting task comments."""

    def test_get_comments_successfully(
        self,
        api_client: APIClient,
        token: str,
        project: Project,
        task: Task,
        comments: list[TaskComment],
    ):
        """Test getting comments successfully."""
        url = reverse("tasks:get-task-comments", args=[project.id, task.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["comments"]) == len(comments)
        assert response.data["data"]["total"] == len(comments)

        # Verify comments are ordered by created_at desc
        response_dates = [
            comment["created_at"] for comment in response.data["data"]["comments"]
        ]
        assert response_dates == sorted(response_dates, reverse=True)

    def test_get_comments_empty_task(
        self, api_client: APIClient, token: str, project: Project, task: Task
    ):
        """Test getting comments for task with no comments."""
        url = reverse("tasks:get-task-comments", args=[project.id, task.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["comments"]) == 0
        assert response.data["data"]["total"] == 0

    def test_get_comments_nonexistent_task(
        self, api_client: APIClient, token: str, project: Project
    ):
        """Test getting comments for nonexistent task."""
        url = reverse("tasks:get-task-comments", args=[project.id, 999])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in str(response.data["errors"])

    def test_get_comments_without_auth(
        self, api_client: APIClient, project: Project, task: Task
    ):
        """Test getting comments without authentication."""
        url = reverse("tasks:get-task-comments", args=[project.id, task.id])

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_comments_with_non_member_user(
        self, api_client: APIClient, project: Project, task: Task
    ):
        """Test getting comments by user who is not a project member."""
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

        url = reverse("tasks:get-task-comments", args=[project.id, task.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in str(response.data["errors"])

    def test_comment_cache_invalidation(
        self,
        api_client: APIClient,
        token: str,
        project: Project,
        task: Task,
        comments: list[TaskComment],
    ):
        """Test that comment cache is properly invalidated."""
        url = reverse("tasks:get-task-comments", args=[project.id, task.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # First request should cache the result
        first_response = api_client.get(url)
        assert first_response.status_code == status.HTTP_200_OK
        initial_count = len(first_response.data["data"]["comments"])

        # Add new comment
        TaskComment.objects.create(
            task=task,
            author=task.created_by,
            content=fake.text(),
        )

        # Second request should get updated results
        second_response = api_client.get(url)
        assert second_response.status_code == status.HTTP_200_OK
        assert len(second_response.data["data"]["comments"]) == initial_count + 1
