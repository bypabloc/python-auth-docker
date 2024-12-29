from __future__ import annotations

from rest_framework.serializers import CharField
from rest_framework.serializers import EmailField
from rest_framework.serializers import Serializer


class VerificationCode(Serializer):
    """Serializer for verification code."""

    code = CharField(min_length=6, max_length=6)
    email = EmailField()
