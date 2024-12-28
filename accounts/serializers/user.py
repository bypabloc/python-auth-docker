from rest_framework.serializers import ModelSerializer

from accounts.models import CustomUser


class User(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "email", "username", "password", "is_verified")
        extra_kwargs = {
            "password": {"write_only": True},
            "is_verified": {"read_only": True},
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        return user
