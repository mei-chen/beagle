import os

from django.core.management.base import BaseCommand
from django.conf import settings
from portal.models import UserProfile


class Command(BaseCommand):
    help = 'Moves the db field `avatar` to `avatar_s3` format. No actual file is moved'

    def handle(self, *args, **options):
        for profile in UserProfile.objects.all():
            try:
                folders = profile.avatar.path.split(os.path.sep)
                start_index = folders.index('profile_photo')
                folders = folders[start_index:]
                path = '/'.join(folders)
                profile.avatar_s3 = "%s:%s" % (settings.PROFILE_PICTURE_BUCKET, path)
                profile.save()
                self.stdout.write('[*] migrated user=%s' % profile.user)
            except:
                pass