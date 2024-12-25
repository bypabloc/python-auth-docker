from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

from accounts.serializers.user import User as UserSerializer
from accounts.utils.generate_token_for_user import generate_token_for_user
from accounts.utils.email import send_verification_email

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        # Generate temporary token
        token, _ = generate_token_for_user(user, request, is_temporary=True)
        data_verify_email = send_verification_email(user, 'registration')
        
        response_data = {
            'message': 'User created successfully. Please check your email for verification code.',
            'user': UserSerializer(user).data,
            'token': token,
        }
        
        # Solo incluir el código en entorno local
        if settings.SEND_VERIFICATION_CODE_IN_RESPONSE:
            response_data['verification'] = data_verify_email
        
        return Response(response_data, status=status.HTTP_201_CREATED)
