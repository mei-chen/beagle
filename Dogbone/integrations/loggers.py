import datetime
import json
import logging
import random

try:
    from django.conf import settings
except ImportError:
    pass

from .tasks import slack
from django.utils import timezone

class SlackLogHandler(logging.Handler):

    class SlackWebHookException(Exception):
        pass

    EMOJIS = {
        logging.NOTSET: ':loudspeaker:',
        logging.DEBUG: ':speaker:',
        logging.INFO: ':information_source:',
        logging.WARNING: ':warning:',
        logging.ERROR: ':exclamation:',
        logging.CRITICAL: ':boom:'
    }

    def __init__(self, webhook=None, channel=None, username=None,
                 format='[%(levelname)s] [%(asctime)s] [%(name)s] - %(message)s'):
        logging.Handler.__init__(self)

        if webhook is None:
            try:
                webhook = settings.SLACK_WEBHOOK
                if webhook is None:
                    raise Exception()
            except:
                logging.getLogger().warn('No SLACK_WEBHOOK specified, no logs will be sent to Slack')
                webhook = None

        if channel is None:
            try:
                channel = settings.SLACK_CHANNEL
                if channel is None:
                    raise Exception("Could not set a proper channel")
            except:
                logging.getLogger().warn('No SLACK_CHANNEL specified, defaulting to #general')
                channel = '#general'

        if username is None:
            try:
                username = settings.SLACK_USERNAME
                if username is None:
                    raise Exception("Could not set a proper username")
            except:
                logging.getLogger().warn('No SLACK_USERNAME specified, defaulting to SlackLogger')
                username = 'SlackLogger'

        self.webhook = webhook
        self.channel = channel
        self.username = username
        self.formatter = logging.Formatter(format)

    def emit(self, record):
        if self.webhook is None:
            return

        try:
            kwargs = {
                'webhook': self.webhook,
                'message': self.format(record),
                'icon_emoji': self.EMOJIS[record.levelno],
            }
            if self.channel:
                kwargs['channel'] = self.channel

            if self.username:
                kwargs['username'] = self.username
            else:
                kwargs['username'] = "{0} - {1}".format(record.module, record.name)

            slack.delay(**kwargs)
        except:
            self.handleError(record)


def slack_log(message, level):
    slack.delay(
        webhook=settings.SLACK_WEBHOOK,
        channel=settings.SLACK_CHANNEL,
        username=settings.SLACK_USERNAME,
        message=message,
        icon_emoji=SlackLogHandler.EMOJIS[level],
    )


class DBHandler(logging.Handler):
    """
    This handler will add logs to a database model defined in settings.py
    If log message (pre-format) is a json string, it will try to apply
    the array onto the log event object.
    """

    model_name = None
    expiry = None

    def __init__(self, model="", expiry=0):
        super(DBHandler, self).__init__()
        self.model_name = model
        self.expiry = int(expiry)

    # TODO: specify exceptions.
    def emit(self, record):
        # big try block here to exit silently if exception occurred
        try:
            # instantiate the model
            try:
                model = self.get_model(self.model_name)
            except:
                from .models import GeneralLog as model

            log_entry = model(level=record.levelname, message=self.format(record))

            # test if msg is json and apply to log record object
            try:
                data = json.loads(record.msg)
                for key, value in data.items():
                    if hasattr(log_entry, key):
                        try:
                            setattr(log_entry, key, value)
                        except:
                            pass
            except:
                pass

            log_entry.save()

            # in 20% of time, check and delete expired logs
            if self.expiry and random.randint(1, 5) == 1:
                model.objects.filter(
                    time__lt=timezone.now() - datetime.timedelta(
                        seconds=self.expiry
                    )
                ).delete()
        except:
            pass

    @staticmethod
    def get_model(name):
        names = name.split('.')
        mod = __import__('.'.join(names[:-1]), fromlist=names[-1:])
        return getattr(mod, names[-1])
