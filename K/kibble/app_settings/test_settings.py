import tempfile
from kibble.settings import *


MEDIA_ROOT = tempfile.gettempdir() + '/kibble_test_files'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
