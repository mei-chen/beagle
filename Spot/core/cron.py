from celery import shared_task
from django.core import management

@shared_task
def remove_expired_session_keys():
    """
    Remove session tokens that have expired from the database
    """
    management.call_command('clearsessions', verbosity=0)