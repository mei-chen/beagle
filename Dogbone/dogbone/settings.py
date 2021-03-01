import os
import socket
from app_settings.common_settings import *
import dj_database_url
from dotenv import load_dotenv, find_dotenv

dotenv = find_dotenv()
if dotenv != "":
  load_dotenv(dotenv)

######################################################################################
#
#  DEBUG
#
######################################################################################

DEBUG = os.environ.get("DJANGO_DEBUG")
if DEBUG is None:
    DEBUG = True  # Default to debug
else:
    DEBUG = int(DEBUG) == 1

SOCKET_DOMAIN = os.environ.get("SOCKET_DOMAIN")
if SOCKET_DOMAIN is None:
    SOCKET_DOMAIN = False  # Default to localhost
else:
    SOCKET_DOMAIN = int(SOCKET_DOMAIN) == 1

HOT_LOAD = os.environ.get("HOT_LOAD")
if HOT_LOAD is None:
    HOT_LOAD = False  # Disabled by default, should be enabled explicitly
else:
    HOT_LOAD = int(HOT_LOAD) == 1

INTERCOM_ENV = 'dev' if DEBUG else 'prod'

ADMINS = (
    ('Cian', 'cian@beagle.ai'),
    ('Iulius', 'iulius@beagle.ai'),
)

MANAGERS = ADMINS

# IP addresses that Django will use in DEBUG mode to be recognized as dev IPs
# Lets us use the `debug` template variable
# see https://docs.djangoproject.com/en/1.4/ref/settings/#internal-ips
INTERNAL_IPS = (
    '192.168.59.3',
    '127.0.0.1'
)

DOMAIN = socket.getfqdn() if SOCKET_DOMAIN else "localhost:8000"
REDIS_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379"
USE_HTTPS = not DEBUG

######################################################################################
#
#  HOOKS
#
######################################################################################

# Webhook for posting to slack
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')

# Slack Logger username
SLACK_USERNAME = os.environ.get('SLACK_USERNAME')

# Slack Logger channel
SLACK_CHANNEL = '#dev'

######################################################################################
#
#  SECURITY
#
######################################################################################

SECRET_KEY = os.environ.get("SESSION_SECRET") or 'debugsekret'
PASSWORD_HASHERS = [
    'dogbone.hashers.MyPBKDF2PasswordHasher',
]

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*'] if DEBUG else [os.environ.get("DOMAIN", DOMAIN)]

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
#  CELERY
#
######################################################################################

BROKER_URL = os.environ.get('BROKER_URL') or 'redis://localhost:6379'
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}

CELERY_RESULT_BACKEND = BROKER_URL
# CELERY_RESULT_BACKEND = 'redis://' + REDIS_HOST + ':' + REDIS_PORT + '/0'

######################################################################################
#
#  DEBUG
#
######################################################################################

REACT_LOCAL_ADDRESS = 'http://127.0.0.1:3000'

INTERCOM_ENV = 'dev'

ADMINS = (
    ('Iulius', 'iulius@beagle.ai'),
    ('Cian', 'cian@beagle.ai'),
)

MANAGERS = ADMINS

# IP addresses that Django will use in DEBUG mode to be recognized as dev IPs
# Lets us use the `debug` template variable
# see https://docs.djangoproject.com/en/1.4/ref/settings/#internal-ips
INTERNAL_IPS = (
    '192.168.59.3',
    '127.0.0.1'
)

######################################################################################
#
#  DATABASE
#
######################################################################################

DATABASES = {
    'default': dj_database_url.config()
}

######################################################################################
#
#  REALTIME
#
######################################################################################

NODEJS_SERVER = socket.getfqdn() if SOCKET_DOMAIN else "localhost:4000"

######################################################################################
#
#  LOGGING
#
######################################################################################

DEFAULT_LOG = {
    'level': 'DEBUG',
    'class': 'logging.StreamHandler',
    'formatter': 'standard'
}

if os.environ.get('SYSLOG'):
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
            'class': 'django.utils.log.NullHandler',
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

MIDDLEWARE_CLASSES += (
    'utils.prof.ProfilerMiddleware',
    'qinspect.middleware.QueryInspectMiddleware',
)

# Query Inspector works only in DEBUG mode!
QUERY_INSPECT_ENABLED = True
QUERY_INSPECT_LOG_STATS = False
QUERY_INSPECT_HEADER_STATS = True
# Should be enabled for duplicate SQL queries detection
# (disabled by default because of excessive verbosity)
QUERY_INSPECT_LOG_QUERIES = False

######################################################################################
#
#  CACHE
#
######################################################################################

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': REDIS_URL,
    },
}

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
STATIC_ROOT = os.environ.get('STATIC_ASSET_PATH') or ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

######################################################################################
#
#  PAYMENTS
#
######################################################################################
if DEBUG:
    PAYPAL_RECEIVER_EMAIL = "iulius.curt@gmail.com"
    PAYPAL_TEST = DEBUG
else:
    PAYPAL_RECEIVER_EMAIL = "paypal@beagle.ai"
    PAYPAL_TEST = DEBUG

PAYPAL_IMAGE = 'https://www.paypalobjects.com/webstatic/mktg/logo/AM_mc_vs_dc_ae.jpg'
PAYPAL_SANDBOX_IMAGE = 'https://www.paypalobjects.com/webstatic/mktg/logo/AM_mc_vs_dc_ae.jpg'

######################################################################################
#
#  INTEGRATIONS
#
######################################################################################

INTERCOM_APP_ID = os.environ.get('INTERCOM_APP_ID')
INTERCOM_API_KEY = os.environ.get('INTERCOM_API_KEY')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_BUCKET_NAME = 'BeagleDefaultS3Bucket'

PROFILE_PICTURE_BUCKET = 'beagle.s3.pictures'
PREDICTION_MODELS_BUCKET = 'beagle.s3.models'
UPLOADED_DOCUMENTS_BUCKET = 'beagle.s3.documents'

######################################################################################
#
#  CONSTANCE CONNECTION
#
######################################################################################

CONSTANCE_REDIS_CONNECTION = BROKER_URL

try:
    from app_settings.local_settings import *
except ImportError:
    print 'Local settings have not been set'

try:
    from app_settings.production_settings import *
except ImportError:
    print 'Production settings have not been set'
