from __future__ import annotations

from django.contrib import admin
from django.urls import include
from django.urls import path

from app.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),  # Ruta raíz
    path("admin/", admin.site.urls),
    path("api/", include("accounts.urls")),
    path("api/", include("projects.urls")),
    path("api/", include("tasks.urls")),
]
