from __future__ import annotations

from typing import Any
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db.models import BooleanField
from django.db.models import DateTimeField
from django.db.models import EmailField
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Custom user model with email as the unique identifier."""

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    email = EmailField(_("email address"), unique=True)
    is_verified = BooleanField(default=False)
    has_mfa = BooleanField(
        default=False, help_text=_("Indicates if user has configured MFA")
    )
    has_password = BooleanField(default=False)

    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        """Meta options for CustomUser model."""

        verbose_name = _("user")
        verbose_name_plural = _("users")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to set has_password flag."""
        if self.password and not self.password.startswith("!"):
            self.has_password = True
        super().save(*args, **kwargs)
