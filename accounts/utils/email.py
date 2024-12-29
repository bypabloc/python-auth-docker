from __future__ import annotations

import random
import string
from datetime import timedelta

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models.verification_code import VerificationCode
from utils.logger import logger


def generate_verification_code() -> str:
    """Generate a random 6-digit verification code."""
    return "".join(random.choices(string.digits, k=6))


def send_verification_email(user: User, code_type: str) -> dict:
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

    code = generate_verification_code()
    expires_at = timezone.now() + timedelta(minutes=10)

    # Create verification code record
    VerificationCode.objects.create(
        user=user, code=code, expires_at=expires_at, type=code_type
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
            ses_client = boto3.client(
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

    return {
        "code": code,
        "expires_at": expires_at,
    }
