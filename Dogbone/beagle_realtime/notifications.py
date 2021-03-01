import json
import logging
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from .base import RedisConnection, NotificationMessage


class NotificationManager:

    redis_manager = RedisConnection(settings.REDIS_URL)

    USER_SESSION_NAMESPACE = "user-notifications.%(session_key)s"
    GLOBAL_NAMESPACE = 'global'

    class ServerNotifications:
        # Sent to the user notifying that their document started processing
        DOCUMENT_PROCESSING_STARTED_NOTIFICATION = 'DOCUMENT_PROCESSING_STARTED'

        # Process of parties identification has been started
        DOCUMENT_PARTY_IDENTIFICATION_STARTED = 'DOCUMENT_PARTY_IDENTIFICATION_STARTED'

        # Process of document reanalysis has been started
        DOCUMENT_REANALYSIS_STARTED = 'DOCUMENT_REANALYSIS_STARTED'

        # Process of Responsibilities, Liabilities, Terminations and
        # External References finding has been started
        DOCUMENT_RLTE_ANALYSIS_STARTED = 'DOCUMENT_RLTE_ANALYSIS_STARTED'

        # Process of applying learners has been started
        DOCUMENT_APPLY_LEARNERS_STARTED = 'DOCUMENT_APPLY_LEARNERS_STARTED'

        # Process of applying Spot experiments has been started
        DOCUMENT_APPLY_SPOT_EXPERIMENTS_STARTED = 'DOCUMENT_APPLY_SPOT_EXPERIMENTS_STARTED'

        # Process of keywords finding has been started
        DOCUMENT_KEYWORDS_SEARCH_STARTED = 'DOCUMENT_KEYWORDS_SEARCH_STARTED'

        # Sent to the user notifying that their document is completed
        DOCUMENT_COMPLETED_NOTIFICATION = 'DOCUMENT_COMPLETED'

        # Sent to the user notifying that their document is converted
        DOCUMENT_CONVERTED_NOTIFICATION = 'DOCUMENT_CONVERTED'

        # Sent to the user notifying that their document is uploaded
        DOCUMENT_UPLOADED_NOTIFICATION = 'DOCUMENT_UPLOADED'

        # Sent to the user notifying that their document is deleted
        DOCUMENT_DELETED_NOTIFICATION = "DOCUMENT_DELETED"

        # Sent to a user who has been invited to a document
        DOCUMENT_INVITE_RECEIVED_NOTIFICATION = 'DOCUMENT_INVITE_RECEIVED'

        # Sent to a user that issued an invitation
        DOCUMENT_INVITE_SENT_NOTIFICATION = 'DOCUMENT_INVITE_SENT'

        # Sent to a user who has been uninvited from a document
        DOCUMENT_INVITE_RECEIVED_REVOKED_NOTIFICATION = 'DOCUMENT_INVITE_RECEIVED_REVOKED'

        # Sent to a user that revoked an invitation
        DOCUMENT_INVITE_SENT_REVOKED_NOTIFICATION = 'DOCUMENT_INVITE_SENT_REVOKED'

        # Sent to a user who has rejected an invite
        DOCUMENT_INVITE_RECEIVED_REJECTED_NOTIFICATION = 'DOCUMENT_INVITE_REJECTED_REVOKED'

        # Something in the document has changed
        DOCUMENT_CHANGED_NOTIFICATION = 'DOCUMENT_CHANGED'

        # Bulk document tags created
        DOCUMENT_BULK_TAGS_CREATED_NOTIFICATION = 'DOCUMENT_BULK_TAGS_CREATED'

        # Bulk document tags deleted
        DOCUMENT_BULK_TAGS_DELETED_NOTIFICATION = 'DOCUMENT_BULK_TAGS_DELETED'

        # Bulk document tags updated
        DOCUMENT_BULK_TAGS_UPDATED_NOTIFICATION = 'DOCUMENT_BULK_TAGS_UPDATED'

        # Lock in the document has changed
        DOCUMENT_LOCK_CHANGED_NOTIFICATION = 'DOCUMENT_LOCK_CHANGED'

        # Something in the document has changed
        DOCUMENT_EXPORT_READY = 'DOCUMENT_EXPORT_READY'

        # If there was in error in the document export
        DOCUMENT_EXPORT_ERROR = 'DOCUMENT_EXPORT_ERROR'

        # The owner of the document has been changed
        DOCUMENT_OWNER_CHANGED_NOTIFICATION = 'DOCUMENT_OWNER_CHANGED'

        # A new comment has been added
        COMMENT_ADDED_NOTIFICATION = 'COMMENT_ADDED'

        # Collaborator logged in
        COLLABORATOR_LOGIN = 'COLLABORATOR_LOGIN'

        # Activity update
        ACTIVITY_UPDATE = 'ACTIVITY_UPDATE'

        # Fully refresh all notifications
        NOTIFICATIONS_FULL_UPDATE = 'NOTIFICATIONS_FULL_UPDATE'

        # While converting a file, the corresponding document model could not be found
        DOCUMENT_ERROR_NOT_FOUND_NOTIFICATION = 'DOCUMENT_ERROR_NOT_FOUND'

        # The document that is converting is malformed
        DOCUMENT_ERROR_MALFORMED_NOTIFICATION = 'DOCUMENT_ERROR_MALFORMED'

        # We only support English. So everything else is an error of humanity
        DOCUMENT_ERROR_UNSUPPORTED_LANGUAGE_NOTIFICATION = 'DOCUMENT_ERROR_UNSUPPORTED_LANGUAGE'

        # The document format unsupported
        DOCUMENT_ERROR_FORMAT_UNSUPPORTED_NOTIFICATION = 'DOCUMENT_ERROR_FORMAT_UNSUPPORTED'

        # The document format unsupported
        DOCUMENT_ERROR_TOO_LARGE_TO_OCR = 'DOCUMENT_ERROR_TOO_LARGE_TO_OCR'

        # There was an error on EasyPDF's end
        EASYPDF_ERROR = 'EASYPDF_ERROR'

        # The document analysis was weak
        WEAK_DOCUMENT_ANALYSIS = "WEAK_DOCUMENT_ANALYSIS"

        # The batch preparing was finished
        BATCH_EXPORT_READY = 'BATCH_WAS_PREPARED'

        # The batch processing was completed
        BATCH_PROCESSING_COMPLETED = 'BATCH_PROCESSING_COMPLETED'

        # The batch turned out to be empty
        BATCH_EMPTY = 'BATCH_EMPTY'

    @classmethod
    def get_session_channel(cls, session_key):
        """
        The naming convention of user session channels
        :param session_key: User session key
        :return:
        """
        return cls.USER_SESSION_NAMESPACE % {'session_key': session_key}

    @classmethod
    def create_message(cls, channels=None, event_name=None, message=None):
        if channels is None:
            channels = []

        return NotificationMessage(cls, channels, event_name, message)

    @classmethod
    def create_user_message(cls, user, event_name=None, message=None):
        """
        Get all the sessions of a user and create
        a message using the `get_session_channel`
        channel naming convention

        :param user: The user to send notifications to
        :param event_name: The message type. The client should listen for .on(event_name)
        :param message: The actual payload
        :return:
        """
        channels = [cls.get_session_channel(session.session_key) for session in user.session_set.all()]
        return cls.create_message(channels=channels, event_name=event_name, message=message)

    @classmethod
    def create_batch_message(cls, batch, event_name=None, message=None, except_sessions=None):
        """
        Get all the sessions of users related to the batch and create
        a message using the `get_session_channel`
        channel naming convention
        
        :param batch: The batch on which we want to send notifications
        :param event_name: The message type. The client should listen for .on(event_name)
        :param message: The actual payload
        :return:
        """

        if not except_sessions:
            except_sessions = []
        except_sessions = set(except_sessions)

        user = batch.owner
        channels = []
        for session in user.session_set.all():
            if session.session_key not in except_sessions:
                channels.append(cls.get_session_channel(session.session_key))
        return cls.create_message(channels=set(channels), event_name=event_name, message=message)

    @classmethod
    def create_document_message(cls, document, event_name=None, message=None, except_users=None, except_sessions=None):
        """
        Get all the sessions of users related to the document and create
        a message using the `get_session_channel`
        channel naming convention

        :param document: The document on which we want to send notifications
        :param event_name: The message type. The client should listen for .on(event_name)
        :param message: The actual payload
        :return:
        """

        if not except_users:
            except_users = []
        except_users = set(except_users)

        if not except_sessions:
            except_sessions = []
        except_sessions = set(except_sessions)

        # TODO (Bogdan): Optimize this to prefetch the sessions for users
        users = set(list(document.collaborators) + [document.owner] +
                    list(User.objects.filter(is_superuser=True))) - except_users
        channels = []
        for user in users:
            for session in user.session_set.all():
                if session.session_key not in except_sessions:
                    channels.append(cls.get_session_channel(session.session_key))
        return cls.create_message(channels=set(channels), event_name=event_name, message=message)

    @classmethod
    def create_collaborators_message(cls, user, event_name=None, message=None, except_users=None, except_sessions=None):
        """
        Send a notification to all the collaborators of the user

        :param user: get all the collaborators of this user
        :param event_name: The message type. The client should listen for .on(event_name)
        :param message: The actual payload
        :return:
        """
        from core.tools import user_collaborators
        if not except_users:
            except_users = []

        except_users = set(except_users)

        if not except_sessions:
            except_sessions = []

        except_sessions = set(except_sessions)

        users = user_collaborators(user) - except_users
        channels = []
        for user in users:
            for session in user.session_set.all():
                if session.session_key not in except_sessions:
                    channels.append(cls.get_session_channel(session.session_key))
        return cls.create_message(channels=set(channels), event_name=event_name, message=message)

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
               conn.publish(channel, json.dumps(payload))
            except Exception as e:
                logging.error('Could not publish message. Encountered=%s', str(e))

        return True


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
            'created': str(datetime.datetime.now()),
            'event_name': event_name
        }
