from authentication.models import AuthToken
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Attach a TokenAuth model to all of the User models'

    def handle(self, *args, **options):
        for user in User.objects.all():
            _, created = AuthToken.create_token_model(user)

            if created:
                self.stdout.write("Created AuthToken for %s\n" % user)