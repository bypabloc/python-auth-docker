"""This module defines the HomeView class.

This module defines a HomeView class,
which is a subclass of rest_framework.views.APIView.
The HomeView class provides a GET endpoint that returns a welcome message and a list
of available authentication endpoints.

Classes:
    HomeView: A view that handles GET requests and returns
        a welcome message and available endpoints.

Usage:
    Add the HomeView to your URL configuration to provide
    a welcome message and list of authentication endpoints.

Example:
    urlpatterns = [
        path('api/home/', HomeView.as_view(), name='home'),
    ]
"""

from typing import ClassVar

from rest_framework import views
from rest_framework.permissions import AllowAny, BasePermission
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
