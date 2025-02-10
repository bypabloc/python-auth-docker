from __future__ import annotations

from datetime import timedelta
from random import choices as random_choices
from string import digits as string_digits
from typing import Any
from urllib.parse import urlencode

from boto3 import client as boto3_client
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models.magic_link import MagicLink
from accounts.models.verification_code import VerificationCode
from shared.result_as_values import Result
from shared.utils.logger import logger


def generate_verification_code() -> Result[str]:
    """Generate a random 6-digit verification code."""
    return Result.ok("".join(random_choices(string_digits, k=6)))


def generate_magic_link(
    user: User | AbstractUser,
    link_type: str,
    base_url: str,
) -> Result[dict[str, Any]]:
    """Generate a magic link for the user.

    Args:
        user: The user to generate the link for
        link_type: The type of magic link (registration, login, password_set)
        base_url: The base URL for the magic link

    Returns:
        The complete magic link URL
    """
    token = MagicLink.generate_token()
    expires_at = timezone.now() + timedelta(minutes=10)

    MagicLink.objects.create(
        user=user,
        token=token,
        type=link_type,
        expires_at=expires_at,
    )

    params = {
        "token": token,
        "email": user.email,
        "type": link_type,
    }

    return Result.ok(
        {
            "link": f"{base_url}?{urlencode(params)}",
            "expires_at": expires_at,
            "token": token,
        }
    )


def send_verification_email(
    user: User | AbstractUser,
    code_type: str,
    base_url: str | None = None,
) -> Result[dict[str, Any]]:
    """Send verification email to user.

    Args:
        user: CustomUser instance
        code_type: String ('registration' or 'login')
        base_url: Base URL for magic link (optional)
    """
    # Delete any previous unused codes of the same type
    VerificationCode.objects.filter(
        user=user,
        type=code_type,
        is_used=False,
    ).delete()

    # Generate new code and expiration
    result_generate_verification_code = generate_verification_code()
    expires_at = timezone.now() + timedelta(minutes=10)
    code = {
        "code": result_generate_verification_code.value,
        "expires_at": expires_at,
    }

    # Create verification code record
    VerificationCode.objects.create(
        user=user,
        code=code["code"],
        expires_at=expires_at,
        type=code_type,
    )

    # Generate magic link if base_url is provided
    magic_link = None
    if base_url:
        result_generate_magic_link = generate_magic_link(
            user=user,
            link_type=code_type,
            base_url=base_url,
        )
        magic_link = result_generate_magic_link.value

    # In test environment, don't try to send emails
    if settings.TESTING:
        return Result.ok(
            {
                "code": code,
                "magic_link": magic_link,
            }
        )

    if settings.SEND_EMAIL:
        try:
            client_params = {
                "service_name": "ses",
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                "region_name": settings.AWS_REGION_NAME,
            }

            # Create a new SES client
            ses_client = boto3_client(**client_params)

            # Prepare email body with both code and magic link
            email_body = f"Your verification code is: {code['code']}\n"
            email_body += "This code will expire in 10 minutes.\n\n"

            if magic_link:
                email_body += "Or click this link to verify your account:\n"
                email_body += f"{magic_link['link']}\n"
                email_body += "This link will expire in 10 minutes."

            send_email_params = {
                "Source": settings.DEFAULT_FROM_EMAIL,
                "Destination": {"ToAddresses": [user.email]},
                "Message": {
                    "Subject": {
                        "Data": "Your Verification Code",
                        "Charset": "UTF-8",
                    },
                    "Body": {
                        "Text": {
                            "Data": email_body,
                            "Charset": "UTF-8",
                        },
                    },
                },
            }

            try:
                response = ses_client.send_email(**send_email_params)
                logger.info(f"Email sent! Message ID: {response['MessageId']}")
            except ClientError as e:
                logger.warning(f"Failed to send email: {e!s}")
                if not settings.DEBUG and not settings.TESTING:
                    raise
        except Exception as e:
            logger.warning(f"Email sending error: {e!s}")
            if not settings.DEBUG and not settings.TESTING:
                raise

    return Result.ok(
        {
            "code": code,
            "magic_link": magic_link,
        }
    )
