from rest_framework.serializers import ModelSerializer, ValidationError

from accounts.models import UserMFA


class UserMFA(ModelSerializer):
    class Meta:
        model = UserMFA
        fields = ("is_enabled", "default_method")
        extra_kwargs = {"default_method": {"required": True}}

    def validate(self, data):
        if data.get("is_enabled") and not data.get("default_method"):
            raise ValidationError("A default method is required when enabling MFA")
        return data
