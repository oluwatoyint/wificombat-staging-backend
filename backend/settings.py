import os
from pathlib import Path
from urllib.parse import urlparse
from datetime import timedelta
import environ
import dj_database_url

# 1. Define BASE_DIR first
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Initialize env
env = environ.Env(
    DEBUG=(bool, False),
    APP_ENV=(str, "production"),
)

# 3. Only read the .env file if it exists (usually only in local dev)
# This prevents a local .env from overwriting Railway's real variables
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# 4. Proceed with other settings
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG", default=False)

APP_ENV = env("APP_ENV", default="production")
APP_NAME = env("APP_NAME", default="wificombat")
DEEP_SEEK_API_KEY = env("DEEP_SEEK_API_KEY", default=None)

# -----------------------------------------------------------------------
# ALLOWED HOSTS
# Supports: production domain, Railway auto-generated URLs, Vercel preview
# -----------------------------------------------------------------------
ALLOWED_HOSTS = [
    "backend.wificombatelearn.com",
    ".railway.app",      # Allows any Railway-provided URL
    "localhost",         # Allows local testing
    "127.0.0.1",
]

# Railway injects RAILWAY_PUBLIC_DOMAIN automatically
RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

# Support any .railway.app subdomain (staging preview URLs)
ALLOWED_HOSTS.append(".railway.app")

ADDITIONAL_ALLOWED_HOSTS = os.getenv("ADDITIONAL_ALLOWED_HOSTS", default=None)
if ADDITIONAL_ALLOWED_HOSTS:
    for host in ADDITIONAL_ALLOWED_HOSTS.split(","):
        host = host.strip()
        url = urlparse(host)
        hostname = url.hostname if url.hostname else host
        if hostname and hostname not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(hostname)

if DEBUG:
    ALLOWED_HOSTS += ["127.0.0.1", "localhost"]

# -----------------------------------------------------------------------
# External service config
# -----------------------------------------------------------------------
PUSH_NOTIFICATION_URL = os.getenv("PUSH_NOTIFICATION_URL", default=None)
FLUTTERWAVE_PUBLIC_KEY = os.getenv("FLUTTERWAVE_PUBLIC_KEY")
FLUTTERWAVE_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY")
FLUTTERWAVE_WEBHOOK_URL = os.getenv("FLUTTERWAVE_WEBHOOK_URL")
FLUTTERWAVE_SECRET_HASH = os.getenv("FLUTTERWAVE_SECRET_HASH")

AUTH_USER_MODEL = "core.User"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "daphne",
    "django.contrib.staticfiles",
    # Personal apps
    "api.apps.ApiConfig",
    "core.apps.CoreConfig",
    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "corsheaders",
    "channels",
    "django_redis",
    "storages",
    "django_celery_beat",
    "whitenoise.runserver_nostatic",  # WhiteNoise for staging static files
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # WhiteNoise — must be after SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

# -----------------------------------------------------------------------
# DATABASE — Railway injects DATABASE_URL automatically when you add
# a PostgreSQL plugin to your Railway project.
# -----------------------------------------------------------------------
# Force connection to the proxy address to bypass DNS resolution issues
DATABASES = {
    'default': dj_database_url.parse('postgresql://postgres:gHdRWgIIrfDYHDvDDAtizUzRMjfKPQkc@metro.proxy.rlwy.net:21679/railway')
}

# Explicitly ensure SSL is enabled for the proxy connection
DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

# -----------------------------------------------------------------------
# CORS — wide open for staging; tighten before going to production
# -----------------------------------------------------------------------
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization", "content-type",
    "dnt", "origin", "user-agent", "x-csrftoken", "x-requested-with",
]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
DATE_INPUT_FORMATS = ["%d-%m-%Y"]

# -----------------------------------------------------------------------
# STATIC & MEDIA FILES
# Staging: WhiteNoise serves static files directly from Railway.
# Production: Switch to S3 by setting APP_ENV=prod and AWS_* vars.
# -----------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# S3 storage — only activated when APP_ENV is "prod"
if APP_ENV == "prod":
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_S3_FILE_OVERWRITE = False
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
    }

# -----------------------------------------------------------------------
# REDIS — Railway Redis plugin injects REDIS_URL automatically.
# -----------------------------------------------------------------------
REDIS_URL = os.getenv("CUSTOM_REDIS_URL") or os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL", "redis://localhost:6379")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": APP_NAME,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    },
}

# -----------------------------------------------------------------------
# CELERY
# -----------------------------------------------------------------------
CELERY_BROKER_URL = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "run-every-minute": {
        "task": "core.tasks.my_scheduled_task",
        "schedule": crontab(minute="*"),
    },
}

# -----------------------------------------------------------------------
# REST FRAMEWORK
# -----------------------------------------------------------------------
REST_USE_JWT = True
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "backend.utils.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=365),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

# -----------------------------------------------------------------------
# EMAIL
# -----------------------------------------------------------------------
EMAIL_BACKEND = os.getenv("MAIL_DRIVER", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("MAIL_HOST")
EMAIL_PORT = os.getenv("MAIL_PORT")
EMAIL_HOST_USER = os.getenv("MAIL_USERNAME")
EMAIL_HOST_PASSWORD = os.getenv("MAIL_PASSWORD")
EMAIL_USE_TLS = os.getenv("MAIL_ENCRYPTION")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CSRF_HEADER_NAME = "HTTP_X_CSRF_TOKEN"

# -----------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
