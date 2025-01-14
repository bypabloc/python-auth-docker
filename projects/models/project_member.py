from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db.models import CASCADE
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import Model
from django.utils.translation import gettext_lazy as _


class ProjectMember(Model):
    """Model for project members."""

    ROLE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("admin", _("Admin")),
        ("member", _("Member")),
        ("viewer", _("Viewer")),
    ]

    project = ForeignKey(
        "projects.Project",
        on_delete=CASCADE,
        related_name="project_members",
        help_text=_("The project this member belongs to"),
    )
    user = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="project_memberships",
        help_text=_("The user who is a member of the project"),
    )
    role = CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="member",
        help_text=_("The role of the user in this project"),
    )
    joined_at = DateTimeField(
        auto_now_add=True,
        help_text=_("When the user joined the project"),
    )

    class Meta:
        """Meta class for ProjectMember."""

        unique_together: ClassVar[list[str]] = ["project", "user"]
        verbose_name = _("project member")
        verbose_name_plural = _("project members")

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.user.email} - {self.project.name} ({self.role})"
