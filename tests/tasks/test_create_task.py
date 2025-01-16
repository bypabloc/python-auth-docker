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
def valid_task_data() -> dict:
    """Create valid task data for testing."""
    return {
        "title": fake.sentence(),
        "description": fake.text(),
        "status": "pending",
        "priority": "medium",
    }


@pytest_mark.django_db
class TestCreateTask:
    """Test suite for task creation."""

    def test_successful_task_creation(
        self,
        api_client: APIClient,
        user: CustomUser,
        token: str,
        project: Project,
        valid_task_data: dict,
    ):
        """Test successful task creation with valid data."""
        url = reverse("tasks:create-task", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url, valid_task_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["title"] == valid_task_data["title"]
        assert response.data["message"] == "Task created successfully"

        # Verify task was created in database
        task = Task.objects.get(title=valid_task_data["title"])
        assert task.project == project
        assert task.created_by == user
        assert task.description == valid_task_data["description"]
        assert task.status == valid_task_data["status"]
        assert task.priority == valid_task_data["priority"]

    def test_task_creation_without_auth(
        self, api_client: APIClient, project: Project, valid_task_data: dict
    ):
        """Test task creation attempt without authentication."""
        url = reverse("tasks:create-task", args=[project.id])
        response = api_client.post(url, valid_task_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_task_creation_nonexistent_project(
        self, api_client: APIClient, token: str, valid_task_data: dict
    ):
        """Test task creation for nonexistent project."""
        url = reverse("tasks:create-task", args=[999])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url, valid_task_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_task_creation_with_invalid_data(
        self, api_client: APIClient, token: str, project: Project
    ):
        """Test task creation with invalid data."""
        url = reverse("tasks:create-task", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Test with empty title
        response = api_client.post(
            url, {"title": "", "description": "test description"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "title" in str(response.data["errors"])

        # Test with invalid status
        response = api_client.post(
            url, {"title": "Test Task", "status": "invalid_status"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in str(response.data["errors"])

    def test_task_creation_as_project_member(
        self, api_client: APIClient, project: Project, valid_task_data: dict
    ):
        """Test task creation as regular project member."""
        # Create another user as project member
        member = CustomUser.objects.create_user(
            username=fake.user_name(), email=fake.email(), password="testpass123"
        )
        member.is_verified = True
        member.save()

        # Add as regular member
        project.project_members.create(user=member, role="member")

        # Generate token for member
        result = generate_token_for_user(
            user=member,
            request=api_client.post("/").wsgi_request,
            is_temporary=False,
        )
        token = result.value["token"]

        url = reverse("tasks:create-task", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url, valid_task_data)

        assert response.status_code == status.HTTP_201_CREATED

        # Verify task was created with correct creator
        task = Task.objects.get(title=valid_task_data["title"])
        assert task.created_by == member
