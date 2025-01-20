from factory.django import DjangoModelFactory
from factory import Faker
from factory import SubFactory
from factory import LazyFunction

from datetime import datetime, timedelta
from django.utils import timezone

from accounts.models.custom_user import CustomUser
from accounts.models.user_token import UserToken


class CustomUserFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser

    username = Faker("user_name")
    email = Faker("email")
    password = "testpass123"
    is_verified = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to use create_user for password hashing."""
        manager = cls._get_manager(model_class)
        is_verified = kwargs.pop("is_verified", False)
        user = manager.create_user(*args, **kwargs)
        if is_verified:
            user.is_verified = True
            user.save()

        return user

    @classmethod
    def create_verified(cls, **kwargs):
        """Helper method to create verified user."""
        return cls.create(is_verified=True, **kwargs)


class UserTokenFactory(DjangoModelFactory):
    class Meta:
        model = UserToken

    user = SubFactory(CustomUserFactory)
    token = Faker("uuid4")
    device_type = "mobile"  # Default value, can be overridden
    device_os = "iOS"  # Default value, can be overridden
    device_browser = "Safari"  # Default value, can be overridden
    is_valid = True
    expires_at = LazyFunction(lambda: timezone.now() + timedelta(days=7))

    class Params:
        """Factory parameters for different token types."""

        permanent = True

    @classmethod
    def create_permanent(cls, **kwargs):
        """Create a permanent token with 30 days expiration."""
        expires_at = timezone.now() + timedelta(days=30)
        return cls.create(expires_at=expires_at, **kwargs)

    @classmethod
    def create_temporary(cls, **kwargs):
        """Create a temporary token with 1 hour expiration."""
        expires_at = timezone.now() + timedelta(hours=1)
        return cls.create(expires_at=expires_at, **kwargs)

    @classmethod
    def create_expired(cls, **kwargs):
        """Create an expired token."""
        expires_at = timezone.now() - timedelta(days=1)
        return cls.create(expires_at=expires_at, **kwargs)

    @classmethod
    def create_with_device(cls, device_type, device_os, device_browser, **kwargs):
        """Create a token with specific device information."""
        return cls.create(
            device_type=device_type,
            device_os=device_os,
            device_browser=device_browser,
            **kwargs,
        )
