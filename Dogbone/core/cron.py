import datetime
import collections
import logging

from celery import shared_task
from notifications.models import Notification
from django.core import management


##################################################################################################
#
#  Periodic Tasks
#
##################################################################################################

@shared_task
def periodic_send_notification_reminders():
    """
    Send an email for unread notifications in the past hour or so
    :return:
    """
    from portal.mailer import BeagleMailer
    from portal.settings import UserSettings

    # Notifications that are older than 10 mins but newer than 1 hour
    notifications = Notification.objects.filter(emailed=False, unread=True,
                                                timestamp__gte=datetime.datetime.now() - datetime.timedelta(minutes=60),
                                                timestamp__lte=datetime.datetime.now() - datetime.timedelta(minutes=10))\
                                        .order_by('-timestamp')

    if not notifications:
        logging.info("No new notifications found")
        return True

    aggregated_notifications = collections.defaultdict(list)

    for notification in notifications:
        if notification.recipient != notification.actor:
            aggregated_notifications[notification.recipient].append(notification)

    for user in aggregated_notifications.keys():
        settings = UserSettings(user)
        if settings.get_setting('email_digest_notification'):
            logging.info("Sending notifications for user=%s", user)
            try:
                user_notifications = aggregated_notifications[user][:10]
                logging.info("Sending %s pending notifications email to %s", len(user_notifications), user)
                BeagleMailer.notification_reminders(user, user_notifications)
            except Exception as e:
                logging.error("Exception during periodic_send_notification_reminders for user=%s, exc=%s", user, e)
        else:
            logging.info("Sending pending notifications digest email FORBIDDEN by user settings: user=%s", user)

    notifications.update(emailed=True)
    return True

@shared_task
def remove_expired_session_keys():
    """
    Remove session tokens that have expired from the database
    """
    management.call_command('clearsessions', verbosity=0)
