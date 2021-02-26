import redis
import logging


class RedisConnection:
    """
    Wrapper class for managing a Redis connection
    """

    def __init__(self, url='redis://localhost:6379/0'):
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
