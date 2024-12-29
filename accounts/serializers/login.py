from rest_framework.serializers import CharField, EmailField, Serializer


class Login(Serializer):
    """Serializer for login."""

    email = EmailField()
    password = CharField(style={"input_type": "password"})
