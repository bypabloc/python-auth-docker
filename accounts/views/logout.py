from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserToken

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Only allow logout with permanent tokens
        if request.token_payload.get('is_temporary', False):
            return Response({
                'error': 'Invalid token type'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        UserToken.objects.filter(
            user=request.user,
            token=request.auth,
            is_valid=True
        ).update(is_valid=False)
            
        return Response({'message': 'Logged out successfully'})
