from rest_framework.serializers import Serializer
from rest_framework.serializers import CharField
from rest_framework.serializers import EmailField


class VerificationCode(Serializer):
    code = CharField(min_length=6, max_length=6)
    email = EmailField()
