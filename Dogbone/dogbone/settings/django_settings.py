import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

# This file describes all of the django settings

######################################################################################
#
#  SECURITY
#
######################################################################################

# Environment variables are strings, need to do a comparison check

DEBUG = os.environ.get("DJANGO_DEBUG", 'True') == 'True'

WSGI_APPLICATION = 'dogbone.wsgi.application'
SILENCED_SYSTEM_CHECKS = ['admin.E130']

SECRET_KEY = os.environ.get("SECRET_KEY") or 'debugsekret'
PASSWORD_HASHERS = [
    'dogbone.hashers.MyPBKDF2PasswordHasher',
]

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [os.environ.get("DOMAIN", "*")]

######################################################################################
#
#  Sessions, Middleware, Authentication
#
######################################################################################

SESSION_ENGINE = 'user_sessions.backends.db'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# For persisting messages between pages
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'user_sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'authentication.middleware.TokenAuthMiddleware',
    'portal.middleware.UserCookieMiddleware',
    'marketing.middleware.ActionManagerMiddleware',
    #'portal.middleware.ExtendedMobileDetectionMiddleware',
    #'django_mobile.middleware.SetFlavourMiddleware',
    'utils.django_utils.middleware.ClientAddressMiddleware',
    'portal.middleware.UserTimezoneMiddleware',
    #'tracking.middleware.VisitorTrackingMiddleware',

    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'authentication.backends.AuthTokenBackend',
    'authentication.backends.OneTimeLoginHashModelBackend',
    'authentication.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

######################################################################################
#
#  INSTALLED DJANGO APPS
#
######################################################################################

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.sessions',

    #'south',
    'user_sessions',
    'notifications',
    'paypal.standard.ipn',
    #'django_mobile',
    'constance',

    'watchman',

    'ml',
    'core',
    'utils',
    'keywords',
    'beagle_bot',
    'marketing',
    'integrations',
    'beagle_deploy',
    'django_reports',
    'clauses_statistics',
    'authentication',
    #'tracking',
    'watcher',
    'statistics',

    'storages',

    # Keeps causing migrations to fail, so need to put it at the end
    # don't need this anymore
    #'longerusernameandemail',

    # Overwrites the default user admin pages along with longerusernameandemail,
    # so need to put it even after longerusernameandemail
    'portal',
)

ROOT_URLCONF = 'dogbone.urls'

######################################################################################
#
#  TEMPLATES
#
######################################################################################

TEMPLATE_LOADERS = (
    #'django_mobile.loader.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.filesystem.Loader',
)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
                "portal.context_processors.git_revision",
                "portal.context_processors.global_settings",
                "portal.context_processors.server_side_data",
                "django_mobile.context_processors.flavour",
            ],
            'loaders': [
                # insert your TEMPLATE_LOADERS here
                #'django_mobile.loader.Loader',
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.filesystem.Loader',
            ]
        },
    },
]

######################################################################################
#
#  INTERNATIONALIZATION & LOCALIZATION
#
######################################################################################

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Toronto'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

######################################################################################
#
#  Error Logging
#
######################################################################################

ADMINS = (
    ('Yixiong', 'sunabcsun71@gmail.com')
)

MANAGERS = ADMINS

DEFAULT_LOG = {
    'level': 'DEBUG',
    'class': 'logging.StreamHandler',
    'formatter': 'standard'
}

if os.environ.get('SYSLOG') == True:
    DEFAULT_LOG['class'] = 'logging.handlers.SysLogHandler'
    DEFAULT_LOG['address'] = '/dev/log'
    DEFAULT_LOG['facility'] = 'daemon'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "dogbone: [%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'request': {
            'format' : "dogbone.request: [%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'default': DEFAULT_LOG,
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'slack': {
            'level': 'CRITICAL',
            'class': 'integrations.loggers.SlackLogHandler',
        },
        'log_db': {
            'level': 'INFO',
            'class': 'integrations.loggers.DBHandler',
            'model': 'integrations.models.SpecialLog',
            'expiry': 86400
        }
    },
    'root': {
        'handlers': ['default'],
        'level': 'DEBUG'
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'django.request': {
            'handlers': ['default', 'slack'],
            'level': 'DEBUG',
            'propagate': False
        },
        'dogbone': {
            'handlers': ['console', 'default', 'slack'],
            'level': 'DEBUG',
        },

        'qinspect': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        },
    }
}

MIDDLEWARE.extend([
    'utils.prof.ProfilerMiddleware',
    'qinspect.middleware.QueryInspectMiddleware',
])

# Query Inspector works only in DEBUG mode!
QUERY_INSPECT_ENABLED = True
QUERY_INSPECT_LOG_STATS = False
QUERY_INSPECT_HEADER_STATS = True
# Should be enabled for duplicate SQL queries detection
# (disabled by default because of excessive verbosity)
QUERY_INSPECT_LOG_QUERIES = False


######################################################################################
#
#  EMAIL
#
######################################################################################

if os.environ.get("EMAIL_BACKEND") == "smtp":
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
  EMAIL_BACKEND = 'portal.backends.OpenBrowserEmailBackend'

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'Beagle Invite <info@beagle.ai>'

######################################################################################
#
#  DEBUG
#
######################################################################################

REACT_LOCAL_ADDRESS = 'http://127.0.0.1:3000'

# IP addresses that Django will use in DEBUG mode to be recognized as dev IPs
# Lets us use the `debug` template variable
# see https://docs.djangoproject.com/en/1.4/ref/settings/#internal-ips
INTERNAL_IPS = (
    '127.0.0.1'
)

######################################################################################
#
#  STATIC FILES
#
######################################################################################

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = 'media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.environ.get('STATIC_ASSET_PATH', 'collectstatic/')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

STATIC_S3 = os.environ.get('STATIC_S3') == 'True'

if STATIC_S3 is True:
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_REGION_NAME= os.environ.get('STATIC_REGION_NAME')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('STATIC_BUCKET_NAME')
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_LOCATION = 'static'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

    STATICFILES_LOCATION = 'static'
    STATICFILES_STORAGE = 'dogbone.custom_storages.StaticStorage'

    MEDIAFILES_LOCATION = 'media'
    DEFAULT_FILE_STORAGE = 'dogbone.custom_storages.MediaStorage'


######################################################################################
#
#  CACHE
#
######################################################################################

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# Store in CACHE URL
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': os.environ.get("REDIS_URL", "redis://localhost:6379"),
    },
}

######################################################################################
#
#  DATABASES
#
######################################################################################

DATABASES = {
	'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("DATABASE_NAME", "dogbone"),
        'USER': os.environ.get("DATABASE_USER", "dogbone"),
        'PASSWORD': os.environ.get("DATABASE_PASSWORD", "password"),
        'HOST': os.environ.get("DATABASE_URL", "localhost"),
        'PORT': os.environ.get("DATABASE_PORT", "5432"),
    }
}

