from typing import ClassVar

from rest_framework import generics
from rest_framework.permissions import BasePermission, IsAuthenticated

from accounts.models.mfa_method import MFAMethod
from accounts.serializers.mfa_method import MFAMethod as MFAMethodSerializer


class ListMFAMethodsView(generics.ListAPIView):
    """List all active MFA methods for the user."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated]
    serializer_class = MFAMethodSerializer
    queryset = MFAMethod.objects.filter(is_active=True)
