"""ASGI config for the Django project.

This module contains the ASGI application used for serving the project.
It exposes the ASGI callable as a module-level variable named `application`.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/asgi/

Attributes:
    application (ASGIHandler): The ASGI application callable.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = get_asgi_application()
