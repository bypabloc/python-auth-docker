from datetime import timedelta

import jwt
from django.conf import settings
from django.utils import timezone
from ua_parser import user_agent_parser

from accounts.models import UserToken


def generate_token_for_user(user, request, is_temporary=False):
    """
    Generate a JWT token and UserToken instance for a given user.

    Args:
        user: The user instance to generate token for
        request: The request object to extract user agent info
        is_temporary: If True, generates a short-lived token for verification

    Returns:
        tuple: (jwt_token, user_token_instance)
    """
    # Parse user agent
    ua_string = request.META.get("HTTP_USER_AGENT", "")
    parsed_ua = user_agent_parser.Parse(ua_string)

    # Set expiration based on token type
    expires_at = timezone.now() + (
        timedelta(minutes=10) if is_temporary else timedelta(days=7)
    )

    # Create JWT token
    token_payload = {
        "user_id": user.id,
        "email": user.email,
        "is_temporary": is_temporary,
        "exp": expires_at.timestamp(),
    }
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm="HS256")

    # Create UserToken instance
    user_token = UserToken.objects.create(
        user=user,
        token=token,
        device_type=parsed_ua["device"]["family"],
        device_os=f"{parsed_ua['os']['family']} {parsed_ua['os']['major']}",
        device_browser=(
            f"{parsed_ua['user_agent']['family']}" f"{parsed_ua['user_agent']['major']}"
        ),
        expires_at=expires_at,
    )

    return token, user_token
