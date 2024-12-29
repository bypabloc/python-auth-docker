from typing import ClassVar

from rest_framework.serializers import ModelSerializer

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

    def create(self, validated_data: dict) -> CustomUser:
        """Create a new user."""
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        return user
