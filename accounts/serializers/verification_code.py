from rest_framework.serializers import CharField, EmailField, Serializer


class VerificationCode(Serializer):
    code = CharField(min_length=6, max_length=6)
    email = EmailField()
