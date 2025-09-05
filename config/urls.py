# config/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# JWT é opcional; fica ativo se o pacote estiver instalado
try:
    from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
    SIMPLEJWT = True
except Exception:
    SIMPLEJWT = False

urlpatterns = [
    path("admin/", admin.site.urls),

    # suas APIs
    path("api/", include("core.urls")),
    path("api/", include("customizacoes.urls")),

    # autenticação por sessão (browsable API e Swagger usam isso)
    path("api-auth/", include("rest_framework.urls")),

    # OpenAPI & Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if SIMPLEJWT:
    urlpatterns += [
        path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
        path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    ]
