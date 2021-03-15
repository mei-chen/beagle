from __future__ import unicode_literals

import random
import re
import string

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from model_utils.models import TimeStampedModel

from portal.models import Project, Batch


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
                                 null=True, blank=True,on_delete=models.DO_NOTHING,)

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

    def __str__(self):
        return self.value


# Abstract invites


class CollaborationInvite(TimeStampedModel):
    """
    Abstract base class for all types of collaboration invites.

    Must include at least 3 foreign key fields: invitee (User), inviter (User),
    and some target object (arbitrary model).
    """

    class Meta:
        abstract = True

    @property
    def target(self):
        raise NotImplementedError

    def __str__(self):
        return u"From: '%s', To: '%s', On: '%s'" % (
            self.inviter, self.invitee, self.target
        )


# Concrete invites


class ProjectCollaborationInvite(CollaborationInvite):

    invitee = models.ForeignKey(User, related_name='project_collaboration_invites_received',on_delete=models.DO_NOTHING,)
    inviter = models.ForeignKey(User, related_name='project_collaboration_invites_sent',on_delete=models.DO_NOTHING,)

    project = models.ForeignKey(Project, related_name='collaboration_invites',on_delete=models.DO_NOTHING,)

    @property
    def target(self):
        return self.project


class BatchCollaborationInvite(CollaborationInvite):

    invitee = models.ForeignKey(User, related_name='batch_collaboration_invites_received',on_delete=models.DO_NOTHING,)
    inviter = models.ForeignKey(User, related_name='batch_collaboration_invites_sent',on_delete=models.DO_NOTHING,)

    batch = models.ForeignKey(Batch, related_name='collaboration_invites',on_delete=models.DO_NOTHING,)

    @property
    def target(self):
        return self.batch
