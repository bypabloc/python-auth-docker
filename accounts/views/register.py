from typing import ClassVar

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers.user import User as UserSerializer
from accounts.utils.email import send_verification_email
from accounts.utils.generate_token_for_user import generate_token_for_user
from utils.logger import logger


class RegisterView(APIView):
    """Handle user registration."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [AllowAny]

    def post(self, request: Request) -> Response:
        """Create a new user."""
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        token, _ = generate_token_for_user(user, request, is_temporary=True)
        data_verify_email = send_verification_email(user, "registration")

        response_data = {
            "message": (
                "User created successfully. "
                "Please check your email for verification code."
            ),
            "user": UserSerializer(user).data,
            "token": token,
        }

        logger.info(
            "User created successfully: {user.email} ",
            extra={
                "SEND_VERIFICATION_CODE_IN_RESPONSE": (
                    settings.SEND_VERIFICATION_CODE_IN_RESPONSE
                ),
            },
        )

        if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
            response_data["verification"] = data_verify_email

        return Response(response_data, status=status.HTTP_201_CREATED)
