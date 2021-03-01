from django.contrib.auth.models import User

from core.models import ProjectCollaborationInvite, BatchCollaborationInvite


def user_to_dict(user):
    """ Serializes the given user into a dict. """

    return {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }


def send_project_invite(email, inviter, project):
    """
    Tries to send an appropriate email to the invitee.
    Returns a pair of the format: (status: bool, message: str).
    """

    email = email.lower()

    invitee = User.objects.filter(email=email).last()

    if invitee:
        if invitee == inviter:
            return False, 'One cannot invite himself/herself.'

        # A collaboration invite is uniquely defined by (invitee, project)
        collaboration_invite, created = \
            ProjectCollaborationInvite.objects.get_or_create(
                invitee=invitee, project=project,
                defaults={'inviter': inviter}
            )

        if created:
            # TODO: implement actual email sending
            pass
        else:
            return False, 'Collaboration invite already exists.'

    else:
        # TODO: implement external invites
        pass

    return True, 'OK'


def revoke_project_invite(username, project):
    """ Tries to delete the corresponding collaboration invites. """

    ProjectCollaborationInvite.objects.filter(
        invitee__username=username, project=project
    ).delete()


def send_batch_invite(email, inviter, batch):
    """
    Tries to send an appropriate email to the invitee.
    Returns a pair of the format: (status: bool, message: str).
    """

    email = email.lower()

    invitee = User.objects.filter(email=email).last()

    if invitee:
        if invitee == inviter:
            return False, 'One cannot invite himself/herself.'

        # A collaboration invite is uniquely defined by (invitee, batch)
        collaboration_invite, created = \
            BatchCollaborationInvite.objects.get_or_create(
                invitee=invitee, batch=batch,
                defaults={'inviter': inviter}
            )

        if created:
            # TODO: implement actual email sending
            pass
        else:
            return False, 'Collaboration invite already exists.'

    else:
        # TODO: implement external invites
        pass

    return True, 'OK'


def revoke_batch_invite(username, batch):
    """ Tries to delete the corresponding collaboration invites. """

    BatchCollaborationInvite.objects.filter(
        invitee__username=username, batch=batch
    ).delete()
