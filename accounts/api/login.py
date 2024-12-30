from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from accounts.models.custom_user import CustomUser
from accounts.models.mfa_verification import MFAVerification
from accounts.models.user_mfa import UserMFA
from accounts.serializers.login import Login as LoginSerializer
from accounts.serializers.user import User as UserSerializer
from accounts.utils.email import generate_verification_code
from accounts.utils.email import send_verification_email
from accounts.utils.generate_token_for_user import generate_token_for_user
from utils.custom_response import CustomResponse
from utils.custom_response import ResponseConfig
from utils.decorators.log_api import log_api
from utils.logger import logger
from utils.result_as_values import Result
from utils.result_as_values import handle_result


@handle_result
def validate_login_data(
    request_data: dict,
) -> Result[dict]:
    """Validate login request data using serializer."""
    serializer = LoginSerializer(data=request_data)
    if not serializer.is_valid():
        return Result.fail(
            "invalid_login_data",
            "Invalid login data",
            details=serializer.errors.__dict__,
        )
    return Result.ok(request_data)


@handle_result
def authenticate_user(
    email: str | None,
    username: str | None,
    password: str,
) -> Result[CustomUser]:
    """Authenticate user with provided credentials."""
    user = authenticate(username=email or username, password=password)
    if not user:
        return Result.fail(
            "invalid_credentials",
            "Invalid credentials",
        )
    return Result.ok(user)


@handle_result
def handle_unverified_user(
    user: User,
    request: Request,
) -> Result[dict[str, Any]]:
    """Handle login attempt for unverified user."""
    result_token = generate_token_for_user(
        user=user,
        request=request,
        is_temporary=True,
    )
    if result_token.is_error:
        return Result.fail(
            "error_generating_token",
            "Error generating token",
        )

    result_verification = send_verification_email(
        user=user,
        code_type="login",
    )
    if result_verification.is_error:
        return Result.fail(
            "error_sending_verification_email",
            "Error sending verification email",
        )

    response_data = {
        "user": UserSerializer(user).data,
        "token": result_token.value["token"],
        "requires_verification": True,
        "verification_type": "email",
    }

    if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
        response_data["verification"] = result_verification.value

    return Result.ok(response_data)


@handle_result
def create_mfa_verification(
    user: User,
    token: str,
) -> Result[dict[str, Any]]:
    """Create MFA verification record and send email."""
    try:
        code = generate_verification_code()
        verification = MFAVerification.objects.create(
            user=user,
            method=user.mfa_config.default_method,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10),
            session_key=token,
        )
    except Exception as e:
        return Result.fail(
            "error_creating_mfa_verification",
            "Error creating MFA verification",
            details={"error": str(e)},
        )

    result_verification = send_verification_email(
        user=user,
        code_type="mfa",
    )
    if result_verification.is_error:
        return Result.fail(
            "error_sending_mfa_email",
            "Error sending MFA email",
        )

    verification_data = {}
    if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
        verification_data["verification"] = {
            "code": code,
            "expires_at": verification.expires_at,
        }

    return Result.ok(
        verification_data,
    )


@handle_result
def handle_mfa_verification(
    user: User,
    request: Request,
) -> Result[dict[str, Any]]:
    """Handle MFA verification if enabled."""
    try:
        mfa_config = user.mfa_config
        if not mfa_config.is_enabled:
            return Result.ok(
                {
                    "requires_verification": True,
                }
            )

        result_token = generate_token_for_user(
            user=user,
            request=request,
            is_temporary=True,
        )
        if result_token.is_error:
            return Result.fail(
                kind="error_generating_token",
                message="Error generating token",
            )

        token = result_token.value["token"]
        response_data = {
            "message": "MFA verification required",
            "token": token,
            "requires_verification": True,
            "verification_type": "mfa",
            "mfa_method": mfa_config.default_method.name,
        }

        if mfa_config.default_method.name == "email":
            result_mfa = create_mfa_verification(
                user,
                token,
            )
            if result_mfa.is_error:
                return Result.fail(
                    kind="error_creating_mfa_verification",
                    message="Error creating MFA verification",
                )
            response_data.update(result_mfa.value or {})

        return Result.ok(
            response_data,
        )
    except UserMFA.DoesNotExist:
        return Result.ok(
            {
                "requires_verification": True,
                "UserMFA.DoesNotExist": True,
            }
        )


@handle_result
def generate_final_token(
    user: User,
    request: Request,
) -> Result[dict[str, Any]]:
    """Generate final authentication token."""
    result_token = generate_token_for_user(
        user=user,
        request=request,
        is_temporary=False,
    )
    if result_token.is_error:
        return Result.fail(
            "error_generating_final_token",
            "Error generating final token",
        )

    return Result.ok(
        {
            "user": UserSerializer(user).data,
            "token": result_token.value["token"],
            "requires_verification": False,
        }
    )


def create_response_from_result(
    result: Result,
    success_config: ResponseConfig | None = None,
    error_status: int = 500,
) -> CustomResponse:
    """Transform a Result into a CustomResponse."""
    if result.is_error:
        return CustomResponse(
            ResponseConfig(
                status=error_status,
                message=result.error.message,
                errors=(
                    result.error.details
                    if result.error.details
                    else {"error": result.error.message}
                ),
            )
        )
    return CustomResponse(success_config or ResponseConfig(data=result.value))


@api_view(["POST"])
@permission_classes([AllowAny])
@log_api
def post(
    request: Request,
) -> CustomResponse:
    """Login the user."""
    # Validate request data
    result_validation = validate_login_data(
        request.data,
    )
    if result_validation.is_error:
        result_validation_error = result_validation.error
        return CustomResponse(
            ResponseConfig(
                message=result_validation_error.message,
                errors=result_validation_error.details,
                code=result_validation_error.kind,
                status=422,
            )
        )

    # Authenticate user
    data = result_validation.value
    result_auth = authenticate_user(
        data.get("email"),
        data.get("username"),
        data.get("password"),
    )
    if result_auth.is_error:
        result_auth_error = result_auth.error
        return CustomResponse(
            ResponseConfig(
                message=result_auth_error.message,
                errors=result_auth_error.details,
                code=result_auth_error.kind,
                status=401,
            )
        )

    # Handle unverified user
    user = result_auth.value
    if not user.is_verified:
        result_unverified = handle_unverified_user(
            user,
            request,
        )
        if result_unverified.is_error:
            result_unverified_error = result_unverified.error
            return CustomResponse(
                ResponseConfig(
                    message=result_unverified_error.message,
                    errors=result_unverified_error.details,
                    code=result_unverified_error.kind,
                    status=401,
                )
            )

        return CustomResponse(
            ResponseConfig(
                message="Please verify your email first.",
                code="email_not_verified",
                status=400,
            )
        )

    # Handle MFA verification
    result_mfa = handle_mfa_verification(
        user=user,
        request=request,
    )
    if result_mfa.is_error:
        result_mfa_error = result_mfa.error
        return CustomResponse(
            ResponseConfig(
                message=result_mfa_error.message,
                code=result_mfa_error.kind,
                status=400,
            )
        )

    logger.info(
        "MFA verification required",
        extra=result_mfa.__dict__,
    )

    # Si hay respuesta de MFA pero no es None, significa que se requiere MFA
    if result_mfa.value["requires_verification"] and user.is_verified:
        return CustomResponse(
            ResponseConfig(
                message="MFA verification required",
                code="mfa_verification_required",
            )
        )

    # Generate final token
    result_token = generate_final_token(
        user=user,
        request=request,
    )

    result_token_value = result_token.value
    return CustomResponse(
        ResponseConfig(
            message="Login successful",
            code="success",
            data=result_token_value,
        )
    )
