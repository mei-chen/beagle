# Python
import email
import validators
import os

# Django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# App
from core.process_mail import main_sample, main
from server.models import Detail


FILE_NAME = 'test.email'
TEST_EMAIL_PATH = test_email = os.path.join(settings.BASE_DIR, 'core', 'management', 'commands', FILE_NAME)
TEST_DOMAIN = '' # use ngrok.io to test locally

class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('Processing the mail', ending='')

        with open(TEST_EMAIL_PATH) as input_email:
            content = input_email.read()
        message = email.message_from_string(content)

        main(message, TEST_DOMAIN, content)
