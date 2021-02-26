import logging

from celery import shared_task

from .models import Event


@shared_task
def log_statistic_event(event_name, event_user, event_data=None):
    event = Event(name=event_name, user=event_user, data=event_data)
    try:
        event.save()
        return True
    except Exception as exception:
        logging.error(u'Could not save {!s}: {!r}'.format(event, exception))
        return False
