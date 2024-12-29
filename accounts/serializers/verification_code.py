from rest_framework.serializers import CharField, EmailField, Serializer


class VerificationCode(Serializer):
    """Serializer for verification code."""

    code = CharField(min_length=6, max_length=6)
    email = EmailField()
