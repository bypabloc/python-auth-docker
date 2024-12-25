from datetime import timedelta

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings

from accounts.models import UserMFA
from accounts.models import MFAVerification
from accounts.serializers.user import User as UserSerializer
from accounts.serializers.login import Login as LoginSerializer
from accounts.utils.generate_token_for_user import generate_token_for_user
from accounts.utils.email import send_verification_email
from accounts.utils.email import generate_verification_code


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        # Check if user is verified
        if not user.is_verified:
            # For unverified users, send verification code and temporary token
            token, _ = generate_token_for_user(user, request, is_temporary=True)
            data_verify_email = send_verification_email(user, 'login')
            
            response_data = {
                'message': 'Please verify your email first.',
                'user': UserSerializer(user).data,
                'token': token,
                'requires_verification': True,
                'verification_type': 'email'
            }
            
            if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
                response_data['verification'] = data_verify_email
                
            return Response(response_data)
        
        # Check if MFA is enabled
        try:
            mfa_config = user.mfa_config
            if mfa_config.is_enabled:
                # Generate temporary token for MFA
                token, _ = generate_token_for_user(
                    user, 
                    request, 
                    is_temporary=True
                )
                
                if mfa_config.default_method.name == 'email':
                    # Send verification code
                    verification = MFAVerification.objects.create(
                        user=user,
                        method=mfa_config.default_method,
                        code=generate_verification_code(),
                        expires_at=timezone.now() + timedelta(minutes=10),
                        session_key=token
                    )
                    # Send email with code
                    send_verification_email(user, 'mfa')
                
                return Response({
                    'message': 'MFA verification required',
                    'token': token,
                    'requires_verification': True,
                    'verification_type': 'mfa',
                    'mfa_method': mfa_config.default_method.name
                })
                
        except UserMFA.DoesNotExist:
            pass
            
        # Si no hay MFA o no está habilitado, generar token permanente
        token, user_token = generate_token_for_user(
            user, 
            request, 
            is_temporary=False
        )
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'token': token,
            'requires_verification': False
        })
