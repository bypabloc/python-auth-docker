from rest_framework.serializers import ModelSerializer

from accounts.models.mfa_method import MFAMethod as MFAMethodModel


class MFAMethod(ModelSerializer):
    """Serializer for MFAMethod model."""

    class Meta:
        """Meta class for MFAMethod."""

        model = MFAMethodModel
        fields = ("id", "name", "is_active")
