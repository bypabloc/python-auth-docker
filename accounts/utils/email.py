from __future__ import annotations

from datetime import timedelta
from random import choices as random_choices
from string import digits as string_digits
from typing import Any

from boto3 import client as boto3_client
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models.verification_code import VerificationCode
from utils.logger import logger
from utils.result_as_values import Result


def generate_verification_code() -> Result[str]:
    """Generate a random 6-digit verification code."""
    return Result.ok("".join(random_choices(string_digits, k=6)))


def send_verification_email(
    user: User | AbstractUser,
    code_type: str,
) -> Result[dict[str, Any]]:
    """Send verification email to user.

    Args:
        user: CustomUser instance
        code_type: String ('registration' or 'login')
    """
    # Eliminar códigos anteriores no usados del mismo tipo
    VerificationCode.objects.filter(
        user=user,
        type=code_type,
        is_used=False,
    ).delete()

    result_generate_verification_code = generate_verification_code()
    expires_at = timezone.now() + timedelta(minutes=10)

    code = result_generate_verification_code.value

    # Create verification code record
    VerificationCode.objects.create(
        user=user,
        code=code,
        expires_at=expires_at,
        type=code_type,
    )

    subject = "Your Verification Code"
    message = f"Your verification code is: {code}\nThis code will expire in 10 minutes."

    if settings.SEND_EMAIL:
        try:
            client_params = {
                "service_name": "ses",
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                "region_name": settings.AWS_REGION_NAME,
            }

            # Create a new SES client
            ses_client = boto3_client(
                **client_params,
            )

            send_email_params = {
                "Source": settings.DEFAULT_FROM_EMAIL,
                "Destination": {"ToAddresses": ["pacg1991@gmail.com"]},
                "Message": {
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": message, "Charset": "UTF-8"}},
                },
            }

            # Send email through SES
            response = ses_client.send_email(**send_email_params)
            logger.info(f"Email sent! Message ID: {response['MessageId']}")
        except ClientError as e:
            logger.info(f"An error occurred: {e.response['Error']['Message']}")
            # Here you might want to handle the error appropriately,
            # such as logging it or raising a custom exception

    return Result.ok(
        {
            "code": code,
            "expires_at": expires_at,
        }
    )
