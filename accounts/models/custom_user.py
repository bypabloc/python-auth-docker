from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db.models import BooleanField, DateTimeField, EmailField
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

    REQUIRED_FIELDS: ClassVar[list[str]] = ["username"]

    class Meta:
        """Meta options for CustomUser model."""

        verbose_name = _("user")
        verbose_name_plural = _("users")
