from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class HomeView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
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
