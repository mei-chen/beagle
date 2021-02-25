from django.contrib.auth.models import User

from core.models import (
    DatasetCollaborationInvite,
    DatasetExternalInvite,
    ExperimentCollaborationInvite,
    ExperimentExternalInvite,
)
from core.tasks import (
    send_dataset_collaboration_invite_email,
    send_dataset_external_invite_email,
    send_experiment_collaboration_invite_email,
    send_experiment_external_invite_email,
)


def user_to_dict(user):
    """ Serializes the given user into a dict. """

    return {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
    }


def send_dataset_invite(email, inviter, dataset, domain):
    """
    Tries to send an appropriate email to the invitee.
    Returns a pair of the format: (status: bool, message: str).
    """

    email = email.lower()

    invitee = User.objects.filter(email=email).last()

    if invitee:
        if invitee == inviter:
            return False, 'One cannot invite himself/herself.'

        # A collaboration invite is uniquely defined by (invitee, dataset)
        collaboration_invite, created = \
            DatasetCollaborationInvite.objects.get_or_create(
                invitee=invitee, dataset=dataset,
                defaults={'inviter': inviter}
            )
        if created:
            send_dataset_collaboration_invite_email.delay(
                collaboration_invite.pk, domain
            )
        else:
            return False, 'Collaboration invite already exists.'

    else:
        # An external invite is uniquely defined by (email, dataset)
        external_invite, created = \
            DatasetExternalInvite.objects.get_or_create(
                email=email, dataset=dataset,
                defaults={'inviter': inviter}
            )
        if created:
            send_dataset_external_invite_email.delay(
                external_invite.pk, domain
            )
        else:
            return False, 'External invite already exists.'

    return True, 'OK'


def revoke_dataset_invite(username, dataset):
    """ Tries to delete the corresponding collaboration invites. """

    DatasetCollaborationInvite.objects.filter(
        invitee__username=username, dataset=dataset
    ).delete()


def send_experiment_invite(email, inviter, experiment, domain):
    """
    Tries to send an appropriate email to the invitee.
    Returns a pair of the format: (status: bool, message: str).
    """

    email = email.lower()

    invitee = User.objects.filter(email=email).last()

    if invitee:
        if invitee == inviter:
            return False, 'One cannot invite himself/herself.'

        # A collaboration invite is uniquely defined by (invitee, experiment)
        collaboration_invite, created = \
            ExperimentCollaborationInvite.objects.get_or_create(
                invitee=invitee, experiment=experiment,
                defaults={'inviter': inviter}
            )
        if created:
            send_experiment_collaboration_invite_email.delay(
                collaboration_invite.pk, domain
            )
        else:
            return False, 'Collaboration invite already exists.'

    else:
        # An external invite is uniquely defined by (email, experiment)
        external_invite, created = \
            ExperimentExternalInvite.objects.get_or_create(
                email=email, experiment=experiment,
                defaults={'inviter': inviter}
            )
        if created:
            send_experiment_external_invite_email.delay(
                external_invite.pk, domain
            )
        else:
            return False, 'External invite already exists.'

    return True, 'OK'


def revoke_experiment_invite(username, experiment):
    """ Tries to delete the corresponding collaboration invites. """

    ExperimentCollaborationInvite.objects.filter(
        invitee__username=username, experiment=experiment
    ).delete()
