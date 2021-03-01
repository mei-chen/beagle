from __future__ import unicode_literals

import random
import re
import string

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.dispatch import receiver
from model_utils.models import TimeStampedModel

from dataset.models import Dataset
from experiment.models import Experiment


MIN_TOKEN_VALUE_LENGTH = 50
MAX_TOKEN_VALUE_LENGTH = 100


TOKEN_VALUE_VALIDATOR = RegexValidator(
    regex=re.compile(r'^[a-zA-Z0-9]{%d,%d}$' %
                     (MIN_TOKEN_VALUE_LENGTH, MAX_TOKEN_VALUE_LENGTH)),
    message='A token value must be an alphanumeric string of a size between '
            '%d and %d characters long.' %
            (MIN_TOKEN_VALUE_LENGTH, MAX_TOKEN_VALUE_LENGTH)
)


ALPHANUMERIC_CHARSET = (
    string.ascii_lowercase + string.ascii_uppercase + string.digits
)


def generate_random_token():
    """ Generates random valid values for access tokens. """
    length = random.randint(MIN_TOKEN_VALUE_LENGTH, MAX_TOKEN_VALUE_LENGTH)
    return ''.join(random.choice(ALPHANUMERIC_CHARSET) for _ in range(length))


class AccessToken(models.Model):

    # Actual user (if token is personal) or None (if token is global)
    owner = models.OneToOneField(User, related_name='access_token',
                                 null=True, blank=True)

    # Actual token value (will be generated automatically, if is omitted)
    value = models.CharField('Value', max_length=MAX_TOKEN_VALUE_LENGTH,
                             default=generate_random_token,
                             unique=True, validators=[TOKEN_VALUE_VALIDATOR])

    def save(self, *args, **kwargs):
        # Validate value before making actual query to db
        # (by default validation is performed only when working via forms)
        TOKEN_VALUE_VALIDATOR(self.value)
        # If no ValidationError was raised, then try to save token to db
        super(AccessToken, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.value


# Abstract invites


class CollaborationInvite(TimeStampedModel):

    class Meta:
        abstract = True
        ordering = ['-created']


class ExternalInvite(TimeStampedModel):

    email = models.EmailField()

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        return super(ExternalInvite, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ['-created']


# Concrete invites


class DatasetCollaborationInvite(CollaborationInvite):

    invitee = models.ForeignKey(User, related_name='dataset_collaboration_invites_received')
    inviter = models.ForeignKey(User, related_name='dataset_collaboration_invites_sent')
    dataset = models.ForeignKey(Dataset, related_name='collaboration_invites')

    def __unicode__(self):
        return u"From: '%s', To: '%s', On: '%s'" % (
            self.inviter, self.invitee, self.dataset
        )


class DatasetExternalInvite(ExternalInvite):

    inviter = models.ForeignKey(User, related_name='dataset_external_invites_sent')
    dataset = models.ForeignKey(Dataset, related_name='external_invites')

    def transform_to_collaboration_invite(self, user):
        collaboration_invite = DatasetCollaborationInvite.objects.create(
            inviter=self.inviter, invitee=user, dataset=self.dataset
        )
        self.delete()
        return collaboration_invite

    def __unicode__(self):
        return u"From: '%s', To: '%s', On: '%s'" % (
            self.inviter, self.email, self.dataset
        )


class ExperimentCollaborationInvite(CollaborationInvite):

    invitee = models.ForeignKey(User, related_name='experiment_collaboration_invites_received')
    inviter = models.ForeignKey(User, related_name='experiment_collaboration_invites_sent')
    experiment = models.ForeignKey(Experiment, related_name='collaboration_invites')

    def __unicode__(self):
        return u"From: '%s', To: '%s', On: '%s'" % (
            self.inviter, self.invitee, self.experiment
        )


class ExperimentExternalInvite(ExternalInvite):

    inviter = models.ForeignKey(User, related_name='experiment_external_invites_sent')
    experiment = models.ForeignKey(Experiment, related_name='external_invites')

    def transform_to_collaboration_invite(self, user):
        collaboration_invite = ExperimentCollaborationInvite.objects.create(
            inviter=self.inviter, invitee=user, experiment=self.experiment
        )
        self.delete()
        return collaboration_invite

    def __unicode__(self):
        return u"From: '%s', To: '%s', On: '%s'" % (
            self.inviter, self.email, self.experiment
        )


@receiver(models.signals.pre_save, sender=User)
def convert_credentials_to_proper_case(sender, instance, **kwargs):
    instance.username = instance.username.lower()
    instance.first_name = instance.first_name.capitalize()
    instance.last_name = instance.last_name.capitalize()
    instance.email = instance.email.lower()


@receiver(models.signals.post_save, sender=User)
def transform_external_invites_to_collaboration_invites(sender, instance,
                                                        created, **kwargs):
    if created:
        for dataset_external_invite in \
                DatasetExternalInvite.objects.filter(email=instance.email):
            dataset_external_invite.transform_to_collaboration_invite(instance)
        for experiment_external_invite in \
                ExperimentExternalInvite.objects.filter(email=instance.email):
            experiment_external_invite.transform_to_collaboration_invite(instance)
