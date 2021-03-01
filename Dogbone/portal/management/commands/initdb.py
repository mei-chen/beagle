from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.db.utils import IntegrityError


class Command(BaseCommand):
    help = 'Seeds the database with minimum data so that the app can be used'

    def handle(self, *args, **options):
        self.stdout.write('[*] Starting command\n')
        from dogbone import init_db

        for username, user_dict in init_db.USERS.iteritems():
            user = User(username=username,
                        email=user_dict['email'],
                        is_superuser=True,
                        is_staff=True,
                        first_name=user_dict['first_name'],
                        last_name=user_dict['last_name'])

            self.stdout.write('[*] Saving user `%s`\n' % str(user))
            user.set_password(user_dict['password'])

            self.stdout.write('[*] Password set for user: %s \n' % user.username)

            try:
                user.save()
                self.stdout.write('[*] User `%s` created\n' % user.username)

            except Exception as e:
                self.stdout.write('[!] User `%s` could not be created (%s)\n' % (user.username, str(e)))

