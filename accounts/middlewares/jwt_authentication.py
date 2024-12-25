from rest_framework import authentication
from rest_framework import exceptions
import jwt
from django.utils import timezone
from django.conf import settings
from accounts.models import UserToken

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        if not auth_header.startswith('Bearer '):
            return None

        try:
            token = auth_header.split(' ')[1]
            
            # Decode token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
            # Verify token in database
            token_obj = UserToken.objects.get(
                token=token,
                is_valid=True,
                expires_at__gt=timezone.now()
            )
            
            # Add payload to request for later use
            request.token_payload = payload
            
            # Update last used
            token_obj.last_used_at = timezone.now()
            token_obj.save()
            
            return (token_obj.user, token)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except UserToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('Token not found')

    def authenticate_header(self, request):
        return 'Bearer'