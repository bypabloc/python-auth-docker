from django.db.models import Model
from django.db.models import DateTimeField
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import ForeignKey
from django.db.models import CASCADE
from django.utils.translation import gettext_lazy as _

from accounts.models.custom_user import CustomUser


class VerificationCode(Model):
    user = ForeignKey(CustomUser, on_delete=CASCADE, related_name='verification_codes')
    code = CharField(max_length=6)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()
    is_used = BooleanField(default=False)
    type = CharField(max_length=20, choices=[
        ('registration', 'Registration'),
        ('login', 'Login')
    ])

    class Meta:
        verbose_name = _('verification code')
        verbose_name_plural = _('verification codes')
