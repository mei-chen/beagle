"""
Django settings for spot project.

Generated by 'django-admin startproject' using Django 1.10.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
from dotenv import load_dotenv, find_dotenv

# Loading the environmental variables
load_dotenv(find_dotenv())

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '==sxke5!cp)49fx(2--zy*9#c95!@2vr%p8$kqz5g+p0#js)w*'

# SECURITY WARNING: don't run with debug turned on in production!
# Setting to false by default and must be explicitly turned on.
DEBUG = False
HOT_LOAD = False

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    # Third party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'constance',
    'rest_framework',
    'watchman',
    'corsheaders',

    # Project
    'core',
    'dataset',
    'experiment',
    'integrations',
    'marketing',
    'ml',
    'portal',
    'realtime',
]

SITE_ID = 1

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'spot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "portal", "templates")
        ],
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

WSGI_APPLICATION = 'spot.wsgi.application'

# Dogbone url
CORS_ALLOWED_ORIGINS = ['http://18.207.159.186']

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

# Default database settings which should be overwritten
# in either local or production settings from app_settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'collectstatic/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "portal", "static"),
]

# Caching
# https://docs.djangoproject.com/en/1.10/topics/cache/

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache',
        'TIMEOUT': 60 * 60 * 24,  # default TTL in seconds
        'OPTIONS': {
            'MAX_ENTRIES': 999999999,  # i.e. actually no size restrictions
        }
    }
}

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
BROKER_URL = os.environ.get('BROKER_URL', 'redis://localhost:6379/1')

# Authentication settings

ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = True

ACCOUNT_ADAPTER = 'portal.adapter.EmailAsUsernameAccountAdapter'

ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
# For ordinary users username and email are equal, but for superusers these
# fields may differ, so this setting makes sense for both cases
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'

# Integration credentials
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#EMAIL_BACKEND = "sgbackend.SendGridBackend"
SENDGRID_API_KEY = ""

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

PREDICTION_MODELS_BUCKET = 'spot.s3.local.models'

# Watchman settings

DEFAULT_WATCHMAN_CHECKS = [
    'watchman.checks.caches',
    'watchman.checks.storage',
    'watchman.checks.databases',
]

CUSTOM_WATCHMAN_CHECKS = [
    'spot.checks.models',
    'spot.checks.celery',
    'spot.checks.redis',
]

WATCHMAN_CHECKS = DEFAULT_WATCHMAN_CHECKS + CUSTOM_WATCHMAN_CHECKS

WATCHMAN_TOKEN_NAME = 'token'

# CSV
WATCHMAN_TOKENS = ','.join([
    'VvoqXjUvPMCH116aedyRKiN3QqgF95XHXRrqDkQFlhfCNRnAvSFdSUmQTX7QRnRcD8x',
])

# Django REST framework settings

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

# Override for current env

try:
    from .app_settings.production_settings import *
except ImportError as e:
    print(e)
    print('Production settings have not been set')

try:
    from .app_settings.local_settings import *
except ImportError:
    print('Local settings have not been set')

# Celery settings

CELERY_BROKER_URL = BROKER_URL
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Constance settings

CONSTANCE_REDIS_CONNECTION = CELERY_BROKER_URL

CONSTANCE_CONFIG = {
    'DOGBONE_AUTHORIZE_URL': (
        'https://{env}.beagle.ai/spot/authorize/'.format(
            env='dev' if DEBUG else 'beta'
        ),
        'The base URL for authorizing users coming from Beagle'
    ),
}

# Tweak settings a bit for debugging purposes only!

if DEBUG:
    # Query Inspector settings

    MIDDLEWARE += [
        'qinspect.middleware.QueryInspectMiddleware',
    ]

    QUERY_INSPECT_ENABLED = True
    QUERY_INSPECT_HEADER_STATS = True
    # Should be enabled for duplicate SQL queries detection
    # (disabled by default because of excessive verbosity)
    QUERY_INSPECT_LOG_STATS = False
    QUERY_INSPECT_LOG_QUERIES = False
    CORS_ALLOWED_ORIGINS.append('http://localhost:8003')
