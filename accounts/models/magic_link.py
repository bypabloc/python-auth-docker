from __future__ import annotations

from typing import ClassVar

from django.db.models import CASCADE
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django.db.models import Index
from django.db.models import Model
from django.utils.crypto import get_random_string

from accounts.models.custom_user import CustomUser


class MagicLink(Model):
    """Model for magic links used in passwordless authentication."""

    user = ForeignKey(CustomUser, on_delete=CASCADE, related_name="magic_links")
    token = CharField(max_length=64, unique=True)
    is_used = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()
    type = CharField(
        max_length=20,
        choices=[
            ("registration", "Registration"),
            ("login", "Login"),
            ("password_set", "Password Set"),
        ],
    )

    class Meta:
        """Meta options for MagicLink model."""

        indexes: ClassVar[list[Index]] = [
            Index(fields=["token", "is_used"]),
            Index(fields=["user", "type", "is_used"]),
        ]

    @classmethod
    def generate_token(cls) -> str:
        """Generate a unique token for the magic link."""
        return get_random_string(64)

    def __str__(self) -> str:
        """Return string representation."""
        return f"Magic link for {self.user.email} ({self.type})"
