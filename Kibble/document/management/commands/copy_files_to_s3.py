import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.conf import settings
from botocore.exceptions import ClientError

from document.models import Document
from portal.models import File


class Command(BaseCommand):
    help = 'Copy all media files to S3 storage'

    def get_content(self, f):
        localpath = os.path.join(settings.MEDIA_ROOT, f.name)
        if not os.path.exists(localpath):
            print('{} does not exist!'.format(localpath))
            return
        if not os.path.isfile(localpath):
            print('{} should be a file!'.format(localpath))
            return
        return SimpleUploadedFile(
            os.path.basename(f.name),
            open(localpath).read(),
            None
        )

    def copy_to_new_dir(self, old_path, new_path):
        # Move files to new place for DB consistency if path is changed
        # in case when S3 is disabled after testing
        if not old_path or old_path == new_path:
            return
        localpath = os.path.join(settings.MEDIA_ROOT, new_path)
        basedir = os.path.dirname(localpath)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        print('Local storage: moving {} to {}'.format(old_path, new_path))
        os.rename(os.path.join(settings.MEDIA_ROOT, old_path), localpath)

    def process_field(self, field):
        name = field.name
        try:
            size = field.size
            print('{} is on S3, size: {}'.format(name, size))
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Remote file not found, try to store
                content = self.get_content(field)
                if not content:
                    return None, None
                print('{} copied to S3'.format(name))
                return name, content
            else:
                # Unknown exception, print error
                print(u'; '.join(e.args))
        return None, None

    def process_files(self):
        for f in File.objects.all():
            old_name, content = self.process_field(f.content)
            if old_name:
                f.content = content
                f.save()
                self.copy_to_new_dir(old_name, f.content.name)

    def process_documents(self):
        for d in Document.objects.all():
            old_doc_name, doc_content = self.process_field(d.content_file)
            old_txt_name, txt_content = self.process_field(d.text_file)
            if old_doc_name or old_txt_name:
                if doc_content:
                    d.content_file = doc_content
                if txt_content:
                    d.text_file = txt_content
                d.save()
                self.copy_to_new_dir(old_doc_name, d.content_file.name)
                self.copy_to_new_dir(old_txt_name, d.text_file.name)

    def handle(self, *args, **options):
        if settings.DEFAULT_FILE_STORAGE.find('S3Boto') == -1:
            print('S3 storage is not configured!')
            return

        self.process_files()
        self.process_documents()
