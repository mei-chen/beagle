import os

from django.contrib.auth.models import User
from django.db import models
import jsonfield
from model_utils.models import TimeStampedModel

from core.models import Document


class CloudTypes:
    DROPBOX = 'dropbox'
    GOOGLE_DRIVE = 'google_drive'

    HUMAN_READABLE = {
        DROPBOX: 'Dropbox',
        GOOGLE_DRIVE: 'Google Drive',
    }


class Folder(TimeStampedModel):
    folder_id = models.CharField(max_length=100, null=False, db_index=True)

    # Only for dropbox
    folder_path = models.CharField(max_length=300, null=True, blank=True)

    title = models.CharField(max_length=120, null=False)

    user = models.ForeignKey(User)

    cloud = models.CharField(max_length=64,
                             choices=CloudTypes.HUMAN_READABLE.items())

    @property
    def human_readable_cloud(self):
        return CloudTypes.HUMAN_READABLE[self.cloud]

    def __unicode__(self):
        return u'[{}] ({}) {}'.format(
            self.user, self.human_readable_cloud, self.title
        )

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'cloud': self.cloud,
        }


class CloudAccess(TimeStampedModel):
    user = models.OneToOneField(User)

    def __unicode__(self):
        return unicode(self.user)

    class Meta:
        abstract = True


class DropboxAccess(CloudAccess):
    token = models.CharField(max_length=150)

    class Meta:
        verbose_name_plural = 'Dropbox Tokens'


class GoogleDriveAccess(CloudAccess):
    credentials = jsonfield.JSONField()

    class Meta:
        verbose_name_plural = 'Google Drive Credentials'


class Synchronized(TimeStampedModel):
    cloud_id = models.CharField(max_length=200, null=False, db_index=True)

    folder = models.ForeignKey(Folder)

    original_name = models.CharField(max_length=200, null=False)

    document = models.OneToOneField(Document, null=True)

    def __unicode__(self):
        return os.path.join(unicode(self.folder), self.original_name)


class Queue(TimeStampedModel):
    cloud_id = models.CharField(max_length=200, null=False, db_index=True)

    # Only for dropbox
    cloud_path = models.CharField(max_length=300, null=True, blank=True)

    folder = models.ForeignKey(Folder)

    title = models.CharField(max_length=200, null=False)

    def __unicode__(self):
        return os.path.join(unicode(self.folder), self.title)
