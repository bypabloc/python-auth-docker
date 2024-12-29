from __future__ import annotations

from typing import ClassVar

from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response


class HomeView(views.APIView):
    """Define the HomeView class."""

    permission_classes: ClassVar[list[type[BasePermission]]] = [AllowAny]

    def get(self, request: Request) -> Response:
        """Handle GET requests.

        Args:
            request: The HTTP request object containing the client's request data.

        Returns:
            A Response object containing a welcome message and available endpoints.
        """
        return Response(
            {
                "message": "Welcome to the API",
                "endpoints": {
                    "auth": {
                        "register": "/api/register/",
                        "login": "/api/login/",
                        "logout": "/api/logout/",
                    }
                },
            }
        )
