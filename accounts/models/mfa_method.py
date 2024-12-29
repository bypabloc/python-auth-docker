from __future__ import annotations

from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import Model
from django.utils.translation import gettext_lazy as _


class MFAMethod(Model):
    """Model for MFA method."""

    name = CharField(
        max_length=20,
        unique=True,
        choices=[("otp", "One-Time Password"), ("email", "Email Verification")],
    )
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        """Meta options for MFAMethod model."""

        verbose_name = _("MFA method")
        verbose_name_plural = _("MFA methods")

    def __str__(self) -> str:
        """Return the display name of the MFA method."""
        return self.get_name_display()
