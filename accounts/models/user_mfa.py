from __future__ import annotations

from django.db.models import CASCADE
from django.db.models import SET_NULL
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import JSONField
from django.db.models import Model
from django.db.models import OneToOneField
from django.utils.translation import gettext_lazy as _

from accounts.models.custom_user import CustomUser
from accounts.models.mfa_method import MFAMethod


class UserMFA(Model):
    """Model for user MFA configuration."""

    user = OneToOneField(CustomUser, on_delete=CASCADE, related_name="mfa_config")
    is_enabled = BooleanField(default=False)
    default_method = ForeignKey(
        MFAMethod,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_users",
    )
    otp_secret = CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text=_("Secret key for TOTP generation"),
    )
    backup_codes = JSONField(
        null=True, blank=True, help_text=_("List of one-time backup codes")
    )
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        """Meta class for UserMFA."""

        verbose_name = _("user MFA configuration")
        verbose_name_plural = _("user MFA configurations")

    def __str__(self) -> str:
        """Return string representation."""
        return f"MFA config for {self.user.email}"
