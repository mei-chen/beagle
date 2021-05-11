"""
Django settings for kibble project.
Generated by 'django-admin startproject' using Django 1.10.5.
For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""
# Python
from datetime import timedelta
import os

# Third Party
from dotenv import load_dotenv, find_dotenv
import dj_database_url

# Loading the environmental variables
load_dotenv(find_dotenv())

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SESSION_SECRET", '==sxke5!cp)49fx(2--zy*9#c95!@2vr%p8$kqz5g+p0#js)w*')

# SECURITY WARNING: don't run with debug turned on in production!
# Setting to false by default and must be explicitly turned on.
#DEBUG = int(os.environ.get("DJANGO_DEBUG", 0)) == 1
DEBUG = False
HOT_LOAD = int(os.environ.get("HOT_LOAD", 0)) == 1
DELOREAN_VM = True
ALLOWED_HOSTS = ["*", "localhost"]

######################################################################################
#
#  DATABASE
#
######################################################################################

# DATABASES = {
#     'default': dj_database_url.config(conn_max_age=600)
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'storages',
    'constance',
    'watchman',
    'corsheaders',


    # Project
    'utils',
    'document',
    'realtime',
    'portal',
    'analysis',
    'watcher',
    'core',
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

FIXTURE_DIRS = (
    os.path.join(BASE_DIR, 'analysis/fixtures/'),
)

ROOT_URLCONF = 'kibble.urls'

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

WSGI_APPLICATION = 'kibble.wsgi.application'

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

CORS_ALLOWED_ORIGINS = ['http://18.207.159.186']

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
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "uploads")

REDIS_URL = os.environ.get("REDIS_URL", 'redis://localhost:6379/0')
BROKER_URL = os.environ.get('BROKER_URL', 'redis://localhost:6379/1')
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SendGrid API key is missing right now, use console as the backend
#EMAIL_BACKEND = "sgbackend.SendGridBackend"
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')

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

DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.BasicAuthentication',
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.TokenAuthentication'
        )
}

######################################################################################
#
#  LOGGING
#
######################################################################################

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

######################################################################################
#
#  EASYPDFCLOUDAPI CREDENTIALS
#
######################################################################################

PDF_CREDENTIALS = {
    'ClientID': 'f088c9b0cf3b45d8bf7c9d84033c604f',
    'ClientSecret': 'BD78A36C65A6F2049123E6396FD4B8291FE512A01D68D743D35ABD4E011C79A3',
    'WorkflowName': 'pdf_to_docx',
    'WorkflowID': '000000000484CEF4',
}

OCR_PDF_CREDENTIALS = {
    'ClientID': 'f088c9b0cf3b45d8bf7c9d84033c604f',
    'ClientSecret': 'BD78A36C65A6F2049123E6396FD4B8291FE512A01D68D743D35ABD4E011C79A3',
    'WorkflowName': 'ocr_pdf_to_docx',
    'WorkflowID': '000000000488C40D',
}

DOC_CREDENTIALS = {
    'ClientID': 'f088c9b0cf3b45d8bf7c9d84033c604f',
    'ClientSecret': 'BD78A36C65A6F2049123E6396FD4B8291FE512A01D68D743D35ABD4E011C79A3',
    'WorkflowName': 'doc_to_docx',
    'WorkflowID': '00000000050D8664',
}

JOB_ENDPOINT = 'https://api.easypdfcloud.com/v1/jobs/'
TOKEN_ENDPOINT = 'https://www.easypdfcloud.com/oauth2/token'
WORKFLOW_ENDPOINT = 'https://api.easypdfcloud.com/v1/workflows/'
AUTHORIZE_ENDPOINT = 'https://www.easypdfcloud.com/oauth2/authorize'

API_LIMIT_PER_PAGE = 0

# Count of batch name chars used for file upload folder naming
BATCH_NAME_TRUNCATE_CHARS = 20

# The (maximum) number of characters to show from the beginning of any sentence
SENTENCE_PREVIEW_LENGTH = 150

# E-mails
EMAIL_RUFUS = 'ubuntu@rufus.beagle.com'

# Document cleanup
# TOC
TOC_NAMES = ['table of contents', 'toc', 'contents']
TOC_ITEM_VALID_STARTS = ('part',)
TOC_ITEM_VALID_ENDS = ('page',)
TOC_ITEM_MAX_LENGTH = 170



# Default user.profile settings
FILE_AUTO_PROCESS = True
AUTO_CLEANUP_TOOLS = [
    # 'linebreakers',
    'title/header/footer',
    'table of contents',
    'bullet points and listing',
    'listing rewriting',
    # 'tables',
]
SENTENCE_PULL_SIZE = 100
SENTENCE_PULL_PERCENTAGES = [40, 40, 20]
OBFUSCATE_STRING = '[[CONFIDENTIAL]]'
HIGHLIGHT_COLOR = 'red'
AUTO_PERSONAL_DATA = False
OBFUSCATED_EXPORT_EXT = 'PDF'
SENTENCE_WORD_THRESHOLD = 8
MIN_SIMILARITY_SCORE = 3.5
PERSONAL_DATA_TYPES = {
    'Person': (True, 'string'),
    'Organization': (True, 'string'),
    'Date': (True, 'string'),
    'Phone': (True, 'string'),
    'Link': (True, 'string'),
    'Email': (True, 'string'),
    'Price': (True, 'string'),
    'Street Address': (True, 'string')
}





# defined later check purpose only
AWS_STORAGE_BUCKET_NAME = None

# Watchman settings

DEFAULT_WATCHMAN_CHECKS = [
    'watchman.checks.caches',
    'watchman.checks.storage',
    'watchman.checks.databases',
]

CUSTOM_WATCHMAN_CHECKS = [
    'kibble.checks.models',
    'kibble.checks.celery',
    'kibble.checks.redis',
]

WATCHMAN_CHECKS = DEFAULT_WATCHMAN_CHECKS + CUSTOM_WATCHMAN_CHECKS

WATCHMAN_TOKEN_NAME = 'token'

# CSV
WATCHMAN_TOKENS = ','.join([
    '9iFnoGoWz32VfhNCVNyCmz0uZok7Y4Bo1IJA8chlcvgrYWUftuBSqFVLwCpOJ1'
])

# Override for current env
try:
    from .app_settings.production_settings import *
except ImportError:
    pass

try:
    from .app_settings.local_settings import *
except ImportError:
    pass


# keyword list analysis
DELOREAN_ENDPOINT = 'http://127.0.0.1:3000/' if DELOREAN_VM else 'http://10.0.2.2:3000/'

#MOST_SIMILAR_ENDPOINT = 'http://api.research.beagle.ai:8000/most_similar/word={word}&model={model}&number={number}&user={user}&password={password}'
MOST_SIMILAR_ENDPOINT = DELOREAN_ENDPOINT + 'most_similar/word={word}&model={model}&number={number}&user={user}&password={password}'
MOST_SIMILAR_DEFAULT_NUMBER = 15
MOST_SIMILAR_USER = 'Beagle'
MOST_SIMILAR_PASSWORD = 'GreatBeagleAI'

SYNONYMS_ENDPOINT = 'https://wordsapiv1.p.mashape.com/words/%s/synonyms'
SYNONYMS_API_KEY = 'a7nUoIQHnEmsho5sOHGXuGueRx0Ap1ld01LjsnAddQybg9aDMu'

# SENTENCE_VECTOR_ENDPOINT = 'http://api.research.beagle.ai:8001/sentence_vector_notag'
SENTENCE_VECTOR_ENDPOINT = DELOREAN_ENDPOINT + 'sentence_vector'


SENTENCE_VECTOR_DEFAULT_MODEL = 'lawinsider_notag'
SENTENCE_VECTOR_DEFAULT_ALGORITHM = 'sif'
SENTENCE_VECTOR_DEFAULT_ALPHA = '3'
SENTENCE_VECTOR_USER = 'Beagle'
SENTENCE_VECTOR_PASSWORD = 'GreatBeagleAI'

# Sentence Splitting
SENTENCE_SPLITTING_TOKEN = 'p03O4qlvnoykdAiz1pPvwLG4XfNzu7AbkqjumXAho1WVS3S91ffx1YYWWSF2X0bQV17euAUc4iAkgQImLouFAm9vXeej6hLMMZ'
# SENTENCE_SPLITTING_ENDPOINT = 'https://kyhk5y2ub3.execute-api.us-west-2.amazonaws.com/dev'
SENTENCE_SPLITTING_ENDPOINT = DELOREAN_ENDPOINT + 'sentence_splitting'

# Celery settings
CELERY_BROKER_URL = BROKER_URL

# Periodic tasks
CELERY_BEAT_SCHEDULE = {
    'import_files_from_dropbox': {
        'task': 'watcher.tasks.import_files_from_dropbox',
        'schedule': timedelta(seconds=(30 if DEBUG else 300)),
    },
    'import_files_from_google_drive': {
        'task': 'watcher.tasks.import_files_from_google_drive',
        'schedule': timedelta(seconds=(30 if DEBUG else 300)),
    },
}

# Constance settings
CONSTANCE_REDIS_CONNECTION = CELERY_BROKER_URL
CONSTANCE_CONFIG = {
    'DOGBONE_AUTHORIZE_URL': (
        'https://{env}.beagle.ai/kibble/authorize/'.format(
            env='dev' if DEBUG else 'beta'
        ),
        'The base URL for authorizing users coming from Beagle'
    ),
}

# Use S3 if credentials are specified
if AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    S3_USE_SIGV4 = True

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
