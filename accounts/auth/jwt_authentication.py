from __future__ import annotations

import jwt
from django.conf import settings
from django.utils import timezone
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.request import Request

from accounts.models.custom_user import CustomUser
from accounts.models.user_token import UserToken


class JWTAuthentication(authentication.BaseAuthentication):
    """JWT Authentication class."""

    def authenticate(self, request: Request) -> tuple[CustomUser, str] | None:
        """Authenticate the request and return a two-tuple of (user, token)."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            return None

        try:
            token = auth_header.split(" ")[1]

            # Decode token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            # Verify token in database
            token_obj = UserToken.objects.get(
                token=token, is_valid=True, expires_at__gt=timezone.now()
            )

            # Add payload to request for later use
            request.token_payload = payload

            # Update last used
            token_obj.last_used_at = timezone.now()
            token_obj.save()

            return token_obj.user, token

        except jwt.ExpiredSignatureError as err:
            raise exceptions.AuthenticationFailed("Token expired") from err
        except jwt.InvalidTokenError as err:
            raise exceptions.AuthenticationFailed("Invalid token") from err
        except UserToken.DoesNotExist as err:
            raise exceptions.AuthenticationFailed("Token not found") from err

    def authenticate_header(self, request: Request) -> str:
        """Return the authentication header."""
        return "Bearer"
