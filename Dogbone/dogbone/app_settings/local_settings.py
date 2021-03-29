DEBUG=True
HOT_LOAD=False

DATABASES = {
	'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dogbone',
        'USER': 'dogbone',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}