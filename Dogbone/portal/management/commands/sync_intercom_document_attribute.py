import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from portal.models import UserProfile
from core.models import Document
from portal.tasks import update_intercom_custom_attribute, log_intercom_custom_event


class Command(BaseCommand):

  def handle(self, *args, **options):
    users = User.objects.all()
    for user in users:
      #Update the documents uploaded attribute
      try:
        doc_count = user.details.get_document_upload_count()
        print("Updating user=%s with count %s" % (user.username, doc_count))
        update_intercom_custom_attribute(email=user.email, attribute_name="Documents Uploaded", attribute_value=user.details.document_upload_count)
      except:
        print(user, '-- No Details')