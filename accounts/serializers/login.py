from rest_framework.serializers import CharField, EmailField, Serializer


class Login(Serializer):
    email = EmailField()
    password = CharField(style={"input_type": "password"})
