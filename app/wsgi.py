"""WSGI config for the Django project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It exposes a module-level variable named
`application` which is a WSGI callable.

Django's `get_wsgi_application()` function is used to initialize the WSGI
application with the settings module specified in the DJANGO_SETTINGS_MODULE
environment variable.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

application = get_wsgi_application()
