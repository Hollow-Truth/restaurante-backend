from pathlib import Path
import os
import dj_database_url
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD: En producción leemos la clave del entorno, en local usamos una por defecto
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-clave-para-desarrollo-local')

# DEBUG: Solo True si NO estamos en Render
DEBUG = 'RENDER' not in os.environ

# HOSTS: Permitir el dominio de Render
ALLOWED_HOSTS = ['*'] # Render se encarga de filtrar, * es seguro aquí o pon tu dominio .onrender.com

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # TERCEROS
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # MIS APPS
    'finance',
    'inventory',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # <--- VITAL PARA ESTILOS EN RENDER
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',      # <--- CORS SIEMPRE ARRIBA
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend_restaurante.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend_restaurante.wsgi.application'

# BASE DE DATOS INTELIGENTE
# Si Render nos da una DATABASE_URL, usamos PostgreSQL. Si no, SQLite.
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}

# VALIDACIÓN DE PASSWORD (Desactivada para desarrollo, activar en prod si quieres)
AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'es-bo' # Español Bolivia
TIME_ZONE = 'America/La_Paz' # Hora correcta
USE_I18N = True
USE_TZ = True

# ARCHIVOS ESTÁTICOS
STATIC_URL = 'static/'
if not DEBUG:
    # Configuración para producción (Whitenoise)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ID DEFAULT
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT CONFIG
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# CORS - PERMISOS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    # AQUÍ AGREGAREMOS TU URL DE VERCEL CUANDO LA TENGAS
    # "https://mi-proyecto.vercel.app"
]
# Opción nuclear para evitar dolores de cabeza al principio (luego la quitas)
CORS_ALLOW_ALL_ORIGINS = True