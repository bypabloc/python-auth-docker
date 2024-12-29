from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from rest_framework.request import Request


class EmailBackend(ModelBackend):
    """Custom authentication backend to allow login with email."""

    def authenticate(
        self,
        request: Request,
        username: str | None = None,
        password: str | None = None,
        **kwargs: dict,
    ) -> AbstractUser | None:
        """Authenticate user by email or username."""
        user_model = get_user_model()
        try:
            user = user_model.objects.get(Q(username=username) | Q(email=username))
            if not password:
                return None

            if not user.check_password(password):
                return None
            return user
        except user_model.DoesNotExist:
            return None
