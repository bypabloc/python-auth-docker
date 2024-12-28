from django.contrib.auth.models import AbstractUser
from django.db.models import BooleanField, DateTimeField, EmailField
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    email = EmailField(_("email address"), unique=True)
    is_verified = BooleanField(default=False)
    has_mfa = BooleanField(
        default=False, help_text=_("Indicates if user has configured MFA")
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
