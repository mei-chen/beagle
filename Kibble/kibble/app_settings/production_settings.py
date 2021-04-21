DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kibble',
        'USER': 'kibble',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

AWS_SECRET_ACCESS_KEY = ''
AWS_ACCESS_KEY_ID = ''
AWS_STORAGE_BUCKET_NAME = ''
AWS_S3_REGION_NAME = ''
DROPBOX_APP_KEY = ''
DROPBOX_APP_SECRET = ''
GOOGLE_DRIVE_CLIENT_ID = ''
GOOGLE_DRIVE_CLIENT_SECRET = ''
SENDGRID_API_KEY = ''
REDIS_URL = 'redis://localhost:6379/0'

DEBUG = False
HOT_LOAD = False
