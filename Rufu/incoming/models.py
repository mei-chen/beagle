from __future__ import unicode_literals
import time
import syslog

# Django
from django.db import models
from django.core.files.storage import default_storage as s3_storage
from django.core.files.base import ContentFile

# Create your models here.

def raw_upload_to(instance, email):
    """
    Stores the sent email content to S3 under <user>@<domain>.com/raw/<timestamp>.txt as sometimes
    the filename is not parsed correctly
    """
    return '%s/raw/%s.txt' % (email, int(time.time()))

class User(models.Model):
    name = models.CharField(
        max_length=300,
        null=True,
        blank=True
    )

    email = models.CharField(
        max_length=300,
        null=True,
        blank=True
    )

    domain = models.CharField(
        max_length=300,
        null=True,
        blank=True
    )

    success = models.NullBooleanField(
        null=True,
        blank=True
    )

    response = models.TextField(
        null=True
    )

    email_raw = models.FileField(
        null=True,
        blank=True,
        storage=s3_storage,
        upload_to=raw_upload_to
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __unicode__(self):
        return self.name

    @classmethod
    def create_user(cls, name, email, domain):
        try:
            return cls.objects.create(name=name, email=email, domain=domain)
        except Exception as e:
            print "create_user: %s" % e
            syslog.syslog("create_user: %s" % e)

    def save_email_content(self, content):
        try:  # As this is not critical, incase of a failure need to send message to logging instead
            file_content = ContentFile(content)
            self.email_raw.save(self.email, file_content)
            self.save()
        except Exception as e:
            print "save_email_content: %s \ncontent: %s" % (e, content)
            syslog.syslog("save_email_content: %s \ncontent: %s" % (e, content))


def attachment_upload_to(instance, filename):
    """
    Stores the sent email content to S3 under <user>@<domain>.com/attachments/<timestamp>-<filename>
    """
    return '%s/attachments/%s-%s' % (instance.user.email, int(time.time()), filename)


class Attachment(models.Model):
    user = models.ForeignKey(
        User
    )

    document = models.CharField(
        max_length=300,
        null=True,
        blank=True
    )

    attachment = models.FileField(
        null=True,
        storage=s3_storage,
        upload_to=attachment_upload_to
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    @classmethod
    def create_attachments(cls, user, attachments):
        for key, value in attachments.items():
            try:
                obj = cls.objects.create(user=user, document=key)
                obj.attachment.save(key, value)
                obj.save()
            except Exception as e:
                print "create_attachments: %s \nattachment: %s" % (e, ContentFile(value.read()))
                syslog.syslog("create_attachments: %s \nattachment: %s" % (e, ContentFile(value.read())))

