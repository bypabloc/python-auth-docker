from django.contrib import admin
from django.urls import path, include
from app.views import HomeView


urlpatterns = [
    path('', HomeView.as_view(), name='home'),  # Ruta raíz
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
]
