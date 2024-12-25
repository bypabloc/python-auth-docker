from django.urls import path
from .views import RegisterView
from .views import LoginView
from .views import LogoutView
from .views import VerifyCodeView
from .views import ResendCodeView
from .views import ListMFAMethodsView
from .views import ConfigureMFAView
from .views import VerifyMFAView

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('resend-code/', ResendCodeView.as_view(), name='resend-code'),
    path('mfa/methods/', ListMFAMethodsView.as_view(), name='mfa-methods'),
    path('mfa/configure/', ConfigureMFAView.as_view(), name='configure-mfa'),
    path('mfa/verify/', VerifyMFAView.as_view(), name='verify-mfa'),
]
