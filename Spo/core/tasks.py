from celery import shared_task
from celery.utils.log import get_task_logger

from core.models import (
    DatasetCollaborationInvite,
    DatasetExternalInvite,
    ExperimentCollaborationInvite,
    ExperimentExternalInvite,
)
from portal.mailer import SpotMailer

logger = get_task_logger(__name__)


@shared_task
def send_dataset_collaboration_invite_email(invite_pk, domain):
    try:
        invite = DatasetCollaborationInvite.objects.get(pk=invite_pk)
    except DatasetCollaborationInvite.DoesNotExist:
        return False

    logger.info('Sending dataset collaboration invite email to: %s',
                invite.invitee)

    success = SpotMailer.send_dataset_collaboration_invite(invite, domain)

    if not success:
        logger.error('Could not send dataset collaboration invite email to: %s',
                     invite.invitee)

    return success


@shared_task
def send_dataset_external_invite_email(invite_pk, domain):
    try:
        invite = DatasetExternalInvite.objects.get(pk=invite_pk)
    except DatasetExternalInvite.DoesNotExist:
        return False

    logger.info('Sending dataset external invite email to: %s', invite.email)

    success = SpotMailer.send_dataset_external_invite(invite, domain)

    if not success:
        logger.error('Could not send dataset external invite email to: %s',
                     invite.email)

    return success


@shared_task
def send_experiment_collaboration_invite_email(invite_pk, domain):
    try:
        invite = ExperimentCollaborationInvite.objects.get(pk=invite_pk)
    except ExperimentCollaborationInvite.DoesNotExist:
        return False

    logger.info('Sending experiment collaboration invite email to: %s',
                invite.invitee)

    success = SpotMailer.send_experiment_collaboration_invite(invite, domain)

    if not success:
        logger.error('Could not send experiment collaboration invite email to: %s',
                     invite.invitee)

    return success


@shared_task
def send_experiment_external_invite_email(invite_pk, domain):
    try:
        invite = ExperimentExternalInvite.objects.get(pk=invite_pk)
    except ExperimentExternalInvite.DoesNotExist:
        return False

    logger.info('Sending experiment external invite email to: %s', invite.email)

    success = SpotMailer.send_experiment_external_invite(invite, domain)

    if not success:
        logger.error('Could not send experiment external invite email to: %s',
                     invite.email)

    return success
