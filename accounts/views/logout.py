from typing import ClassVar

from rest_framework import status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models.user_token import UserToken


class LogoutView(APIView):
    """Handle user logout."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Logout the user."""
        # Only allow logout with permanent tokens
        if request.token_payload.get("is_temporary", False):
            return Response(
                {"error": "Invalid token type"}, status=status.HTTP_400_BAD_REQUEST
            )

        UserToken.objects.filter(
            user=request.user, token=request.auth, is_valid=True
        ).update(is_valid=False)

        return Response({"message": "Logged out successfully"})
