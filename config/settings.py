# --- topo do arquivo ---
import os
from pathlib import Path
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

# Segurança e debug (em produção: defina SECRET_KEY via ambiente)
SECRET_KEY = os.getenv("SECRET_KEY") or get_random_secret_key()
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Idioma e tz
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Maceio"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DB toggle sqlite/sqlserver ---
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").lower()
if DB_BACKEND == "sqlserver":
    DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'AGenreciadorJn',
        'USER': 'sa',
        'PASSWORD': '@Senha123',  # Substitua pela senha real do SQL Server
        'HOST': 'localhost',
        'PORT': '1433',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'unicode_results': True,
            'extra_params': 'Encrypt=no;TrustServerCertificate=yes',
        },
    },
}
else:
    DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'AGenreciadorJn',
        'USER': 'sa',
        'PASSWORD': '@Senha123',  # Substitua pela senha real do SQL Server
        'HOST': 'localhost',
        'PORT': '1433',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'unicode_results': True,
            'extra_params': 'Encrypt=no;TrustServerCertificate=yes',
        },
    },
}

INSTALLED_APPS = [
    # Django core
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',

    # Third-party
    'corsheaders','rest_framework','django_filters','drf_spectacular',

    # Seus apps
    'core',
    'customizacoes.apps.CustomizacoesConfig',
    'ai.apps.AiConfig',              # <= ADICIONE ESTA LINHA
]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # <= só uma vez, aqui no topo
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'core.middleware.CurrentUserMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# --- CORS/CSRF para dev com frontend em Vite (porta 5173) ---
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",

]
# Se você tinha CORS_ALLOW_ALL_ORIGINS = True, REMOVA/COMENTE.

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
]

# Cookies em dev (http)
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
# Em DEV: para testar sem login
# (se quiser fechado, comente esse bloco)
# if os.getenv("DEV_OPEN_API", "1") == "1" and DEBUG:
    # REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = []
    # REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = ["rest_framework.permissions.AllowAny"]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    # Padrão: fechado (exige autenticação)
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

# Abrir tudo só em dev quando quiser testar sem login
if os.getenv("DEV_OPEN_API", "1") == "1" and DEBUG:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = []
    REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = ["rest_framework.permissions.AllowAny"]

SPECTACULAR_SETTINGS = {
    "TITLE": "API - Gestão de Customizações RM",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# ========= E-mail (SMTP) =========
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")            # ex.: smtp.gmail.com
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))    # 587(TLS) ou 465(SSL)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@localhost")
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# Em dev, se não houver SMTP configurado, imprime no console
if DEBUG and not EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# (Opcional) Perfis/hierarquia — você disse que ajusta depois:
# PROFILE_RANKS = {"OPERADOR":0,"ANALISTA":1,"COORDENADOR":2,"GESTOR":3}
# PROFILE_DEFAULT = "OPERADOR"
