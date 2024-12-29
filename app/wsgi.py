from __future__ import annotations

from os import environ as os_environ

from django.core.wsgi import get_wsgi_application

os_environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = get_wsgi_application()
