from __future__ import annotations

from django.urls import path

from projects.api import create_project_post
from projects.api import delete_project
from projects.api import get_project
from projects.api import list_projects
from projects.api import update_project

app_name = "projects"

urlpatterns = [
    path("", list_projects, name="list-projects"),
    path("create/", create_project_post, name="create-project"),
    path("<int:project_id>/", get_project, name="get-project"),
    path("<int:project_id>/update/", update_project, name="update-project"),
    path("<int:project_id>/delete/", delete_project, name="delete-project"),
]
