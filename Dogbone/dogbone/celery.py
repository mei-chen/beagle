from __future__ import absolute_import

import os
import logging

from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dogbone.settings')

def setup_handler(sender=None, logger=None, loglevel=None,
                  logfile=None, fmt=None, colorize=None, **kwds):
    """ Creates a syslog handler. """
    handler = logging.handlers.SysLogHandler(address='/dev/log', facility='daemon')
    handler.setFormatter(logging.Formatter("celery: %(message)s"))
    handler.setLevel(loglevel or logging.INFO)
    logger.addHandler(handler)

after_setup_logger.connect(setup_handler)
after_setup_task_logger.connect(setup_handler)

app = Celery('dogbone')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
