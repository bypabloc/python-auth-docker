from rest_framework.serializers import CharField, Serializer


class MFAVerification(Serializer):
    """Serializer for MFA verification."""

    code = CharField(min_length=6, max_length=8)
