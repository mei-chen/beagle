import os
import logging
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from portal.models import ProjectArchive

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=ProjectArchive)
def project_archive_delete(sender, instance, **kwargs):
    try:
        if not instance.content_file:
            return
        path = instance.content_file.path
        os.remove(path)
    except (OSError, ValueError):
        logger.warning("%s deletion failed" % instance, exc_info=True)
