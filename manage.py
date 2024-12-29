#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
from __future__ import annotations

from os import environ as os_environ
from sys import argv as sys_argv


def main():
    """Run administrative tasks."""
    os_environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys_argv)


if __name__ == "__main__":
    main()
