from django.db.models import Model
from django.db.models import DateTimeField
from django.db.models import BooleanField
from django.db.models import CharField
from django.utils.translation import gettext_lazy as _


class MFAMethod(Model):
    name = CharField(
        max_length=20,
        unique=True,
        choices=[
            ('otp', 'One-Time Password'),
            ('email', 'Email Verification')
        ]
    )
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('MFA method')
        verbose_name_plural = _('MFA methods')

    def __str__(self):
        return self.get_name_display()
