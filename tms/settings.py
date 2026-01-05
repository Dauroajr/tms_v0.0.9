import os
from pathlib import Path

from django.conf.global_settings import LANGUAGES as DJANGO_LANGUAGES
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Criar diretório de logs se não existir
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-r32m%qg2cj-(g^&7!d%pa@6s5np9&=oql+*j7ut!y3&6z@(os1"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "audit.apps.AuditConfig",
    "core.apps.CoreConfig",
    "fleet.apps.FleetConfig",
    "personnel.apps.PersonnelConfig",
    "tenants.apps.TenantsConfig",
]


ROOT_URLCONF = "tms.urls"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = reverse_lazy("home")


WSGI_APPLICATION = "tms.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"
LANGUAGES = (
    ("pt-br", _("Português Brasileiro")),
    ("en", _("English")),
    ("es", _("Español")),
    ("fr", _("Français")),
    ("de", _("Deutsch")),
    ("it", _("Italiano")),
)

TIME_ZONE = "UTC"

USE_I18N = True
USE_L10N = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Use a leading slash for URLs and Path objects for filesystem paths.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Custom User Model
AUTH_USER_MODEL = "accounts.CustomUser"

# Middleware configuration (order matters!)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "tenants.middleware.TenantMiddleware",  # Must come after AuthenticationMiddleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Context processors
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tenants.context_processors.tenant_context",  # Add tenant context
            ],
        },
    },
]

# Tenant-specific settings
TENANT_MODEL = "tenants.Tenant"
TENANT_SUBDOMAIN_PREFIX = "app"  # e.g., tenant1.app.yourdomain.com
TENANT_DEFAULT_SLUG = "demo"  # For development/testing

# Session configuration for tenant isolation
SESSION_COOKIE_NAME = "tenant_sessionid"
SESSION_COOKIE_DOMAIN = (
    None if DEBUG else ".yourdomain.com"
)  # Allow cookies across subdomains
SESSION_COOKIE_SECURE = not True  # Use HTTPS in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Cache configuration for tenant isolation
""" CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'KEY_PREFIX': 'tenant',  # Prefix cache keys with tenant
    }
} """

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",  # ✅
        "LOCATION": "unique-snowflake",
    }
}

# Database routing for advanced isolation (optional)
DATABASE_ROUTERS = ["tenants.routers.TenantDatabaseRouter"]


# ==========================================
# LOGGING CONFIGURATION
# ==========================================

# ==========================================
# LOGGING CONFIGURATION
# ==========================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
        "tenant_format": {
            "format": "{levelname} {asctime} [{tenant_id}] [{user_id}] {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "console_debug": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "django.log"),
            "maxBytes": 1024 * 1024 * 5,  # 5MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_debug": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "django_debug.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10MB
            "backupCount": 3,
            "formatter": "verbose",
        },
        "tenant_audit": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "tenant_audit.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10MB
            "backupCount": 10,
            "formatter": "tenant_format",
        },
        "security": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "security.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security", "console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console_debug"],
            "level": "DEBUG",
            "propagate": False,
        },
        "tenants": {
            "handlers": ["console", "tenant_audit"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "tenants.audit": {
            "handlers": ["tenant_audit"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "audit": {
            "handlers": ["console", "tenant_audit"],
            "level": "INFO",
            "propagate": False,
        },
        "core": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}


# Logging configuration for audit


# ==========================================
# SECURITY SETTINGS FOR MULTI-TENANT
# ==========================================

# Adicione seu domínio permitido
# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.yourdomain.com']

# CSRF settings for subdomains
# CSRF_COOKIE_DOMAIN = '.yourdomain.com'  # Uncomment for production

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # Add your production domains here
]
