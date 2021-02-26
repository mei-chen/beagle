from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from portal.models import OneTimeLoginHash
from portal.mailer import BeagleMailer


class Command(BaseCommand):
    def handle(self, *args, **options):
        for email in args:
            try:
                user = User.objects.get(email__iexact=email)
                h = OneTimeLoginHash.create(user)
                BeagleMailer.auto_account_creation_notification(h)
            except User.DoesNotExist:
                self.stderr.write('No such user: "%s" ' % email)
