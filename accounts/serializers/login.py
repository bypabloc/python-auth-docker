from __future__ import annotations

from rest_framework.serializers import CharField
from rest_framework.serializers import EmailField
from rest_framework.serializers import Serializer


class Login(Serializer):
    """Serializer for login."""

    email = EmailField()
    password = CharField(style={"input_type": "password"})
