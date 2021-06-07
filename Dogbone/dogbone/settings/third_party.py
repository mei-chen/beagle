import os
from datetime import timedelta

from dotenv import load_dotenv
from selenium import webdriver


load_dotenv()

# This file describes third party settings

######################################################################################
#
#  TESTING
#
######################################################################################

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

######################################################################################
#
#  NOTIFICATIONS
#
######################################################################################

NOTIFICATIONS_USE_JSONFIELD = True
NOTIFICATIONS_SOFT_DELETE = False

######################################################################################
#
#  CELERY
#
######################################################################################

BROKER_URL = os.environ.get("BROKER_URL", "redis://localhost:6379/1")
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}

CELERY_RESULT_BACKEND = BROKER_URL

######################################################################################
#
#  CELERY BEAT PERIODIC TASKS
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

# TODO: Add clear session task

######################################################################################
#
#  MARKETING
#
######################################################################################

# TODO: Fix keys and integrations

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

# TODO: Fix keys

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
DEFAULT_SPOT_CONNECT_ENDPOINT = 'dogbone/connect/'
DEFAULT_SPOT_LOGIN_ENDPOINT = 'dogbone/login/'

######################################################################################
#
#  KIBBLE SETTINGS (DEFAULT)
#
######################################################################################

DEFAULT_KIBBLE_API_URL = 'http://kibble.beagle.ai/api/v1/'
DEFAULT_KIBBLE_CONNECT_ENDPOINT = 'dogbone/connect/'
DEFAULT_KIBBLE_LOGIN_ENDPOINT = 'dogbone/login/'

######################################################################################
#
#  CONSTANCE DYNAMIC SETTINGS
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
    'SPOT_CONNECT_ENDPOINT': (DEFAULT_SPOT_CONNECT_ENDPOINT, 'The endpoint for connecting Dogbone users with the Spot API'),
    'SPOT_LOGIN_ENDPOINT': (DEFAULT_SPOT_LOGIN_ENDPOINT, 'The endpoint for login of Dogbone users in Spot'),
    'KIBBLE_API_URL': (DEFAULT_KIBBLE_API_URL, 'The base URL for accessing the KIBBLE API'),
    'KIBBLE_CONNECT_ENDPOINT': (DEFAULT_KIBBLE_CONNECT_ENDPOINT, 'The endpoint for connecting Dogbone users with the KIBBLE API'),
    'KIBBLE_LOGIN_ENDPOINT': (DEFAULT_KIBBLE_LOGIN_ENDPOINT, 'The endpoint for login of Dogbone users in KIBBLE')
}

CONSTANCE_REDIS_CONNECTION = os.environ.get("REDIS_URL", "redis://localhost:6379")


######################################################################################
#
#  WATCHMAN SETTINGS
#
######################################################################################

# TODO: Check if working

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

######################################################################################
#
#  PAYMENTS
#
######################################################################################

PAYPAL_TEST= os.environ.get("PAYPAL_TEST", 'True') == 'True'
if PAYPAL_TEST:
    PAYPAL_RECEIVER_EMAIL = "iulius.curt@gmail.com"
else:
    PAYPAL_RECEIVER_EMAIL = "paypal@beagle.ai"

PAYPAL_IMAGE = 'https://www.paypalobjects.com/webstatic/mktg/logo/AM_mc_vs_dc_ae.jpg'
PAYPAL_SANDBOX_IMAGE = 'https://www.paypalobjects.com/webstatic/mktg/logo/AM_mc_vs_dc_ae.jpg'

######################################################################################
#
#  SLACK
#
######################################################################################

# Webhook for posting to slack
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')

# Slack Logger username
SLACK_USERNAME = os.environ.get('SLACK_USERNAME')

# Slack Logger channel
SLACK_CHANNEL = '#dev'

SLACKBOT_URL = 'https://beagleinc.slack.com/services/hooks/slackbot'
SLACKBOT_TOKEN = 'lOMXI2idvDsRo8x42zUwdK79'

######################################################################################
#
#  INTERCOM
#
######################################################################################

INTERCOM_STAFF = {
    'BeagleSupport': 70271,
    'Iulius': 71186,
}

INTERCOM_ENV = os.environ.get('INTERCOM_ENV', 'dev')

INTERCOM_APP_ID = os.environ.get('INTERCOM_APP_ID')
INTERCOM_API_KEY = os.environ.get('INTERCOM_API_KEY')

######################################################################################
#
#  AWS
#
######################################################################################

## Where to store the exported documents
S3_EXPORT_PATH = 'exports/%s.export.docx'
AWS_DEFAULT_BUCKET_NAME = 'BeagleDefaultS3Bucket'

PROFILE_PICTURE_BUCKET = 'beagle.s3.pictures'
PREDICTION_MODELS_BUCKET = 'beagle.s3.models'
UPLOADED_DOCUMENTS_BUCKET = 'beagle.s3.documents'