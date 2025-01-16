from __future__ import annotations

from django.urls import path

from tasks.api import create_comment_post
from tasks.api import create_task_post
from tasks.api import delete_task
from tasks.api import get_task
from tasks.api import list_tasks_get
from tasks.api import update_task

app_name = "tasks"

urlpatterns = [
    path("projects/<int:project_id>/tasks/", list_tasks_get, name="list-tasks"),
    path(
        "projects/<int:project_id>/tasks/create/", create_task_post, name="create-task"
    ),
    path("projects/<int:project_id>/tasks/<int:task_id>/", get_task, name="get-task"),
    path(
        "projects/<int:project_id>/tasks/<int:task_id>/update/",
        update_task,
        name="update-task",
    ),
    path(
        "projects/<int:project_id>/tasks/<int:task_id>/delete/",
        delete_task,
        name="delete-task",
    ),
    path(
        "projects/<int:project_id>/tasks/<int:task_id>/comments/",
        create_comment_post,
        name="create-comment",
    ),
]
