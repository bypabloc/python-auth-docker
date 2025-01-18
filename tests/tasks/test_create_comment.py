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
    project.project_members.create(
        user=user,
        role="admin",
    )
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


@pytest_mark.django_db
class TestCreateComment:
    """Test suite for creating task comments."""

    def test_successful_comment_creation(
        self, api_client: APIClient, token: str, project: Project, task: Task
    ):
        url = reverse("tasks:create-comment", args=[project.id, task.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        comment_data = {
            "content": fake.text(),
        }

        response = api_client.post(url, comment_data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_comment_creation_with_empty_content(
        self,
        api_client: APIClient,
        token: str,
        project: Project,
        task: Task,
    ):
        """Test comment creation with empty content."""
        url = reverse(
            "tasks:create-comment",
            args=[
                project.id,
                task.id,
            ],
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url, {"content": ""})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "content" in str(response.data["errors"])

    def test_comment_on_nonexistent_task(
        self,
        api_client: APIClient,
        token: str,
        project: Project,
    ):
        """Test commenting on a nonexistent task."""
        url = reverse(
            "tasks:create-comment",
            args=[
                project.id,
                999,
            ],
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url, {"content": fake.text()})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in str(response.data["errors"])

    def test_comment_without_auth(
        self,
        api_client: APIClient,
        project: Project,
        task: Task,
    ):
        """Test comment creation without authentication."""
        url = reverse(
            "tasks:create-comment",
            args=[
                project.id,
                task.id,
            ],
        )

        response = api_client.post(url, {"content": fake.text()})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_comment_with_non_member_user(
        self,
        api_client: APIClient,
        project: Project,
        task: Task,
    ):
        """Test comment creation by user who is not a project member."""
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

        url = reverse(
            "tasks:create-comment",
            args=[
                project.id,
                task.id,
            ],
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url, {"content": fake.text()})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in str(response.data["errors"])

    def test_comment_on_inactive_project(
        self,
        api_client: APIClient,
        token: str,
        project: Project,
        task: Task,
    ):
        """Test comment creation on a task in an inactive project."""
        # Deactivate project
        project.is_active = False
        project.save()

        url = reverse(
            "tasks:create-comment",
            args=[
                project.id,
                task.id,
            ],
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url, {"content": fake.text()})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in str(response.data["errors"])
