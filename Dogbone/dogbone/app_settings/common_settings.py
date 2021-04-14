from datetime import timedelta
import os

from selenium import webdriver

import dogbone.app_settings.marketing_settings


WSGI_APPLICATION = 'dogbone.wsgi.application'
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__name__))
SITE_ID = 1

SELENIUM_WEBDRIVER = {
    # 'webdriver_path': os.path.join(SITE_ROOT, 'testing', 'linux', 'phantomjs'),
    'webdriver_path': os.path.join(SITE_ROOT, 'testing', 'linux', 'chromedriver'),
    # 'webdriver_path': os.path.join(SITE_ROOT, 'testing', 'osx', 'chromedriver'),
    # 'webdriver_path': os.path.join(SITE_ROOT, 'testing', 'osx', 'phantomjs'),
    # 'webdriver_type': webdriver.PhantomJS,
    'webdriver_type': webdriver.Chrome
}

# Change this to False, run them on local
SKIP_SELENIUM_TESTS = True

SILENCED_SYSTEM_CHECKS = ['admin.E130']


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

    # Keeps causing migrations to fail, so need to put it at the end
    # don't need this anymore
    #'longerusernameandemail',

    # Overwrites the default user admin pages along with longerusernameandemail,
    # so need to put it even after longerusernameandemail
    'portal',
)

ROOT_URLCONF = 'dogbone.urls'

# Notification related settings
NOTIFICATIONS_USE_JSONFIELD = True
NOTIFICATIONS_SOFT_DELETE = False

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
#  DATABASE
#
######################################################################################

#SOUTH_MIGRATION_MODULES = {
#    'user_sessions': 'user_sessions.south_migrations',
#}
#SOUTH_TESTS_MIGRATE = False

######################################################################################
#
#  STATIC FILES
#
######################################################################################

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SAMPLE_DOCS_DIR = os.path.join(PROJECT_ROOT, 'resources', 'init_samples')

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
#  PERIODIC TASKS
#
######################################################################################

CELERYBEAT_SCHEDULE = {
    'periodic_send_notification_reminders': {
        'task': 'core.cron.periodic_send_notification_reminders',
        'schedule': timedelta(minutes=30),
    },

    'queue_worker': {
        'task': 'watcher.tasks.queue_worker',
        'schedule': timedelta(seconds=60),
    },

    'import_from_google_drive': {
        'task': 'watcher.tasks.add_to_queue_from_google_drive',
        'schedule': timedelta(seconds=30),
    },

    'add_dropbox_file_to_queue': {
        'task': 'watcher.tasks.add_to_queue_from_dropbox',
        'schedule': timedelta(seconds=30),
    }
}

######################################################################################
#
#  MARKETING
#
######################################################################################

HUBSPOT_PORTAL_ID = '541681'
HUBSPOT_API_KEY = '534b9182-1fe7-4ab3-8589-46b2d086dce7'

# HubSpot Forms
HUBSPOT_REGISTER_FORM_GUID = '2e912178-1b60-4f86-a57f-bc190ee62777'
HUBSPOT_EXTERNAL_REGISTER_FORM_GUID = '288fdc3d-d7d0-4388-81f8-7f7899e40e40'
HUBSPOT_SUBSCRIPTION_EXPIRED_FORM_GUID = 'e7f26592-ef11-4305-adb2-9a49b9b04c96'
HUBSPOT_SUBSCRIPTION_STARTED_FORM_GUID = 'f1afd438-8c28-4a5a-8009-c15c3b6c09a4'
HUBSPOT_SUBSCRIPTION_EXTENDED_FORM_GUID = 'f9ef7a4e-6190-41d4-9dfd-1b34856b634b'
HUBSPOT_PAYMENT_FORM_GUID = '9d85db75-e7b7-4faa-8a91-eb52532043b8'

######################################################################################
#
#  DROPBOX AND GOOGLE DRIVE APPS (DEFAULT)
#
######################################################################################

# An unofficial app which is fine for local and dev settings,
# but should be changed to an official one in production environments
DEFAULT_DROPBOX_APP_KEY = 'ix65108k8ykt90i'
DEFAULT_DROPBOX_APP_SECRET = 'smhtps1u21cp4wk'

# Ditto
DEFAULT_GOOGLE_DRIVE_CLIENT_ID = '1041503396875-inoac6vsobcqs7dr078hgklkgueasj3d.apps.googleusercontent.com'
DEFAULT_GOOGLE_DRIVE_CLIENT_SECRET = 'AjgHIhJdGFGa3GTVKrt-McAn'

######################################################################################
#
#  SPOT SETTINGS (DEFAULT)
#
######################################################################################

DEFAULT_SPOT_API_URL = 'http://spot.beagle.ai/api/v1/'

######################################################################################
#
#  DYNAMIC SETTINGS
#
######################################################################################

CONSTANCE_BACKEND = 'constance.backends.redisd.RedisBackend'

CONSTANCE_CONFIG = {
    'BROWSER_EXTENSION_ENABLED': (True, 'Enable/Disable the browser extension'),
    'BROWSER_EXTENSION_DISABLED_MESSAGE': ('The Service is under development. Please try again later.',
                                           'The message displayed to the user in case the service is disabled.'),
    'MAX_PDF_OCR_UPLOAD_PAGES': (75, 'Adjust pdf pages limit on upload'
                                     '(applied only if OCR is needed for pdf converting).'),
    'DROPBOX_APP_KEY': (DEFAULT_DROPBOX_APP_KEY, 'Put "App key" from the Dropbox App Console'),
    'DROPBOX_APP_SECRET': (DEFAULT_DROPBOX_APP_SECRET, 'Put "App secret" the Dropbox App Console (hidden by default)'),
    'GOOGLE_DRIVE_CLIENT_ID': (DEFAULT_GOOGLE_DRIVE_CLIENT_ID, 'Put "Client ID" from the Google API Console'),
    'GOOGLE_DRIVE_CLIENT_SECRET': (DEFAULT_GOOGLE_DRIVE_CLIENT_SECRET, 'Put "Client secret" from the Google API Console'),
    'SPOT_API_URL': (DEFAULT_SPOT_API_URL, 'The base URL for accessing the Spot API'),
}

######################################################################################
#
#  OTHER INTEGRATIONS
#
######################################################################################

## SLACK

SLACKBOT_URL = 'https://beagleinc.slack.com/services/hooks/slackbot'
SLACKBOT_TOKEN = 'lOMXI2idvDsRo8x42zUwdK79'

## INTERCOM

INTERCOM_STAFF = {
    'BeagleSupport': 70271,
    'Iulius': 71186,
}

## Mobile Detection Flavors

FLAVOURS = (
    "full",
    "mobile",
    "tablet",
)

## Message to be sent through Intercom in case of EASYPDF failure

EASYPDF_ERROR_MESSAGE = """Hi {{first_name | fallback: "there" }},

We noticed that there was a problem with the PDF you uploaded. We apologize \
for the error and are looking into it. In the meantime please feel free to \
try a different document.

We appreciate your patience and feedback, thanks for using Beagle! \
"""

DOC_ERROR_MESSAGE = """Hi {{first_name | fallback: "there" }},

You seem to have uploaded a .DOC file. Unfortunately, we currently only support \
.PDF, .TXT and .DOCX files. Good news is, if you have Microsoft Word, you can \
easily save the file as a .DOCX instead of .DOC. \

We appreciate your patience and feedback, thanks for using Beagle! \
"""

## Where to store the exported documents
S3_EXPORT_PATH = 'exports/%s.export.docx'

######################################################################################
#
#  UI SETTINGS
#
######################################################################################

# How many new comments to load when pushing `more` on comments widget
COMMENTS_PER_PAGE = 5

# How many most frequent keywords to show in document digest
TOP_KEYWORD_COUNT_DIGEST = 5

# How many clauses to preview for each top keyword in document digest
TOP_KEYWORD_CLAUSE_COUNT_DIGEST = 3

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

######################################################################################
#
#  WATCHMAN SETTINGS
#
######################################################################################

DEFAULT_WATCHMAN_CHECKS = [
    'watchman.checks.caches',
    'watchman.checks.storage',
    'watchman.checks.databases',
]

CUSTOM_WATCHMAN_CHECKS = [
    'dogbone.checks.models',
    'dogbone.checks.celery',
    'dogbone.checks.redis',
]

WATCHMAN_CHECKS = DEFAULT_WATCHMAN_CHECKS + CUSTOM_WATCHMAN_CHECKS

WATCHMAN_TOKEN_NAME = 'token'

# CSV
WATCHMAN_TOKENS = ','.join([
    'dk80kIZrXnVNJxS5VW1OtO9t1worbnpOwsYftwusmIXOIc3amQWArI5RwjNWjmT90q9wY',
])
