from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db.models import CASCADE
from django.db.models import SET_NULL
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import Model
from django.db.models import TextChoices
from django.db.models import TextField
from django.utils.translation import gettext_lazy as _


class Task(Model):
    """Model for tasks."""

    class Status(TextChoices):
        """Status choices for tasks."""

        PENDING = "pending", _("Pending")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    class Priority(TextChoices):
        """Priority choices for tasks."""

        LOW = "low", _("Low")
        MEDIUM = "medium", _("Medium")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    title = CharField(
        max_length=200,
        help_text=_("The title of the task"),
    )
    description = TextField(
        blank=True,
        help_text=_("A detailed description of the task"),
    )
    status = CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_("The current status of the task"),
    )
    priority = CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text=_("The priority level of the task"),
    )
    due_date = DateTimeField(
        null=True,
        blank=True,
        help_text=_("When the task is due"),
    )
    project = ForeignKey(
        "projects.Project",
        on_delete=CASCADE,
        related_name="tasks",
        help_text=_("The project this task belongs to"),
    )
    assignee = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        help_text=_("The user assigned to this task"),
    )
    created_by = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="created_tasks",
        help_text=_("The user who created the task"),
    )
    is_active = BooleanField(
        default=True,
        help_text=_("Whether the task is active"),
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text=_("When the task was created"),
    )
    updated_at = DateTimeField(
        auto_now=True,
        help_text=_("When the task was last updated"),
    )

    class Meta:
        """Meta class for Task."""

        ordering: ClassVar[list[str]] = ["-created_at"]
        verbose_name = _("task")
        verbose_name_plural = _("tasks")

    def __str__(self) -> str:
        """Return string representation."""
        return self.title


class TaskComment(Model):
    """Model for task comments."""

    task = ForeignKey(
        Task,
        on_delete=CASCADE,
        related_name="comments",
        help_text=_("The task this comment belongs to"),
    )
    author = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="task_comments",
        help_text=_("The user who wrote this comment"),
    )
    content = TextField(
        help_text=_("The content of the comment"),
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text=_("When the comment was created"),
    )
    updated_at = DateTimeField(
        auto_now=True,
        help_text=_("When the comment was last updated"),
    )

    class Meta:
        """Meta class for TaskComment."""

        ordering: ClassVar[list[str]] = ["-created_at"]
        verbose_name = _("task comment")
        verbose_name_plural = _("task comments")

    def __str__(self) -> str:
        """Return string representation."""
        return f"Comment by {self.author.username} on {self.task.title}"
