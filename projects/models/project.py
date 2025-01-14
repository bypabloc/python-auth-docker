from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db.models import CASCADE
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import ManyToManyField
from django.db.models import Model
from django.db.models import TextField
from django.utils.translation import gettext_lazy as _


class Project(Model):
    """Model for projects."""

    name = CharField(
        max_length=200,
        help_text=_("The name of the project"),
    )
    description = TextField(
        blank=True,
        help_text=_("A detailed description of the project"),
    )
    owner = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="owned_projects",
        help_text=_("The user who created the project"),
    )
    members = ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="projects.ProjectMember",
        related_name="projects",
        help_text=_("Users who are members of this project"),
    )
    is_active = BooleanField(
        default=True,
        help_text=_("Whether the project is active"),
    )
    created_at = DateTimeField(
        auto_now_add=True,
        help_text=_("When the project was created"),
    )
    updated_at = DateTimeField(
        auto_now=True,
        help_text=_("When the project was last updated"),
    )

    class Meta:
        """Meta class for Project."""

        ordering: ClassVar[list[str]] = ["-created_at"]
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def __str__(self) -> str:
        """Return string representation."""
        return self.name
