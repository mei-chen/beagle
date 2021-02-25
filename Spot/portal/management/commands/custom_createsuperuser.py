# Django
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Custom create superuser command to progammatically create user in ansible'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            dest='username',
            help='Username for superuser'
        ),

        parser.add_argument(
            '--password',
            dest='password',
            help='Password for superuser'
        ),

        parser.add_argument(
            '--email',
            dest='email',
            help='Email for superuser'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')
        email = options.get('email')

        user = User.objects.filter(username=username).first()
        if not user:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS('Successfully created a super user'))
        else:
            self.stdout.write(self.style.ERROR('User already exists'))
