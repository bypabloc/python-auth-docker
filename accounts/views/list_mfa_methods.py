from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.models import MFAMethod
from accounts.serializers.mfa_method import MFAMethod as MFAMethodSerializer


class ListMFAMethodsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MFAMethodSerializer
    queryset = MFAMethod.objects.filter(is_active=True)
