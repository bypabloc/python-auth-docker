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
def valid_project_data() -> dict:
    """Create valid project data for testing."""
    return {
        "name": fake.company(),
        "description": fake.text(max_nb_chars=200),
        "is_active": True,
    }


@pytest_mark.django_db
class TestCreateProject:
    """Test suite for project creation."""

    def test_successful_project_creation(
        self,
        api_client: APIClient,
        user: CustomUser,
        token: str,
        valid_project_data: dict,
    ):
        """Test successful project creation with valid data."""
        url = reverse("projects:create-project")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.post(url, valid_project_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["name"] == valid_project_data["name"]
        assert response.data["message"] == "Project created successfully"

        # Verify project was created in database
        project = Project.objects.get(name=valid_project_data["name"])
        assert project.owner == user
        assert project.description == valid_project_data["description"]
        assert project.is_active == valid_project_data["is_active"]

        # Verify creator was added as admin member
        member = project.project_members.get(user=user)
        assert member.role == "admin"

    def test_project_creation_without_auth(
        self, api_client: APIClient, valid_project_data: dict
    ):
        """Test project creation attempt without authentication."""
        url = reverse("projects:create-project")
        response = api_client.post(url, valid_project_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_project_creation_with_invalid_data(
        self, api_client: APIClient, user: CustomUser, token: str
    ):
        """Test project creation with invalid data."""
        url = reverse("projects:create-project")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Test with empty name
        response = api_client.post(url, {"name": "", "description": "test description"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in str(response.data["errors"])

        # Test with too short name
        response = api_client.post(
            url,
            {
                "name": "ab",  # Should be at least 3 characters
                "description": "test description",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in str(response.data["errors"])
