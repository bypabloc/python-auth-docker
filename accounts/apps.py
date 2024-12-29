from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """App config for accounts."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        """Override this to put in."""
        # import accounts.signals
        pass
