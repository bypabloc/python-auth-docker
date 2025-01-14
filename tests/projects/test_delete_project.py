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


@pytest_fixture
def member_user() -> CustomUser:
    """Create another user as member."""
    user = CustomUser.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password="testpass123",
    )
    user.is_verified = True
    user.save()
    return user


@pytest_mark.django_db
class TestDeleteProject:
    """Test suite for project deletion."""

    def test_successful_delete(
        self, api_client: APIClient, token: str, project: Project
    ):
        """Test successful project deletion by admin."""
        url = reverse("projects:delete-project", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Project deleted successfully"

        # Verify project was deleted
        assert not Project.objects.filter(id=project.id).exists()

    def test_delete_as_member(
        self,
        api_client: APIClient,
        project: Project,
        member_user: CustomUser,
    ):
        """Test project deletion attempt by regular member."""
        # Add member_user as regular member
        project.project_members.create(user=member_user, role="member")

        # Generate token for member user
        result = generate_token_for_user(
            user=member_user,
            request=api_client.post("/").wsgi_request,
            is_temporary=False,
        )
        token = result.value["token"]

        url = reverse("projects:delete-project", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Permission denied" in str(response.data["errors"])

        # Verify project still exists
        assert Project.objects.filter(id=project.id).exists()

    def test_delete_nonexistent_project(self, api_client: APIClient, token: str):
        """Test deleting a nonexistent project."""
        url = reverse("projects:delete-project", args=[999])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Project not found" in str(response.data["errors"])

    def test_delete_without_auth(self, api_client: APIClient, project: Project):
        """Test deletion attempt without authentication."""
        url = reverse("projects:delete-project", args=[project.id])

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify project still exists
        assert Project.objects.filter(id=project.id).exists()

    def test_delete_project_multiple_members(
        self,
        api_client: APIClient,
        token: str,
        project: Project,
        member_user: CustomUser,
    ):
        """Test deleting project with multiple members."""
        # Add member_user as regular member
        project.project_members.create(user=member_user, role="member")

        url = reverse("projects:delete-project", args=[project.id])
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Project deleted successfully"

        # Verify project and all memberships were deleted
        assert not Project.objects.filter(id=project.id).exists()
        assert not project.project_members.exists()
