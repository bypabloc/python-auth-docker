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
        fields = ("id", "email", "username", "password", "is_verified")
        extra_kwargs: ClassVar[dict] = {
            "password": {"write_only": True},
            "is_verified": {"read_only": True},
        }

    def validate_password(self, value: str) -> str:
        """Validate password using Django's password validators."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise ValidationError(list(e.messages)) from e
        return value

    def create(self, validated_data: dict) -> CustomUser:
        """Create a new user with proper password hashing."""
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        return user

    def to_representation(self, instance: CustomUser) -> dict:
        """Convert User instance to dictionary, excluding sensitive fields."""
        data = super().to_representation(instance)
        return data
