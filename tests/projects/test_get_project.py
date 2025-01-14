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
def project(user: CustomUser) -> Project:
    """Create a test project."""
    project = Project.objects.create(
        name=fake.company(),
        description=fake.text(max_nb_chars=200),
        owner=user,
        is_active=True,
    )
    # Add user as admin member
    project.project_members.create(user=user, role="admin")
    return project


@pytest_mark.django_db
class TestGetProject:
    """Test suite for getting project details."""

    def test_get_project_details(
        self, api_client: APIClient, user: CustomUser, token: str, project: Project
    ):
        """Test getting project details successfully."""
        url = reverse("projects:get-project", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["id"] == project.id
        assert response.data["data"]["name"] == project.name
        assert response.data["data"]["description"] == project.description
        assert response.data["data"]["owner"]["id"] == user.id
        assert response.data["data"]["current_user_role"] == "admin"

    def test_get_nonexistent_project(self, api_client: APIClient, token: str):
        """Test getting a project that doesn't exist."""
        url = reverse("projects:get-project", args=[999])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Project not found" in str(response.data["errors"])

    def test_get_project_without_auth(self, api_client: APIClient, project: Project):
        """Test getting project without authentication."""
        url = reverse("projects:get-project", args=[project.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_project_unauthorized_user(
        self, api_client: APIClient, project: Project
    ):
        """Test getting project details with unauthorized user."""
        # Create another user
        other_user = CustomUser.objects.create_user(
            username=fake.user_name(), email=fake.email(), password="testpass123"
        )
        other_user.is_verified = True
        other_user.save()

        # Generate token for other user
        result = generate_token_for_user(
            user=other_user,
            request=api_client.post("/").wsgi_request,
            is_temporary=False,
        )
        token = result.value["token"]

        url = reverse("projects:get-project", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
