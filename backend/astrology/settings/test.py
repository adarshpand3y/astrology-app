from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK

DEBUG = False
ENABLE_TEST_UI = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {k: "10000/min" for k in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]}
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
