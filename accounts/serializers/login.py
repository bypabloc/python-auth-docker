from rest_framework.serializers import Serializer
from rest_framework.serializers import EmailField
from rest_framework.serializers import CharField


class Login(Serializer):
    email = EmailField()
    password = CharField(style={'input_type': 'password'})
