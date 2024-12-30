from __future__ import annotations

from django.urls import path

from accounts.views.configure_mfa import configure_mfa
from accounts.views.list_mfa_methods import get as list_mfa_methods_get
from accounts.views.login import post as login_post
from accounts.views.logout import post as logout_post
from accounts.views.register import post as register_post
from accounts.views.resend_code import post as resend_code_post
from accounts.views.verify_code import post as verify_code_post
from accounts.views.verify_mfa import post as verify_mfa_post

app_name = "accounts"

urlpatterns = [
    path(
        "register/",
        register_post,
        name="register",
    ),
    path(
        "login/",
        login_post,
        name="login",
    ),
    path(
        "logout/",
        logout_post,
        name="logout",
    ),
    path(
        "verify-code/",
        verify_code_post,
        name="verify-code",
    ),
    path(
        "resend-code/",
        resend_code_post,
        name="resend-code",
    ),
    path(
        "mfa/methods/",
        list_mfa_methods_get,
        name="mfa-methods",
    ),
    path(
        "mfa/configure/",
        configure_mfa,
        name="configure-mfa",
    ),
    path(
        "mfa/verify/",
        verify_mfa_post,
        name="verify-mfa",
    ),
]
