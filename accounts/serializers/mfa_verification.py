from __future__ import annotations

from rest_framework.serializers import CharField
from rest_framework.serializers import Serializer


class MFAVerification(Serializer):
    """Serializer for MFA verification."""

    code = CharField(min_length=6, max_length=8)
