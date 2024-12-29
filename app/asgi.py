from __future__ import annotations

from os import environ as os_environ

from django.core.asgi import get_asgi_application

os_environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = get_asgi_application()
