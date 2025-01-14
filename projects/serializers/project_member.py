from __future__ import annotations

from typing import ClassVar

from rest_framework.serializers import ModelSerializer

from accounts.serializers.user import User as UserSerializer
from projects.models import ProjectMember


class ProjectMemberSerializer(ModelSerializer):
    """Serializer for ProjectMember model."""

    user = UserSerializer(read_only=True)

    class Meta:
        """Meta class for ProjectMemberSerializer."""

        model = ProjectMember
        fields: ClassVar[list[str]] = [
            "id",
            "user",
            "role",
            "joined_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["joined_at"]
