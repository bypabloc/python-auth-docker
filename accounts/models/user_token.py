from django.db.models import Model
from django.db.models import DateTimeField
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import ForeignKey
from django.db.models import TextField
from django.db.models import CASCADE
from django.utils.translation import gettext_lazy as _

from accounts.models.custom_user import CustomUser


class UserToken(Model):
    user = ForeignKey(CustomUser, on_delete=CASCADE, related_name='tokens')
    token = TextField()
    device_type = CharField(max_length=50)
    device_os = CharField(max_length=50)
    device_browser = CharField(max_length=50)
    is_valid = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()
    last_used_at = DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user token')
        verbose_name_plural = _('user tokens')
