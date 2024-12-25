from django.db.models import Model
from django.db.models import DateTimeField
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import ForeignKey
from django.db.models import CASCADE
from django.utils.translation import gettext_lazy as _

from accounts.models.custom_user import CustomUser
from accounts.models.mfa_method import MFAMethod


class MFAVerification(Model):
    user = ForeignKey(
        CustomUser,
        on_delete=CASCADE,
        related_name='mfa_verifications'
    )
    method = ForeignKey(
        MFAMethod,
        on_delete=CASCADE,
        related_name='verifications'
    )
    code = CharField(max_length=6)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()
    verified_at = DateTimeField(null=True, blank=True)
    is_verified = BooleanField(default=False)
    session_key = CharField(
        max_length=64,
        help_text=_('Temporary session key for MFA verification process')
    )

    class Meta:
        verbose_name = _('MFA verification')
        verbose_name_plural = _('MFA verifications')
        ordering = ['-created_at']

    def __str__(self):
        return f'MFA verification for {self.user.email} using {self.method.name}'
