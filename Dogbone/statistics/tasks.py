import logging

from celery import shared_task

from .models import Event
from django.contrib.auth.models import User


@shared_task
def log_statistic_event(event_name, event_user_id, event_data=None):
    user = User.objects.get(id=event_user_id)

    event = Event(name=event_name, user=user, data=event_data)
    try:
        event.save()
        return True
    except Exception as exception:
        logging.error(u'Could not save {!s}: {!r}'.format(event, exception))
        return False
