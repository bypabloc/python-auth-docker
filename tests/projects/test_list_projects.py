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
def projects(user: CustomUser) -> list[Project]:
    """Create some test projects."""
    projects = []
    for _ in range(3):
        project = Project.objects.create(
            name=fake.company(),
            description=fake.text(max_nb_chars=200),
            owner=user,
            is_active=True,
        )
        # Add user as admin member
        project.project_members.create(user=user, role="admin")
        projects.append(project)
    return projects


@pytest_mark.django_db
class TestListProjects:
    """Test suite for listing projects."""

    def test_list_user_projects(
        self,
        api_client: APIClient,
        user: CustomUser,
        token: str,
        projects: list[Project],
    ):
        """Test listing projects for authenticated user."""
        url = reverse("projects:list-projects")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "projects" in response.data["data"]
        assert len(response.data["data"]["projects"]) == len(projects)

        # Verify returned project data
        project_ids = {p.id for p in projects}
        response_ids = {p["id"] for p in response.data["data"]["projects"]}
        assert project_ids == response_ids

    def test_list_projects_without_auth(self, api_client: APIClient):
        """Test listing projects without authentication."""
        url = reverse("projects:list-projects")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_projects_other_user(
        self, api_client: APIClient, projects: list[Project]
    ):
        """Test listing projects with different user."""
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

        url = reverse("projects:list-projects")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]["projects"]) == 0  # Should see no projects
