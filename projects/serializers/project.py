from __future__ import annotations

from typing import ClassVar

from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SerializerMethodField
from rest_framework.serializers import ValidationError

from accounts.serializers.user import User as UserSerializer
from projects.models import Project
from projects.models import ProjectMember


class ProjectSerializer(ModelSerializer):
    """Serializer for Project model."""

    owner = UserSerializer(read_only=True)
    members_count = SerializerMethodField()
    current_user_role = SerializerMethodField()

    class Meta:
        """Meta class for ProjectSerializer."""

        model = Project
        fields: ClassVar[list[str]] = [
            "id",
            "name",
            "description",
            "owner",
            "is_active",
            "members_count",
            "current_user_role",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["owner", "created_at", "updated_at"]

    MIN_PROJECT_NAME_LENGTH: ClassVar[int] = 3

    def validate_name(self, value: str) -> str:
        """Validate project name."""
        if len(value.strip()) < self.MIN_PROJECT_NAME_LENGTH:
            raise ValidationError("Project name must be at least " "characters long")
        return value.strip()

    def get_members_count(self, obj: Project) -> int:
        """Get number of members in project."""
        return obj.members.count()

    def get_current_user_role(self, obj: Project) -> str | None:
        """Get role of current user in project."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        try:
            member = obj.project_members.get(user=request.user)
            return member.role
        except ProjectMember.DoesNotExist:
            return None
