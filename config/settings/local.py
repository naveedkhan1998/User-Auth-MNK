from .base import *  # noqa: F403, F401
from .base import (
    BASE_DIR,
    SIMPLE_JWT,  # noqa: F401
)


SECRET_KEY = "django-insecure-3e5av)!)m@!8o)95ha%lp08x#f(-9s)-o)!6u$3_2hwv)&rb3r"

DEBUG = True


ALLOWED_HOSTS = ["*"]
HOST = "localhost"


# CORS settings for development
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:3000",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:3000",
]

X_FRAME_OPTIONS = "ALLOW-FROM http://localhost:3000/"

# Update JWT settings with local secret key
SIMPLE_JWT.update(
    {
        "SIGNING_KEY": SECRET_KEY,
    }
)

# Local development: Use the filesystem for static and media files

STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "static/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"
OUTPUT_ROOT = BASE_DIR / "OUTPUTS"
OUTPUT_URL = "outputs/"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "mydatabase",
    }
}