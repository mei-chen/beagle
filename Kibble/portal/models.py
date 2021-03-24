from __future__ import unicode_literals

import io
import logging
import os
import img2pdf
import magic
import re
import tempfile

from jsonfield import JSONField
from zipfile import ZipFile, ZIP_DEFLATED

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from document.models import Document, Sentence, PersonalData, CustomPersonalData
from portal.constants import ProjectStatus
from utils.conversion import (
    requires_ocr, pdf_to_docx, txt_to_docx, doc_to_docx, compress_to_zip,
    html_to_docx, xml_to_docx
)

logger = logging.getLogger(__name__)


def make_upload_path(instance, fname):
    if instance.batch is not None:
        name = instance.batch.name.replace(
            ' ', '_')[:settings.BATCH_NAME_TRUNCATE_CHARS]
        predicate = '{}_{}'.format(instance.batch.id, name)
    else:
        predicate = 'initially_unassigned'
    path = os.path.join('batches', predicate, fname)
    return path


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    file_auto_process = models.BooleanField(default=settings.FILE_AUTO_PROCESS)
    auto_cleanup_tools = JSONField(default=settings.AUTO_CLEANUP_TOOLS)
    obfuscate_string = models.CharField(max_length=255, default=settings.OBFUSCATE_STRING)
    highlight_color = models.CharField(max_length=16, default=settings.HIGHLIGHT_COLOR)
    auto_gather_personal_data = models.BooleanField(default=settings.AUTO_PERSONAL_DATA)
    obfuscated_export_ext = models.CharField(max_length=4, default=settings.OBFUSCATED_EXPORT_EXT)
    sentence_word_threshold = models.SmallIntegerField(default=settings.SENTENCE_WORD_THRESHOLD)
    personal_data_types = JSONField(default=settings.PERSONAL_DATA_TYPES)
    min_similarity_score = models.FloatField(default=settings.MIN_SIMILARITY_SCORE)
    auth_token = models.CharField(max_length=40, null=True)

    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)
        self.prev_personal_data_types = self.personal_data_types


class Project(models.Model):
    name = models.CharField(max_length=200, unique=True)
    owner = models.ForeignKey(User, null=True, blank=True,
                              related_name='projects',on_delete=models.CASCADE)
    status = models.SmallIntegerField(choices=ProjectStatus.choices(),
                                      default=ProjectStatus.Active.value)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_zipped_batches(self):
        if self.batches.count() > 0:
            filelike = io.BytesIO()
            with ZipFile(filelike, 'w', ZIP_DEFLATED) as zf:
                for batch in self.batches.all():
                    zipped_batch = batch.get_zipped_files()
                    filepath = os.path.join(
                        '%s_%s.zip' % (batch.id, batch.name.replace(' ', '_')[:settings.BATCH_NAME_TRUNCATE_CHARS])
                    )
                    zf.writestr(filepath, zipped_batch.getvalue())
            return ContentFile(filelike.getvalue(), '{0.id}_{0.name}.zip'.format(self))
        return None

    def compress(self):
        if hasattr(self, 'archive'):
            self.archive.delete()
        archive = ProjectArchive.objects.create(
            project=self,
            content_file=self.get_zipped_batches()
        )
        if self.status != ProjectStatus.Archived.value:
            self.status = ProjectStatus.Archived.value
            self.save()
        return archive

    def __str__(self):
        return self.name

    @property
    def collaborators(self):
        invites = self.collaboration_invites.select_related('invitee')
        invites = invites.order_by('-id')
        return [invite.invitee for invite in invites]


class Batch(models.Model):
    name = models.CharField(max_length=200)
    project = models.ManyToManyField(Project, related_name='batches')
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    upload_error = models.CharField(max_length=50, blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    process_time = models.TimeField(null=True, blank=True)
    owner = models.ForeignKey(User, null=True, blank=True,
                              related_name='batches',on_delete=models.CASCADE)
    personal_data_gathered = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "batches"

    def get_upload_date(self):
        return self.upload_date.strftime('%Y-%m-%d')

    def get_upload_time(self):
        return self.upload_date.strftime('%H:%M')

    def __str__(self):
        return self.name

    def get_converted_documents(self, plaintext=False):
        docs = Document.objects.filter(source_file__batch=self)
        if plaintext:
            return compress_to_zip(
                [i.text_file if i.text_file else None for i in docs])
        return compress_to_zip(
            [i.content_file if i.content_file else None for i in docs])

    @property
    def upload_dir(self):
        name = self.name.replace(' ', '_')[:settings.BATCH_NAME_TRUNCATE_CHARS]
        path = os.path.join(
            settings.MEDIA_ROOT, 'batches', '%s_%s' % (self.id, name)
        )
        return path

    def get_zipped_sentences(self, ziptype):
        if ziptype not in ['csv', 'json']:
            raise ValueError('Wrong ziptype %s' % ziptype)
        docs = Document.objects.filter(source_file__batch=self)
        file = 'sentences_%s_%s.zip' % (self.name, ziptype)
        dst = '%s/%s' % (settings.MEDIA_ROOT, file)
        with ZipFile(dst, mode='w') as zf:
            for doc in filter(lambda d: d.has_sentences, docs):
                text = doc.get_json() if ziptype == 'json' else doc.get_csv()
                zf.writestr(
                    doc.name + '.' + ziptype,
                    text
                )
        return dst, '%s%s' % (settings.MEDIA_URL, file)

    def get_zipped_reports(self, ziptype, report_type):
        if ziptype not in ['csv', 'json']:
            raise ValueError('Wrong ziptype {}'.format(ziptype))
        dst = '{}/reports_{}.zip'.format(settings.MEDIA_ROOT, self.name)
        with ZipFile(dst, mode='w') as zf:
            for report in filter(lambda r: bool(r.json), self.reports.filter(report_type=report_type)):
                content = report.json if ziptype == 'json' else report.generate_csv().getvalue()
                zf.writestr(
                    report.name + '.' + ziptype,
                    content
                )
        return dst, '{}reports_{}.zip'.format(settings.MEDIA_URL, self.name)

    def get_cleaned_documents(self, plaintext=False):
        docs = Document.objects.filter(source_file__batch=self)
        files = []
        for doc in filter(lambda doc: hasattr(doc, 'cleaned'), docs):
            if plaintext:
                files.append(doc.cleaned.text_file)
            else:
                files.append(doc.cleaned.content_file)
        return compress_to_zip(files)

    def get_zipped_files(self):
        filelike = io.BytesIO()
        with ZipFile(filelike, 'a', ZIP_DEFLATED, False) as zf:
            for fileobj in self.files.all():
                zf.writestr(
                    fileobj.filename, fileobj.content.read())
        return filelike

    @property
    def project_name(self):
        return ', '.join(self.project.all().values_list('name', flat=True))

    def _sentences_count(self):
        return Sentence.objects.filter(
            document__source_file__batch=self
        ).count()

    @property
    def sentences_count(self):
        return self._sentences_count()

    @property
    def collaborators(self):
        invites = self.collaboration_invites.select_related('invitee')
        invites = invites.order_by('-id')
        return [invite.invitee for invite in invites]


class File(models.Model):
    (
        FILE_UNKNOWN, FILE_DOCX, FILE_DOC, FILE_PDF, FILE_TXT,
        FILE_IMG, FILE_ZIP, FILE_HTML, FILE_XML
    ) = range(9)

    TYPE_CHOICES = (
        (FILE_UNKNOWN, 'Unknown'),
        (FILE_DOCX, 'DOCX'),
        (FILE_DOC, 'DOC'),
        (FILE_PDF, 'PDF'),
        (FILE_TXT, 'TXT'),
        (FILE_IMG, 'Image'),
        (FILE_ZIP, 'ZIP'),
        (FILE_HTML, 'HTML'),
        (FILE_XML, 'XML')
    )

    FILE_TYPES = (
        ('application/vnd.openxmlformats-officedocument.'
         'wordprocessingml.document', FILE_DOCX),
        ('application/msword', FILE_DOC),
        ('application/pdf', FILE_PDF),
        ('text/plain', FILE_TXT),
        (re.compile(r'^text/x-'), FILE_TXT),
        ('image/jpg', FILE_IMG),
        ('image/jpeg', FILE_IMG),
        ('image/png', FILE_IMG),
        ('image/tiff', FILE_IMG),
        ('application/zip', FILE_ZIP),
        ('text/html', FILE_HTML),
        ('application/xml', FILE_XML)
    )

    file_name = models.CharField(max_length=200, null=True)
    content = models.FileField(upload_to=make_upload_path, max_length=400)
    batch = models.ForeignKey(Batch, related_name='files',
                              null=True, blank=True,on_delete=models.CASCADE)
    need_ocr = models.NullBooleanField(default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(choices=TYPE_CHOICES, null=True)
    auto_processed = models.CharField(max_length=7, null=True)

    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)
        self.mime = None

    @property
    def filename(self):
        return self.file_name or os.path.basename(self.content.name)

    def __str__(self):
        return self.content.name

    def get_content_file(self):
        if not self.content:
            return None
        f = tempfile.NamedTemporaryFile(delete=True, suffix=os.path.splitext(self.content.name)[1])
        self.content.seek(0)
        f.write(self.content.read())
        self.content.seek(0)
        f.flush()
        return f

    def check_zipped_type(self):
        with ZipFile(self.content, mode='r') as zf:
            namelist = [n for n in zf.namelist() if not n.endswith('/')]
            if 'word/document.xml' in namelist:
                return self.FILE_DOCX
        return self.FILE_ZIP

    @staticmethod
    def check_mime(actual, expected):
        if hasattr(expected, 'match'):
            return expected.match(actual)
        # Simple match
        return actual == expected

    def get_type(self):
        if not self.content:
            return None
        self.content.file.seek(0)
        self.mime = magic.from_buffer(self.content.file.read(), mime=True)
        self.content.file.seek(0)
        for m, t in self.FILE_TYPES:
            if self.check_mime(self.mime, m):
                if t == self.FILE_ZIP:
                    return self.check_zipped_type()
                return t
        # Sometimes magic cannot detect the exact file type
        if self.mime == 'application/octet-stream':
            filename = self.filename.lower()
            if filename.endswith('.docx'):
                return self.FILE_DOCX
            if filename.endswith('.doc'):
                return self.FILE_DOC
            if filename.endswith('.pdf'):
                return self.FILE_PDF
        logger.warn(
            'File %s: unknown type - MIME %s' % (self.file_name, self.mime))
        return self.FILE_UNKNOWN

    def update_type(self):
        try:
            self.type = self.get_type()
        except Exception as e:
            logger.warn(
                "Can't determine file type for %s: %s" %
                (self.file_name, e)
            )
            self.type = self.FILE_UNKNOWN

    def clean_old_content(self):
        if not self.pk:
            return
        # Clean old file from storage
        f = File.objects.filter(pk=1).first()
        if f and f.content != self.content:
            f.content.delete(False)

    def save(self, *args, **kwargs):
        if not self.file_name:
            self.file_name = os.path.basename(self.content.name)

        if self.type is None:
            self.update_type()

        if self.type == self.FILE_ZIP:
            return

        self.clean_old_content()

        super(File, self).save()

        if self.need_ocr is None:
            self.need_ocr = bool(
                self.type == self.FILE_IMG or (
                    self.type == self.FILE_PDF and
                    requires_ocr(self.content)
                )
            )
            super(File, self).save()

    def img2pdf(self):
        if self.type != self.FILE_IMG:
            return
        name = os.path.basename(self.content.name)
        pdf_name = os.path.splitext(name)[0] + '.pdf'
        pdf_bytes = img2pdf.convert([self.content])
        self.content = SimpleUploadedFile(pdf_name, pdf_bytes, None)
        self.file_name = os.path.basename(pdf_name)
        self.save()

    def convert_pdf(self, path):
        return pdf_to_docx(path, self.need_ocr)

    def _store_converted(self, content):
        if not content:
            return
        name = os.path.splitext(os.path.basename(self.content.name))[0]
        file = ContentFile(content)
        file.name = name + '.docx'
        d = Document.objects.create(
            name=name,
            source_file=self,
            content_file=file
        )
        return d

    def get_converted_docx_content(self):
        data = None
        docxpath = None
        content = self.get_content_file()
        try:
            if self.type == self.FILE_PDF:
                docxpath = self.convert_pdf(content.name)
            elif self.type == self.FILE_DOC:
                docxpath = doc_to_docx(content.name)
            elif self.type == self.FILE_TXT:
                docxpath = txt_to_docx(content.name)
            elif self.type == self.FILE_DOCX:
                self.content.seek(0)
                data = self.content.read()
            elif self.type == self.FILE_HTML:
                docxpath = html_to_docx(content.name)
            elif self.type == self.FILE_XML:
                docxpath = xml_to_docx(content.name)
            if docxpath and os.path.exists(docxpath):
                data = open(docxpath, 'rb').read()
        finally:
            content.close()
        return data

    def convert(self):
        if self.type == self.FILE_UNKNOWN or self.type is None:
            self.update_type()
            self.save()
        data = self.get_converted_docx_content()
        return self._store_converted(data)

    class Meta:
        unique_together = (('file_name', 'batch'), )
        ordering = ['id']


class KeywordList(models.Model):
    name = models.CharField(max_length=200)
    batch = models.ForeignKey(
        Batch, related_name='keywordlists', null=True, blank=True,on_delete=models.DO_NOTHING,)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProjectArchive(models.Model):
    project = models.OneToOneField(Project, related_name='archive',on_delete=models.DO_NOTHING,)
    created_at = models.DateTimeField(auto_now_add=True)
    content_file = models.FileField(upload_to='project_archives/', null=True)

    def __str__(self):
        return '{0.project.name} archive ({0.created_at})'.format(self)


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    """
    Create Profile on User create or update Profile on User update
    """

    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


@receiver(post_save, sender=Profile)
def update_personal_data(sender, instance, created, **kw):
    """
    Update `selected` field of PersonalData on personal_data_types change
    """
    if created:
        return

    prev = instance.prev_personal_data_types
    cur = instance.personal_data_types
    if prev != cur:
        for type in cur:
            if cur[type][0] != prev[type][0]:
                for pd in PersonalData.objects.filter(user=instance.user, type=type):
                    pd.selected = cur[type][0]
                    pd.save()
                for cpd in CustomPersonalData.objects.filter(user=instance.user, type=type):
                    cpd.selected = cur[type][0]
                    cpd.save()

        instance.prev_personal_data_types = cur
        instance.save()
