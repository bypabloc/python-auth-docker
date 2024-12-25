from rest_framework.serializers import ModelSerializer
from accounts.models import MFAMethod


class MFAMethod(ModelSerializer):
    class Meta:
        model = MFAMethod
        fields = ('id', 'name', 'is_active')
