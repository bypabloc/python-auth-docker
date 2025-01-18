from __future__ import annotations

from typing import ClassVar

from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import SerializerMethodField
from rest_framework.serializers import ValidationError

from accounts.serializers.user import User as UserSerializer
from tasks.models import Task
from tasks.models import TaskComment


class TaskCommentSerializer(ModelSerializer):
    """Serializer for TaskComment model."""

    author = UserSerializer(read_only=True)

    class Meta:
        """Meta class for TaskCommentSerializer."""

        model = TaskComment
        fields: ClassVar[list[str]] = [
            "id",
            "task",
            "author",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "author",
            "task",
            "created_at",
            "updated_at",
        ]


class TaskSerializer(ModelSerializer):
    """Serializer for Task model."""

    assignee = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    comments_count = SerializerMethodField()

    class Meta:
        """Meta class for TaskSerializer."""

        model = Task
        fields: ClassVar[list[str]] = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "project",
            "assignee",
            "created_by",
            "is_active",
            "comments_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "created_by",
            "created_at",
            "updated_at",
            "project",
        ]

    TITLE_MIN_LENGTH = 3

    def validate_title(self, value: str) -> str:
        """Validate task title."""
        if len(value.strip()) < self.TITLE_MIN_LENGTH:
            raise ValidationError(
                f"Task title must be at least {self.TITLE_MIN_LENGTH} characters long"
            )
        return value.strip()

    def get_comments_count(self, obj: Task) -> int:
        """Get number of comments on task."""
        return obj.comments.count()
