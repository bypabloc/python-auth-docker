from __future__ import annotations

from typing import ClassVar

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import ValidationError

from accounts.models.custom_user import CustomUser


class User(ModelSerializer):
    """Serializer for CustomUser model."""

    class Meta:
        """Meta class for User."""

        model = CustomUser
        fields = ("id", "email", "password", "is_verified", "has_password")
        extra_kwargs: ClassVar[dict] = {
            "password": {"write_only": True, "required": False},
            "is_verified": {"read_only": True},
            "has_password": {"read_only": True},
        }

    def validate_password(self, value: str | None) -> str | None:
        """Validate password using Django's password validators."""
        if value:
            try:
                validate_password(value)
            except DjangoValidationError as e:
                raise ValidationError(list(e.messages)) from e
        return value

    def create(self, validated_data: dict) -> CustomUser:
        """Create a new user with proper password hashing."""
        # Generate a temporary unusable password if none provided
        if "password" not in validated_data:
            validated_data["password"] = None

        # Create user without password if none provided
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data.get("username", validated_data["email"]),
            password=validated_data["password"],
        )

        # If no password was provided, set an unusable password
        if not validated_data["password"]:
            user.set_unusable_password()
            user.save()

        return user
