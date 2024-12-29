from typing import ClassVar

from rest_framework.serializers import ModelSerializer, ValidationError

from accounts.models.user_mfa import UserMFA


class UserMFASerializer(ModelSerializer):
    """Serializer for UserMFA model."""

    class Meta:
        """Meta class for UserMFASerializer."""

        model = UserMFA
        fields = (
            "id",
            "user",
            "is_enabled",
            "default_method",
            "otp_secret",
            "backup_codes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at", "otp_secret")
        extra_kwargs: ClassVar[dict] = {"default_method": {"required": True}}

    def validate(self, data: dict) -> dict:
        """Validate the serializer data."""
        if data.get("is_enabled") and not data.get("default_method"):
            raise ValidationError("A default method is required when enabling MFA")
        return data
