from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from portal.models import Profile


class Command(BaseCommand):
    help = 'Create profiles for already existing users'

    def handle(self, *args, **options):

        for user in User.objects.all():
            try:
                user.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=user)
                self.stdout.write(
                    self.style.SUCCESS('Created profile for user: %s' % user.username)
                )
