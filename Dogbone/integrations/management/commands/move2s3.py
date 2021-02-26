import traceback

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from integrations.s3 import get_s3_bucket_manager


class Command(BaseCommand):
    help = 'move a folder to S3. usage: ./manage.py move2s3 SOURCE_FOLDER --bucket=S3BUCKET --path=S3PATH'

    option_list = BaseCommand.option_list + (
        make_option('--bucket', help='In which bucket to store the folder'),
        make_option('--acl', help='what ACL to set to the files', default=None),
        make_option('--path', help='The path in S3 to store the folder to', default=''),
    )

    def handle(self, *args, **options):
        if 'bucket' not in options:
            raise CommandError('Please specify a bucket. Use --bucket option')

        fm = get_s3_bucket_manager(options['bucket'])
        self.stdout.write('Starting moving files')
        try:
            fm.save_folder(options['path'], args[0], acl=options['acl'])
        except Exception as e:
            self.stderr.write('Encountered error: %s' % str(e))
            self.stderr.write(traceback.format_exc())

        self.stdout.write('Finished moving files')