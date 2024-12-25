from rest_framework.serializers import Serializer
from rest_framework.serializers import CharField


class MFAVerification(Serializer):
    code = CharField(min_length=6, max_length=8)
