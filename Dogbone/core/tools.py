import os
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils import timezone

from marketing.models import PurchasedSubscription
from dogbone.app_settings.marketing_settings import TrialSubscription


def init_sample_docs():
    samples = [f for f in os.listdir(settings.SAMPLE_DOCS_DIR)
                 if not f.startswith('.') and not f.startswith('-') and
                    os.path.isfile(os.path.join(settings.SAMPLE_DOCS_DIR, f))]
    return samples


def user_collaborators(user):
    """ Get all the collaborators of a certain user """

    # This import is put inside a function for script
    # scripts/gather_document_data_from_bd.py to work.
    from django.db.models import Q
    from .models import CollaborationInvite

    collaborations = CollaborationInvite.objects.filter(
        Q(inviter=user) | Q(invitee=user)
    ).select_related('inviter', 'invitee')

    known_collaborators = set(
        [c.invitee for c in collaborations] +
        [c.inviter for c in collaborations]
    ).difference([user])

    return known_collaborators


def smart_dict(instance):
    """
    Automatic decide how to serialize models
    :param instance: a `django.Model` instance
    :return: `dict`
    """
    if instance is None:
        return None

    if instance.__class__.__name__ == 'User':
        return user_to_dict(instance)
    elif instance.__class__.__name__ == 'Document':
        return {
            'created': str(instance.created),
            'original_name': instance.original_name,
            'owner': user_to_dict(instance.owner),
            'title': instance.title,
            'uuid': instance.uuid,
        }
    elif instance.__class__.__name__ == 'CollaborationInvite':
        return {
            'inviter': user_to_dict(instance.inviter),
            'invitee': user_to_dict(instance.invitee),
            'external': False,
            'document': smart_dict(instance.document),
        }
    else:
        try:
            return instance.to_dict()
        except:
            pass

        try:
            return {'id': instance.pk}
        except:
            pass

    return {}


def user_is_paid(user):
    return user.is_superuser or PurchasedSubscription.has_active_subscription(user)


def user_had_trial(user):
    return any([ps for ps in PurchasedSubscription.objects.filter(buyer=user, start__lte=timezone.now())
                if TrialSubscription.includes(ps.get_subscription())])


def user_to_dict(user):
    """
    Returns a dictionary of information for the provided user
    :param user:
    """

    cache_key = 'user:dict:%d' % user.id

    data = cache.get(cache_key)

    if data is None:
        data = {
            'email': user.email,
            'username': user.username,
            'id': user.id,
            'last_login': str(user.last_login),
            'date_joined': str(user.date_joined),
            'first_name': user.first_name or None,
            'last_name': user.last_name or None,
            'job_title': user.details.job_title or None,
            'avatar': user.details.get_avatar(),
            'company': user.details.company or None,
            'is_paid': user_is_paid(user),
            'had_trial': user_had_trial(user),
            'is_super': user.is_superuser,
            'pending': False,
            'tags': user.details.tags,
            'keywords': user.details.keywords,
            'settings': user.details.settings or {},
            'document_upload_count': user.details.get_document_upload_count(),
            'phone': user.details.phone or None,
        }

        cache.set(cache_key, data, timeout=15)

    return data


def invalidate_user_cache(user):
    cache.delete('user:dict:%d' % user.id)
    cache.delete('user:projects:%d' % user.id)


def notification_to_dict(notification):
    """
    Returns a dictionary for a Notification model from `notifications.models`
    :param notification:
    :return:
    """

    serialized = {
        'id': notification.pk,
        'read': not notification.unread,
        'level': notification.level,
        'actor_type': notification.actor_content_type.model
                        if notification.actor_content_type else None,
        'target_type': notification.target_content_type.model
                        if notification.target_content_type else None,
        'action_object_type': notification.action_object_content_type.model
                        if notification.action_object_content_type else None,
        'verb': notification.verb,
        'description': notification.description,
        'timestamp': str(notification.timestamp),
        'data': notification.data,
    }

    for field_name in ['actor', 'target', 'action_object']:
        field_value = getattr(notification, field_name, None)
        serialized[field_name] = smart_dict(field_value)

    try:
        render_string = notification.data['render_string']
        suggested_display = render_notification(notification)
    except (AttributeError, KeyError, TypeError):
        render_string = None
        suggested_display = None

    serialized.update({'render_string': render_string,
                       'suggested_display': suggested_display})

    return serialized


def render_notification(notification):
    """
    Helper function for rendering the notification
    - Try first to find the `render_string` field in the notification.
    If found, use that
    - Try to use the verb to tie stuff together

    :param notification: notifications.models.Notification
    :return: a string
    """

    # Check if we have `render_string` field inside `data`
    try:
        render_string = notification.data.get('render_string', None)
    except AttributeError:
        render_string = None

    if render_string is None:
        if notification.action_object is None and notification.target is None:
            render_string = "(actor) (verb)"
        elif notification.action_object is None:
            render_string = "(actor) (verb) (target)"
        else:
            render_string = "(actor) (verb) (target) on (action_object)"

    if render_string is not None:
        if notification.actor == notification.recipient:
            render_string = render_string.replace('(actor)', 'You')
        else:
            render_string = render_string.replace('(actor)', unicode(notification.actor))

        if notification.target == notification.recipient:
            render_string = render_string.replace('(target)', 'You')
        else:
            render_string = render_string.replace('(target)', unicode(notification.target))

        render_string = render_string.replace('(action_object)', unicode(notification.action_object))
        render_string = render_string.replace('(verb)', notification.verb)
        return render_string

    return None


def _disconnect_signal(signal, receiver, sender):
    """
    Used to temporary disconnect a signal
    :param signal: signal class
    :param receiver: receiver function
    :param sender: Django Model class
    :return:
    """
    disconnect = getattr(signal, 'disconnect')
    disconnect(receiver, sender)


def _reconnect_signal(signal, receiver, sender):
    """
    Used to reconnect a temporary disconnected signal
    :param signal: signal class
    :param receiver: receiver function
    :param sender: Django Model class
    :return:
    """
    connect = getattr(signal, 'connect')
    connect(receiver, sender=sender)


class disconnect_signal:
    def __init__(self, signal, receiver, sender):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender

    def __enter__(self):
        _disconnect_signal(
            signal=self.signal,
            receiver=self.receiver,
            sender=self.sender
        )

    def __exit__(self, type, value, traceback):
        _reconnect_signal(
            signal=self.signal,
            receiver=self.receiver,
            sender=self.sender
        )


# This list is used to asses which component of a Notification will be bound to the URL
# Example 1:
# Alex(User) invited You(User) to collaborate on Document "Dropbox TOS"
# The URL should point to a document related view, not a user one
#
# Example 2:
# Alex commented on a sentence in "Dropbox TOS"
# The URL should point to a sentence related view, not a User one, not a document one
OBJECT_PARTICULARITY_HIERARCHY = (
    'User',
    'Document',
    'Sentence',
)


def focus_object(notification):
    best_particularity, best_object, best_component = -1, None, None

    # Compute the particularity of actor
    if notification.actor:
        try:
            actor_particularity = OBJECT_PARTICULARITY_HIERARCHY.index(notification.actor.__class__.__name__)
            if actor_particularity is not None and actor_particularity >= best_particularity:
                best_object = notification.actor
                best_particularity = actor_particularity
                best_component = 'actor'
        except ValueError:
            pass

    # Compute the particularity of target
    if notification.target:
        try:
            target_particularity = OBJECT_PARTICULARITY_HIERARCHY.index(notification.target.__class__.__name__)
            if target_particularity is not None and target_particularity >= best_particularity:
                best_object = notification.target
                best_particularity = target_particularity
                best_component = 'target'
        except ValueError:
            pass

    # Compute the particularity of action_object
    if notification.action_object:
        try:
            action_object_particularity = OBJECT_PARTICULARITY_HIERARCHY.index(notification.action_object.__class__.__name__)
            if action_object_particularity is not None and action_object_particularity >= best_particularity:
                best_object = notification.action_object
                best_particularity = action_object_particularity
                best_component = 'action_object'
        except ValueError:
            pass

    return best_object, best_component


def batch_url(batch):
    """
    Shortcut for getting the batch URL
    """
    return reverse('summary', kwargs={'id': batch.id})


def document_url(document):
    """
    Shortcut for getting the document URL
    """
    return reverse('report', kwargs={'uuid': document.uuid})


def sentence_url(sentence, sentence_index):
    """
    Shortcut for getting the sentence URL
    """
    return reverse('report', kwargs={'uuid': sentence.doc.uuid}) + '#/context-view?idx=%s' % sentence_index


def notification_url(notification):
    """
    A Heuristic approach to creating Notifications ULRs.

    Note: Notification URLs have a Frontend Routing component

    Reasons for which we chose a heuristic approach
    1) The URL could have been created and persisted when the Notification was created.
    Unfortunately, in case the frontend changes, so does the URL, so the persisted URLs will be invalid

    2) The logic of creating the URL is pretty complex, and we don't want the client to build this URL.
    We might at one point though, when we'll have different clients that have different URL schemes (Like mobile apps)

    :param notification: A notifications.models.Notification object
    :return: a complete backend/frontend URL
    Example: /report/1111-2222-3333-4444#/detail-view/sentence/5555
    """

    obj, component = focus_object(notification)
    if obj is None:
        return None

    object_type = obj.__class__.__name__

    if object_type == 'Document':
        return document_url(obj)

    if object_type == 'Sentence':
        sentence_index = None

        # Try to find the Sentence inside the notification in the document's sentence list
        try:
            sentence_index = obj.doc.sentences_pks.index(obj.pk)
        except ValueError:
            logging.warning('notification_url: original notification sentence index could not be found.')

        # If the sentence could not be found, try finding the latest revision
        if sentence_index is None:
            latest_sentence = obj.latest_revision

            try:
                sentence_index = latest_sentence.doc.sentences_pks.index(latest_sentence.pk)

                # Update the sentence on the notification, so that we don't have to recompute it
                setattr(notification, component, latest_sentence)
                notification.save()
            except ValueError:
                logging.error('notification_url: latest notification sentence index could not be found.')

        if sentence_index is None:
            logging.warning('Could not resolute a notification URL')
            return None

        return sentence_url(obj, sentence_index)

    return None


def kick_my_other_sessions(sender, request, user, **kwargs):
    """ Removes user sessions to only have one at a moment. """

    try:
        current_session_key = request.session.session_key
        user.session_set.exclude(session_key=current_session_key).delete()
    except:
        pass


def kick_all_my_sessions(sender, request, user, **kwargs):
    """ Removes all user sessions. """

    try:
        user.session_set.all().delete()
    except:
        pass


def user_is_logged_in(user):
    """
    Checks whether the user has any valid (i.e. not expired yet) sessions.

    Note that the `is_authenticated` method/property always returns True for
    existing users, so is useless outside of views and cannot be used here.
    """

    return user.session_set.filter(expire_date__gt=timezone.now()).exists()


def login_resource_url(user, resource_url):
    """
    If the user is not logged in yet, adds a login hash
    to the base URL in order to access the resource immediately.
    """

    from urllib import urlencode

    from authentication.models import OneTimeLoginHash

    if not user_is_logged_in(user):
        login_hash = OneTimeLoginHash.create(user)
        resource_url = '%s?%s' % (
            reverse('login'), urlencode({
                'hash': login_hash.get_hash(), 'next': resource_url
            })
        )

    return resource_url
