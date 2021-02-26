import time
import logging
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User

from intercom import Intercom
from intercom.errors import IntercomError
from intercom import User as IntercomUser
from intercom import Event as IntercomEvent

from .slack import SlackPostAPI


Intercom.app_id = settings.INTERCOM_APP_ID
Intercom.app_api_key = settings.INTERCOM_API_KEY


##################################################################################################
#
#   Slack Tasks
#
##################################################################################################


@shared_task
def slack(webhook, message, channel, username=None, icon_emoji=None):
    api = SlackPostAPI(webhook)
    try:
        return api.send_message(message, channel=channel, username=username, icon_emoji=icon_emoji)
    except:
        return False


def send_slack_message(message, channel='#general'):
    """
    Send a slackbot message
    :param message: The actual message
    :param channel: The channel: #dev, #general etc...
    :return:
    """
    return slack.delay(settings.SLACK_WEBHOOK, message, channel)


##################################################################################################
#
#   Intercom Tasks
#
##################################################################################################


@shared_task
def update_intercom_document_count(email):
    try:
        intercom_user = IntercomUser.find(email=email)
        beagle_user = User.objects.get(email__iexact=email)
        intercom_user.custom_attributes["Documents Uploaded"] = beagle_user.details.document_upload_count
        intercom_user.save()
        return True
    except IntercomError:
        logging.error('The Intercom user with email=%s could not be found' % email)
    except User.DoesNotExist:
        logging.error('Could not find the user with email=%s in the Beagle Database' % email)
    return False


@shared_task
def update_intercom_custom_attribute(email, attribute_name, attribute_value):
    try:
        intercom_user = IntercomUser.find(email=email)
        intercom_user.custom_attributes[attribute_name] = attribute_value
        intercom_user.save()
        return True
    except IntercomError as e:
        logging.error('IntercomError: %s' % e)
    return False


@shared_task
def log_intercom_custom_event(email, event_name, metadata=None, created_at=None):
    if not created_at:
        created_at = int(time.time())
    if not metadata:
        metadata = {}

    try:
        IntercomEvent.create(
            event_name=event_name,
            created_at=created_at,
            email=email,
            metadata=metadata
        )
        return True
    except IntercomError as e:
        logging.error('IntercomError: %s' % e)
    return False
