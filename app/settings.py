from __future__ import annotations

from os import environ as os_environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os_environ.get(
    "SECRET_KEY", "django-insecure-d$-*&$588rqbns7lc9kix*wnh)mr$eeb#&#v4jp!1ndq)m%ax^"
)

DEBUG = os_environ.get("DEBUG", "0") == "1"

ALLOWED_HOSTS = os_environ.get("ALLOWED_HOSTS", "").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "app.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os_environ.get("DB_NAME", "postgres"),
        "USER": os_environ.get("DB_USER", "postgres"),
        "PASSWORD": os_environ.get("DB_PASSWORD", "postgres"),
        "HOST": os_environ.get("DB_HOST", "db"),
        "PORT": os_environ.get("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.auth.jwt_authentication.JWTAuthentication",
    ],
}

if os_environ.get("RATE_LIMIT_ENABLED", "0") == "1":
    REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ]
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": "30/minute",
        "user": os_environ.get("MAX_REQUESTS_PER_MINUTE", "60") + "/minute",
    }

# Custom user model
AUTH_USER_MODEL = "accounts.CustomUser"
AUTHENTICATION_BACKENDS = [
    "accounts.auth.email_backend.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Email settings
EMAIL_BACKEND = os_environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = os_environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com")

# AWS Settings
AWS_ACCESS_KEY_ID = os_environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os_environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = os_environ.get("AWS_REGION_NAME", "us-east-1")
AWS_SES_AUTO_THROTTLE = 0.5

SEND_VERIFICATION_CODE_IN_RESPONSE = False
SEND_EMAIL = True

# Development settings
ENVIRONMENT = os_environ.get("ENVIRONMENT", "local")

if ENVIRONMENT == "local":
    SEND_VERIFICATION_CODE_IN_RESPONSE = (
        os_environ.get("SEND_VERIFICATION_CODE_IN_RESPONSE", "0") == "1"
    )
    SEND_EMAIL = os_environ.get("SEND_EMAIL", "0") == "1"

# Security settings
if not DEBUG:
    # HTTPS settings
    if os_environ.get("SECURE_SSL_REDIRECT", "0") == "1":
        SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
        SECURE_BROWSER_XSS_FILTER = True
        SECURE_CONTENT_TYPE_NOSNIFF = True

        # HSTS settings
        SECURE_HSTS_SECONDS = int(os_environ.get("SECURE_HSTS_SECONDS", 31536000))
        SECURE_HSTS_INCLUDE_SUBDOMAINS = (
            os_environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", "1") == "1"
        )
        SECURE_HSTS_PRELOAD = os_environ.get("SECURE_HSTS_PRELOAD", "1") == "1"

    # Session settings
    SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
    SESSION_COOKIE_HTTPONLY = True
