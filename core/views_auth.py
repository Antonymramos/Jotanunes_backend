# core/views_auth.py
import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as dj_login, logout as dj_logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET


@require_GET
@ensure_csrf_cookie
def csrf_view(request):
    """
    Apenas garante que o cookie 'csrftoken' seja definido.
    """
    return JsonResponse({"detail": "ok"})


@require_POST
@csrf_protect
def login_view(request):
    """
    Aceita username OU e-mail em 'username'.
    body: {"username": "...", "password": "..."}
    """
    try:
        data = json.loads(request.body.decode() or "{}")
    except Exception:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    identifier = (data.get("username") or data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not identifier or not password:
        return JsonResponse({"detail": "Credenciais ausentes"}, status=400)

    # Se parece e-mail, converte para username real
    username = identifier
    if "@" in identifier:
        try:
            u = User.objects.get(email__iexact=identifier)
            username = u.username
        except User.DoesNotExist:
            return JsonResponse({"detail": "Usuário ou senha inválidos"}, status=400)

    user = authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({"detail": "Usuário ou senha inválidos"}, status=400)

    dj_login(request, user)
    return JsonResponse({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    })


@require_POST
@csrf_protect
def logout_view(request):
    dj_logout(request)
    return JsonResponse({"detail": "ok"})


@require_GET
def whoami_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Unauthenticated"}, status=401)
    u = request.user
    return JsonResponse({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
    })


# Alias /me/ para compatibilidade com o front antigo
@require_GET
def me_view(request):
    return whoami_view(request)
