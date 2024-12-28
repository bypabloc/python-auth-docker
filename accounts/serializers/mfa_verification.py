from rest_framework.serializers import CharField, Serializer


class MFAVerification(Serializer):
    code = CharField(min_length=6, max_length=8)
