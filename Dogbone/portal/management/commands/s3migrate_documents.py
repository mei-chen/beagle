import os
import traceback

from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Document


class Command(BaseCommand):
    help = 'Moves the db field `docx_path` to `docx_s3` format. No actual file is moved'

    def handle(self, *args, **options):
        for document in Document.lightweight.exclude(docx_file__isnull=True).exclude(docx_file__exact=''):
            try:
                # chunks = profile.avatar.path.split(os.path.sep)
                chunks = os.path.split(document.docx_file)
                if not chunks:
                    continue
                file_name = chunks[-1]
                document.docx_s3 = "%s:%s" % (settings.UPLOADED_DOCUMENTS_BUCKET, 'uploads/media/%s' % file_name)
                self.stdout.write('[*] migrated document=%s docx_file="%s" => docx_s3="%s"' % (
                    document, document.docx_file, document.docx_s3))
                document.docx_file = None
                document.save()
            except:
                print traceback.print_exc()