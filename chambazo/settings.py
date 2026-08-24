from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-chambazo-sprint2-2026'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'rest_framework',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'chambazo.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'core' / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'chambazo.wsgi.application'
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'es-sv'
TIME_ZONE = 'America/El_Salvador'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Sprint 2 — Google Maps (key pública; en prod usar variable de entorno)
GOOGLE_MAPS_API_KEY = 'AIzaSyB41DRUbKWJHPxaFjMAwdrzWzbVKartNQ8'

# Ubicaciones reales de El Salvador para demo
SV_LOCATIONS = [
    {"nombre": "San Salvador Centro", "lat": 13.6929, "lng": -89.2182},
    {"nombre": "Santa Tecla", "lat": 13.6740, "lng": -89.2797},
    {"nombre": "Soyapango", "lat": 13.7105, "lng": -89.1520},
    {"nombre": "San Miguel", "lat": 13.4800, "lng": -88.1800},
    {"nombre": "Santa Ana", "lat": 13.9933, "lng": -89.5597},
    {"nombre": "Mejicanos", "lat": 13.7313, "lng": -89.2174},
    {"nombre": "Apopa", "lat": 13.8060, "lng": -89.1790},
    {"nombre": "Delgado", "lat": 13.7239, "lng": -89.1680},
    {"nombre": "Usulután", "lat": 13.3500, "lng": -88.4500},
    {"nombre": "Zacatecoluca", "lat": 13.5000, "lng": -88.8667},
    {"nombre": "La Libertad", "lat": 13.4833, "lng": -89.3167},
    {"nombre": "Cojutepeque", "lat": 13.7167, "lng": -88.9333},
    {"nombre": "Antiguo Cuscatlán", "lat": 13.6751, "lng": -89.2491},
    {"nombre": "San Marcos", "lat": 13.6667, "lng": -89.1833},
    {"nombre": "Ilopango", "lat": 13.7000, "lng": -89.1167},
    {"nombre": "Sonsonante", "lat": 13.7194, "lng": -89.7244},
    {"nombre": "Ahuachapán", "lat": 13.9219, "lng": -89.8453},
    {"nombre": "Chalatenango", "lat": 14.0333, "lng": -88.9333},
    {"nombre": "San Vicente", "lat": 13.6419, "lng": -88.7836},
    {"nombre": "La Unión", "lat": 13.3361, "lng": -87.8436},
]
