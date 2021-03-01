from __future__ import unicode_literals

import os

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import jsonfield
from model_utils.models import TimeStampedModel

from portal.models import Batch, File


class CloudAccess(models.Model):
    user = models.OneToOneField(User,on_delete=models.DO_NOTHING,)

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


class CloudTypes:
    DROPBOX = 'dropbox'
    GOOGLE_DRIVE = 'google_drive'

    HUMAN_READABLE = {
        DROPBOX: 'Dropbox',
        GOOGLE_DRIVE: 'Google Drive',
    }


class CloudFolder(TimeStampedModel):
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING,)
    batch = models.OneToOneField(Batch, null=True, blank=True,on_delete=models.DO_NOTHING,)

    cloud = models.CharField(
        max_length=50, choices=CloudTypes.HUMAN_READABLE.items()
    )

    folder_id = models.CharField(max_length=100, unique=True)
    folder_path = models.CharField(max_length=300)

    @property
    def human_readable_cloud(self):
        return CloudTypes.HUMAN_READABLE[self.cloud]

    def __unicode__(self):
        return u'[%s] (%s) %s' % (
            self.user, self.human_readable_cloud, self.folder_path
        )

    class Meta:
        verbose_name_plural = 'Folders'


class CloudFile(TimeStampedModel):
    folder = models.ForeignKey(CloudFolder, related_name='files',on_delete=models.DO_NOTHING,)
    file_object = models.OneToOneField(File, null=True, blank=True,on_delete=models.DO_NOTHING,)

    file_id = models.CharField(max_length=100, unique=True)
    file_name = models.CharField(max_length=100)

    @property
    def file_path(self):
        return os.path.join(self.folder.folder_path, self.file_name)

    def __unicode__(self):
        return os.path.join(unicode(self.folder), self.file_name)

    class Meta:
        verbose_name_plural = 'Files'


@receiver(post_save, sender=CloudFolder)
def create_batch_for_cloud_folder(sender, instance, created, **kwargs):
    """ Creates some corresponding Batch for each newly created CloudFolder. """

    if created:
        batch_name = '[{cloud}] {name}'.format(
            cloud=instance.human_readable_cloud,
            name=instance.folder_path
        )
        batch = Batch.objects.create(
            name=batch_name,
            owner=instance.user
        )
        instance.batch = batch
        instance.save()
