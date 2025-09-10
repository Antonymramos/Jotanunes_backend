from django.urls import path, include
from core.views_auth import csrf_view, login_view, logout_view, whoami_view, me_view

urlpatterns = [
    # AUTH
    path("auth/csrf/", csrf_view, name="auth-csrf"),
    path("auth/login/", login_view, name="auth-login"),
    path("auth/logout/", logout_view, name="auth-logout"),
    path("auth/whoami/", whoami_view, name="auth-whoami"),
    path("auth/me/", me_view, name="auth-me"),  # alias p/ compat

]
