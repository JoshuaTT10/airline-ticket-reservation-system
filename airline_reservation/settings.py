import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


DEBUG = os.environ.get(
    "DJANGO_DEBUG",
    "True",
).lower() in {
    "1",
    "true",
    "yes",
}


SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-development-key"
    else:
        raise RuntimeError("SECRET_KEY must be configured when DEBUG is False.")


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)


extra_allowed_hosts = os.environ.get(
    "ALLOWED_HOSTS",
    "",
)

if extra_allowed_hosts:
    ALLOWED_HOSTS.extend(
        host.strip() for host in (extra_allowed_hosts.split(",")) if host.strip()
    )


CSRF_TRUSTED_ORIGINS = []


if render_hostname:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_hostname}")


extra_csrf_origins = os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    "",
)

if extra_csrf_origins:
    CSRF_TRUSTED_ORIGINS.extend(
        origin.strip() for origin in (extra_csrf_origins.split(",")) if origin.strip()
    )


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "reservations",
]


MIDDLEWARE = [
    ("django.middleware.security.SecurityMiddleware"),
    ("whitenoise.middleware.WhiteNoiseMiddleware"),
    ("django.contrib.sessions.middleware.SessionMiddleware"),
    ("django_htmx.middleware.HtmxMiddleware"),
    ("django.middleware.common.CommonMiddleware"),
    ("django.middleware.csrf.CsrfViewMiddleware"),
    ("django.contrib.auth.middleware.AuthenticationMiddleware"),
    ("django.contrib.messages.middleware.MessageMiddleware"),
    ("django.middleware.clickjacking.XFrameOptionsMiddleware"),
]


ROOT_URLCONF = "airline_reservation.urls"


TEMPLATES = [
    {
        "BACKEND": ("django.template.backends.django.DjangoTemplates"),
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                ("django.template.context_processors.request"),
                ("django.contrib.auth.context_processors.auth"),
                ("django.contrib.messages.context_processors.messages"),
            ],
        },
    },
]


WSGI_APPLICATION = "airline_reservation.wsgi.application"


ASGI_APPLICATION = "airline_reservation.asgi.application"


database_url = os.environ.get("DATABASE_URL")


if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

else:
    DATABASES = {
        "default": {
            "ENGINE": ("django.db.backends.sqlite3"),
            "NAME": (BASE_DIR / "db.sqlite3"),
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.MinimumLengthValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.CommonPasswordValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.NumericPasswordValidator"),
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Tokyo"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": ("django.core.files.storage.FileSystemStorage"),
        },
        "staticfiles": {
            "BACKEND": ("django.contrib.staticfiles.storage.StaticFilesStorage"),
        },
    }

else:
    STORAGES = {
        "default": {
            "BACKEND": ("django.core.files.storage.FileSystemStorage"),
        },
        "staticfiles": {
            "BACKEND": ("whitenoise.storage.CompressedManifestStaticFilesStorage"),
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


LOGIN_URL = "reservations:login"

LOGIN_REDIRECT_URL = "reservations:home"

LOGOUT_REDIRECT_URL = "reservations:home"


SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


if not DEBUG:
    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_SSL_REDIRECT = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = "DENY"
