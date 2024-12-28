from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models.user_token import UserToken
from accounts.models.verification_code import VerificationCode
from accounts.serializers.user import User as UserSerializer
from accounts.serializers.verification_code import (
    VerificationCode as VerificationCodeSerializer,
)
from accounts.utils.generate_token_for_user import generate_token_for_user


class VerifyCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Check if token is temporary
        if not request.token_payload.get("is_temporary", False):
            return Response(
                {"error": "Invalid token type"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = VerificationCodeSerializer(
            data={
                "code": request.data.get("code"),
                "email": request.token_payload["email"],
            }
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        verification = (
            VerificationCode.objects.filter(
                user=user,
                code=serializer.validated_data["code"],
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .order_by("-created_at")
            .first()
        )

        if not verification:
            return Response(
                {"error": "Invalid or expired verification code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark code as used
        verification.is_used = True
        verification.save()

        # Handle registration verification
        if verification.type == "registration":
            user.is_verified = True
            user.save()

        # Generate permanent token
        token, user_token = generate_token_for_user(user, request, is_temporary=False)

        # Invalidate temporary token
        UserToken.objects.filter(user=user, token=request.auth, is_valid=True).update(
            is_valid=False
        )

        if not user.is_verified:
            user.is_verified = True
            user.save()

        # delete all verification codes for the user
        VerificationCode.objects.filter(user=user).delete()

        return Response(
            {
                "message": "Verification successful",
                "token": token,
                "user": UserSerializer(user).data,
            }
        )
