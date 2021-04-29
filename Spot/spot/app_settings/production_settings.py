DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'spot',
        'USER': 'spot',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

SENDGRID_API_KEY = ''
REDIS_URL = 'redis://localhost:6379/0'

DEBUG = False
HOT_LOAD = False
