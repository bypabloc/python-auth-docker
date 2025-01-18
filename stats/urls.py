from __future__ import annotations

from django.urls import path

from stats.api.project_stats import get_stats as get_project_stats
from stats.api.user_stats import get_stats as get_user_stats

app_name = "stats"

urlpatterns = [
    path("me/", get_user_stats, name="user-stats"),
    path("projects/<int:project_id>/", get_project_stats, name="project-stats"),
]
