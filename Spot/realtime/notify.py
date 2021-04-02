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

    class ServerNotifications:
        GENERIC_NOTIFICATION = 'GENERIC_NOTIFICATION'
        CLASSIFIER_TRAINED_NOTIFICATION = 'CLASSIFIER_TRAINED_NOTIFICATION'
        CLASSIFIER_TRAINING_ERROR_NOTIFICATION = 'CLASSIFIER_TRAINING_ERROR_NOTIFICATION'
        CLASSIFIER_DECISION_FUNCTION_PLOTTED_NOTIFICATION = 'CLASSIFIER_DECISION_FUNCTION_PLOTTED_NOTIFICATION'
        CLASSIFIER_DECISION_FUNCTION_PLOTTING_ERROR_NOTIFICATION = 'CLASSIFIER_DECISION_FUNCTION_PLOTTING_ERROR_NOTIFICATION'
        EXPERIMENT_SIMULATED_NOTIFICATION = 'EXPERIMENT_SIMULATED_NOTIFICATION'
        EXPERIMENT_EVALUATED_NOTIFICATION = 'EXPERIMENT_EVALUATED_NOTIFICATION'
        EXPERIMENT_EVALUATING_ERROR_NOTIFICATION = 'EXPERIMENT_EVALUATING_ERROR_NOTIFICATION'
        EXPERIMENT_GENERATED_NOTIFICATION = 'EXPERIMENT_GENERATED_NOTIFICATION'
        EXPERIMENT_GENERATING_ERROR_NOTIFICATION = 'EXPERIMENT_GENERATING_ERROR_NOTIFICATION'
        LABELING_TASK_SAMPLES_SELECTED_NOTIFICATION = 'LABELING_TASK_SAMPLES_SELECTED_NOTIFICATION'
        LABELING_TASK_SAMPLES_STORED_NOTIFICATION = 'LABELING_TASK_SAMPLES_STORED_NOTIFICATION'
        LABELING_TASK_SUPERVISED_DATASET_EXPORTED_NOTIFICATION = 'LABELING_TASK_SUPERVISED_DATASET_EXPORTED_NOTIFICATION'
        LABELING_TASK_EVALUATION_SCORE_EXPANDED_NOTIFICATION = 'LABELING_TASK_EVALUATION_SCORE_EXPANDED_NOTIFICATION'
        LABELING_TASK_ACCORD_MATRIX_COMPUTED_NOTIFICATION = 'LABELING_TASK_ACCORD_MATRIX_COMPUTED_NOTIFICATION'
        LABELING_TASK_EXPERIMENT_BUILT_NOTIFICATION = 'LABELING_TASK_EXPERIMENT_BUILT_NOTIFICATION'

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
        if conn is None:
            logging.error('Connection is None in NotificationManager')
            return False

        for channel in msg.channels:
            try:
                logging.info(payload)
                conn.publish(channel, json.dumps(payload))
            except Exception as e:
                logging.error('Could not publish message. Encountered=%s', str(e))

        logging.info('Sent')
        return True

    @classmethod
    def notify_client(cls, session_key, message=None):
        channels = [cls.get_session_channel(session_key)]
        event_name = cls.ACTIONS['NOTIFICATION']
        return NotificationMessage(cls, channels, event_name, message)
