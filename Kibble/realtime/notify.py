# Python
import logging
import json
import uuid

# Django
from django.conf import settings

# Third Party
import redis


class RedisConnection:
    """
    Wrapper class for managing a Redis connection
    """

    def __init__(self, url=settings.REDIS_URL):
        self.__connection = None
        self.url = url

    def get_connection(self):
        """
        Singleton pattern
        """
        if self.__connection is None:
            try:
                self.__connection = redis.StrictRedis.from_url(self.url)
                if self.__connection is None:
                    raise Exception('Redis Connection is None')
            except Exception as e:
                logging.critical('Could not establish Redis connection: %s', str(e))
                self.__connection = None

        return self.__connection


class NotificationMessage:
    def __init__(self, manager, channels=None, event_name=None, message=None):
        """
        :param manager: A class with a `send` method
        :param channels: The channels the message will be issued to
        :param event_name: The type of event
        :return:
        """

        if channels is None:
            channels = []

        self.manager = manager
        self.channels = channels
        self.event_name = event_name
        self.message = message

    def set_channels(self, channels):
        self.channels = channels

    def set_event_name(self, event_name):
        self.event_name = event_name

    def set_message(self, message):
        self.message = message

    def send(self):
        if not self.channels:
            return False

        if self.message is None:
            logging.warning('Issuing an empty message')
        self.manager.send(self)
        return True


class NotificationManager:
    redis_manager = RedisConnection(settings.REDIS_URL)
    USER_SESSION_NAMESPACE = "user-notifications.%(session_key)s"
    ACTIONS = {
        'NOTIFICATION': 'NOTIFICATION'
    }

    @classmethod
    def get_session_channel(cls, session_key):
        """
        The naming convention of user session channels
        :param session_key: User session key
        :return:
        """
        return cls.USER_SESSION_NAMESPACE % {'session_key': session_key}

    @classmethod
    def wrap_messsage(cls, event_name, message):
        """
        Add convenient metadata to the message
        :param event_name: The event that will be triggered on client
        :param message: dict object, the actual message that is sent
        :return: wrapped message. A dict containing the original message under `message` field
        """

        return {
            'message': message,
            'event_name': event_name,
            'message_uuid': str(uuid.uuid4())
        }

    @classmethod
    def send(cls, msg):
        """
        Send the actual notification through the redis pubsub
        :param msg: The NotificationMessage object
        :return:
        """

        payload = cls.wrap_messsage(msg.event_name, msg.message)
        conn = cls.redis_manager.get_connection()
        success = False
        if conn is None:
            logging.error('Connection is None in NotificationManager')
            return False

        for channel in msg.channels:
            try:
                logging.info(payload)
                conn.publish(channel, json.dumps(payload))
                # if we sent at least one message - return True
                success = True
            except Exception as e:
                logging.error('Could not publish message. Encountered=%s', str(e))

        if success:
            logging.info('Notification was sent successfully')
        else:
            logging.warn('Notification was NOT sent')
        return success

    @classmethod
    def notify_client(cls, session_key=None, message='Success'):
        channels = [cls.get_session_channel(session_key)]
        event_name = cls.ACTIONS['NOTIFICATION']
        return NotificationMessage(cls, channels, event_name, message)

    @classmethod
    def popup_notification(cls, session, message, level='info'):
        ret = {
            'notify': {
                'level': level,
                'message': message,
            }
        }
        message = cls.notify_client(session, ret)
        message.send()
