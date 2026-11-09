#Arquivo de configuração do Django, com ajustes para a API REST e o drf-spectacular.

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

DEBUG = os.getenv('DJANGO_DEBUG', '0') == '1'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY') or ('apenas-para-desenvolvimento-local' if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError('Defina DJANGO_SECRET_KEY (obrigatória com DEBUG=0).')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    'locadora',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# DB_ENGINE=sqlite -> desenvolvimento e testes rápidos
# DB_ENGINE=postgres -> produção (e CI, para garantir que o SQL roda nos dois)
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite')
if DB_ENGINE == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'easycar'),
            'USER': os.getenv('POSTGRES_USER', 'easycar'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 60,
            'CONN_HEALTH_CHECKS': True,
        }
    }
elif DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.getenv('SQLITE_PATH', BASE_DIR / 'db.sqlite3'),
        }
    }
else:
    raise RuntimeError(f'DB_ENGINE inválido: {DB_ENGINE!r} (use sqlite ou postgres).')

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Depois do login pela web (/api-auth/login/), volta para a raiz da API
LOGIN_REDIRECT_URL = '/api/'

REST_FRAMEWORK = {
    # Token no cabeçalho "Authorization: Token ..." e sessão (login pela web)
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Seguro por padrão: sem login, nada. Cada view refina por grupo.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'API EasyCar',
    'DESCRIPTION': 'Aluguel de carros: clientes, carros e aluguéis, com acesso por grupos.',
    'VERSION': '1.0.0',
    # Carro e Aluguel têm um campo "status" com opções diferentes: um nome para cada
    'ENUM_NAME_OVERRIDES': {
        'StatusCarroEnum': 'locadora.models.Carro.Status',
        'StatusAluguelEnum': 'locadora.models.Aluguel.Status',
    },
}