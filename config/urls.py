from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Rotas principais do sistema
    path("", include("users.urls")),   # login, logout, registro, etc.
    path("", include("core.urls")),    # dashboard, histórico, dependências, etc.

    # Redireciona a raiz do site para o login ou dashboard
    path("", RedirectView.as_view(pattern_name="login", permanent=False)),
]
