from __future__ import annotations

from django.apps import AppConfig


class StatsConfig(AppConfig):
    """Configuration for the stats app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "stats"
