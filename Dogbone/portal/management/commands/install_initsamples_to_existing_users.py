from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.tasks import initialize_sample_docs


class Command(BaseCommand):
    help = 'As init sample docs are installed on user creation, old users do not get them'

    def handle(self, *args, **options):
        for user in User.objects.all():
            try:
                initialize_sample_docs.delay(user)
            except:
                pass
