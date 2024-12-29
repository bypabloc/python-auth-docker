from __future__ import annotations

from typing import ClassVar

from django.db.models import CASCADE
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import Model
from django.utils.translation import gettext_lazy as _

from accounts.models.custom_user import CustomUser
from accounts.models.mfa_method import MFAMethod


class MFAVerification(Model):
    """Model for MFA verification."""

    user = ForeignKey(CustomUser, on_delete=CASCADE, related_name="mfa_verifications")
    method = ForeignKey(MFAMethod, on_delete=CASCADE, related_name="verifications")
    code = CharField(max_length=6)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()
    verified_at = DateTimeField(null=True, blank=True)
    is_verified = BooleanField(default=False)
    session_key = CharField(
        max_length=512,
        help_text=_("Temporary session key for MFA verification process"),
    )

    class Meta:
        """Meta class for MFAVerification."""

        verbose_name = _("MFA verification")
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"MFA verification for {self.user.email} using {self.method.name}"
