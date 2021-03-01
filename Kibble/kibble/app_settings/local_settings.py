import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DB_DIR, 'db.sqlite3'),
    }
}

# AWS_ACCESS_KEY_ID = 'AKIAJ32G4N2ZUDZJVKQA'
# AWS_SECRET_ACCESS_KEY = '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'
# AWS_STORAGE_BUCKET_NAME = 'nitr0-kibble'
# AWS_S3_REGION_NAME = 'eu-central-1'

# DROPBOX_APP_KEY: ...
# DROPBOX_APP_SECRET: ...
# GOOGLE_DRIVE_CLIENT_ID: ...
# GOOGLE_DRIVE_CLIENT_SECRET: ...
# SENDGRID_API_KEY: [required]
# db_password: ...
# public_key: ~/.ssh/<your_rsa>.pub
superuser_username: 'wei'
superuser_password: '991020'


DEBUG = True

HOT_LOAD = True