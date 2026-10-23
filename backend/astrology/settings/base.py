"""Base settings shared by all environments. Values come from env / .env."""
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-key-change-me-in-every-real-environment")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    # local
    "apps.core",
    "apps.accounts",
    "apps.places",
    "apps.profiles",
    "apps.vedic",
    "apps.billing",
    "apps.daily",
    "apps.remedies",
    "apps.journal",
    "apps.alerts",
    "apps.web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "astrology.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "astrology.wsgi.application"
ASGI_APPLICATION = "astrology.asgi.application"

DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --- Data files ---------------------------------------------------------------------
DATA_DIR = Path(env("DATA_DIR", default=str(BASE_DIR / "data")))
EPHEMERIS_PATH = Path(env("EPHEMERIS_PATH", default=str(DATA_DIR)))

# --- Email (Django 6.1 MAILERS) --------------------------------------------------------
SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
NITROSEND_BACKEND = "apps.core.mail.NitrosendBackend"
CONSOLE_BACKEND = "django.core.mail.backends.console.EmailBackend"
# Short names accepted for EMAIL_BACKEND.
EMAIL_BACKEND_ALIASES = {"nitrosend": NITROSEND_BACKEND, "smtp": SMTP_BACKEND, "console": CONSOLE_BACKEND}


def build_mailers(default_backend: str) -> dict:
    backend = env("EMAIL_BACKEND", default=default_backend)
    backend = EMAIL_BACKEND_ALIASES.get(backend.lower(), backend)
    mailer = {"BACKEND": backend}
    if backend == NITROSEND_BACKEND:
        mailer["OPTIONS"] = {
            "api_key": env("NITROSEND_API_KEY", default=""),
            "base_url": env("NITROSEND_API_URL", default="https://api.nitrosend.com/v1/my"),
            "timeout": env.float("NITROSEND_TIMEOUT", default=20),
        }
    elif backend == SMTP_BACKEND:
        mailer["OPTIONS"] = {
            "host": env("EMAIL_HOST", default="localhost"),
            "port": env.int("EMAIL_PORT", default=587),
            "username": env("EMAIL_HOST_USER", default=""),
            "password": env("EMAIL_HOST_PASSWORD", default=""),
            "use_tls": env.bool("EMAIL_USE_TLS", default=True),
        }
    return {"default": mailer}


# Development defaults to the console backend (set EMAIL_BACKEND=nitrosend to send for real);
# prod.py defaults to Nitrosend.
MAILERS = build_mailers(CONSOLE_BACKEND)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Astrology <no-reply@example.com>")
# Branding used in emails (match frontend/brand.config.js).
APP_NAME = env("APP_NAME", default="Guru Drishti")
APP_TAGLINE = env("APP_TAGLINE", default="Vedic daily companion")
EMAIL_ACCENT_COLOR = env("EMAIL_ACCENT_COLOR", default="#B0722F")

# --- Cache (throttling) -------------------------------------------------------------
CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://")}

# --- DRF ----------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", default="60/min"),
        "user": env("THROTTLE_USER", default="300/min"),
        "auth": env("THROTTLE_AUTH", default="10/min"),
        "otp": env("THROTTLE_OTP", default="5/min"),
        "compute": env("THROTTLE_COMPUTE", default="60/min"),
        "places": env("THROTTLE_PLACES", default="120/min"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=30)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Astrology API",
    "DESCRIPTION": "Auth, birth profiles, places and the Vedic astrology engine.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# --- App settings -------------------------------------------------------------------
ENABLE_TEST_UI = env.bool("ENABLE_TEST_UI", default=False)
OTP_TTL_MINUTES = env.int("OTP_TTL_MINUTES", default=10)
OTP_MAX_ATTEMPTS = env.int("OTP_MAX_ATTEMPTS", default=5)
REQUIRE_EMAIL_VERIFICATION = env.bool("REQUIRE_EMAIL_VERIFICATION", default=True)

# Pro plan (billing integration comes later; prices are display values)
PRO_TRIAL_DAYS = env.int("PRO_TRIAL_DAYS", default=7)
PRO_CURRENCY = env("PRO_CURRENCY", default="INR")
PRO_PRICE_MONTHLY = env.int("PRO_PRICE_MONTHLY", default=299)
PRO_PRICE_ANNUAL = env.int("PRO_PRICE_ANNUAL", default=2499)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
    "loggers": {"django.db.backends": {"level": "WARNING"}},
}
