from django.urls import path

from accounts.views.configure_mfa import ConfigureMFAView
from accounts.views.list_mfa_methods import ListMFAMethodsView
from accounts.views.login import LoginView
from accounts.views.logout import LogoutView
from accounts.views.register import RegisterView
from accounts.views.resend_code import ResendCodeView
from accounts.views.verify_code import VerifyCodeView
from accounts.views.verify_mfa import VerifyMFAView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verify-code/", VerifyCodeView.as_view(), name="verify-code"),
    path("resend-code/", ResendCodeView.as_view(), name="resend-code"),
    path("mfa/methods/", ListMFAMethodsView.as_view(), name="mfa-methods"),
    path("mfa/configure/", ConfigureMFAView.as_view(), name="configure-mfa"),
    path("mfa/verify/", VerifyMFAView.as_view(), name="verify-mfa"),
]
