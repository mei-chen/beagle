import json
import logging
from itertools import chain

from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse
from itsdangerous import URLSafeSerializer

from beagle_simpleapi.endpoint import ListView
from beagle_simpleapi.mixin import PostListModelMixin
from beagle_realtime.notifications import NotificationManager
from core.models import CollaborationInvite, Document, ExternalInvite, Sentence, CollaboratorList
from core.tasks import send_external_invite, send_collaboration_invite
from core.signals import collaboration_invite_pre_delete
from portal.tools import add_salt
from dogbone.actions import has_permission


class CurrentUserReceivedInvitationsListView(ListView):
    model = CollaborationInvite
    url_pattern = r'/user/me/received_invitations$'
    endpoint_name = 'me_received_invitations_list_view'

    _cached_object_count = None

    DEFAULT_RESULTS_PER_PAGE = 4

    def get_page_count(self):
        """ Determine total number of pages in this result, given the RPP. """
        rpp = self.get_rpp()
        object_count = self.get_object_count()
        return self._compute_page_count(object_count, rpp)

    def get_object_count(self):
        """
        Determine total number of objects in this list view.
        Returns a cached object count, no queries are made.
        """
        return self._cached_object_count

    def meta(self):
        return {'pagination': self.pagination(),
                'search': self.search()}

    def search(self):
        return {'query': self.request.GET.get('q')}

    def wrap_result(self, result):
        return {'objects': result,
                'meta': self.meta()}

    def get_queryset(self, request):
        filtering_options = {'invitee': self.user}
        if 'q' in request.GET:
            filtering_options['document__title__icontains'] = request.GET['q']
        queryset = self.model.objects.filter(**filtering_options)
        self._cached_object_count = queryset.count()
        return queryset.order_by('-created')


class CurrentUserIssuedInvitationsListView(ListView, PostListModelMixin):
    model = CollaborationInvite
    url_pattern = r'/user/me/issued_invitations$'
    endpoint_name = 'me_issued_invitations_list_view'

    def get_list(self, request, *args, **kwargs):
        return CollaborationInvite.objects.filter(inviter=self.user)[self.get_slice()]

    def save_model(self, item, request, *args, **kwargs):
        """
        Save the model, required for PostModelMixin
        """
        d = Document.objects.get(uuid=item['document'])
        if not d or not d.has_access(self.user):
            return None

        new_instance = self.model()
        new_instance.inviter = self.user
        new_instance.invitee = User.objects.get(email__iexact=item['invitee'])
        new_instance.document = d
        new_instance.save()

        return new_instance


class DocumentReceivedInvitationsListView(ListView):
    model = CollaborationInvite
    url_pattern = r'/document/(?P<uuid>[a-z0-9\-]+)/received_invitations$'
    endpoint_name = 'document_received_invitations_list_view'

    def get_document(self, request, *args, **kwargs):
        try:
            document = Document.ready_objects.get(trash=False, uuid=kwargs['uuid'])
            if not document.has_access(self.user):
                return None
            return document
        except Document.DoesNotExist:
            return None

    def get_list(self, request, *args, **kwargs):
        document = self.get_document(request, *args, **kwargs)
        if not document:
            raise self.NotFoundException("Document not found")

        return self.model.objects.filter(invitee=self.user, document=document)

    def delete(self, request, *args, **kwargs):
        document = self.get_document(request, *args, **kwargs)
        if not document:
            raise self.NotFoundException("Document not found")

        allow, _ = has_permission(request, 'delete_invite', document=document)
        if not allow:
            logging.warning('%s tried to delete invites without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to delete invites with your subscription")

        payload = []

        invites = self.model.objects.filter(invitee=self.user, document=document)

        for invite in invites:
            collaboration_invite_pre_delete.send(
                sender=self.model,
                request_user=self.user,
                instance=invite
            )

            invitee = invite.invitee
            invite.delete()

            NotificationManager.create_document_message(
                document,
                event_name='message',
                message={
                    'notif': NotificationManager.ServerNotifications.DOCUMENT_INVITE_RECEIVED_REJECTED_NOTIFICATION,
                    'invitee': {
                        'id': invitee.id,
                        'username': invitee.username,
                        'email': invitee.email
                    },
                    'document': document.to_dict(include_analysis=False)
                }
            ).send()

            payload.append(invite.to_dict())

        return payload


class DocumentIssuedInvitationsListView(ListView, PostListModelMixin):
    model = CollaborationInvite
    url_pattern = r'/document/(?P<uuid>[a-z0-9\-]+)/issued_invitations$'
    endpoint_name = 'document_issued_invitations_list_view'

    def get_document(self, request, *args, **kwargs):
        try:
            document = Document.ready_objects.get(trash=False, uuid=kwargs['uuid'])
            if not document.has_access(self.user):
                return None
            return document
        except Document.DoesNotExist:
            logging.warning('DocumentIssuedInvitationsListView.get_document - Document does not exist')
            return None

    def get_sentence(self, document, data, request, *args, **kwargs):
        """
        Get the sentence a user is invited to
        :param document: The document the user is invited to
        :param request:
        :param args:
        :param kwargs:
        :return: The sentence object
        """
        try:
            sentence_index = int(data['sentenceIdx'])
            sentence_id = document.sentences_ids[sentence_index]
            sentence = Sentence.objects.get(pk=sentence_id)
            sentence = sentence.latest_revision
            return sentence, sentence_index

        except KeyError:
            return None, None

        except ValueError:
            logging.error('DocumentIssuedInvitationsListView.get_document - invalid sentence index')
            raise self.BadRequestException()

        except (Sentence.DoesNotExist, IndexError):
            logging.error('DocumentIssuedInvitationsListView.get_document - Sentence not found')
            raise self.NotFoundException()

    def allow_external(self, request):
        """
        Check if we allow external invites in the results
        """
        return request.GET.get('external', 'false').lower() == 'true'

    def get_list(self, request, *args, **kwargs):
        document = self.get_document(request, *args, **kwargs)
        if not document:
            raise self.NotFoundException("Document not found")
        invites = CollaborationInvite.objects.filter(inviter=self.user,
                                                     document=document)
        if self.allow_external(request):
            external_invites = ExternalInvite.pending_objects.filter(inviter=self.user,
                                                                     document=document)
            invites = list(chain(invites, external_invites))
        return invites

    def send_external_invite_email(self, request, external_invite, sentence_index=None):
        """
        `external_invite` may have a sentence attached. If so, the index of the sentence is `sentence_index`
        """
        serializer = URLSafeSerializer(settings.SECRET_KEY)
        encoded_email = serializer.dumps(add_salt(external_invite.email))
        signup_url = request.build_absolute_uri(reverse('signup'))
        signup_url = "%s?payload=%s" % (signup_url, encoded_email)
        send_external_invite.delay(external_invite.pk, signup_url)

    def send_collaboration_invite_email(self, request, collaboration_invite, sentence_index=None):
        """
        `collaboration_invite` may have a sentence attached. If so, the index of the sentence is `sentence_index`
        """
        from core.tools import login_resource_url

        if collaboration_invite.sentence is None:
            if sentence_index is not None:
                logging.error('DocumentIssuedInvitationsListView.send_collaboration_invite_email: '
                              'Strange state: sentence is None, but sentence_index is not None')
            report_url = collaboration_invite.document.get_report_url()
        else:
            if sentence_index is None:
                logging.error('DocumentIssuedInvitationsListView.send_collaboration_invite_email: '
                              'Strange state: sentence is not None, but sentence_index is None')
                report_url = collaboration_invite.document.get_report_url()
            else:
                report_url = collaboration_invite.sentence.get_report_url(sentence_index)

        follow_url = request.build_absolute_uri(
            login_resource_url(collaboration_invite.invitee, report_url)
        )

        send_collaboration_invite.delay(collaboration_invite.pk, follow_url)

    def save_model(self, model, item, request, *args, **kwargs):
        """
        Save the model, required for PostModelMixin
        """
        d = self.get_document(request, *args, **kwargs)

        if not d or not d.has_access(self.user):
            return None

        allow, _ = has_permission(request, 'invite', document=d)
        if not allow:
            logging.warning('%s tried to invite without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to invite people to this document")

        CollaboratorList.add_suggestion(self.user, email=item['invitee'])

        try:
            invitee = User.objects.get(email__iexact=item['invitee'])
            if invitee == d.owner:
                raise self.BadRequestException("The owner of the document can't invite himself/herself")

            try:
                CollaborationInvite.objects.get(inviter=self.user,
                                                invitee=invitee,
                                                document=d)
                raise self.UnauthorizedException("Collaboration invite already exists")
            except CollaborationInvite.DoesNotExist:
                sentence, sentence_index = self.get_sentence(d, item, request, *args, **kwargs)
                model.inviter = self.user
                model.invitee = invitee
                model.document = d
                model.sentence = sentence
                model.save()

                self.send_collaboration_invite_email(request, model, sentence_index)

                # Send notification
                NotificationManager.create_user_message(invitee, 'message', {
                    'notif': NotificationManager.ServerNotifications.DOCUMENT_INVITE_RECEIVED_NOTIFICATION
                }).send()

                CollaboratorList.add_suggestion(invitee, email=self.user.email)

            return model
        except User.DoesNotExist:
            if self.allow_external(request):
                try:
                    ExternalInvite.pending_objects.get(inviter=self.user,
                                                       email=item['invitee'],
                                                       document=d)
                    raise self.UnauthorizedException("External invite already exists")
                except ExternalInvite.DoesNotExist:
                    sentence, sentence_index = self.get_sentence(d, item, request, *args, **kwargs)
                    model = ExternalInvite(inviter=self.user,
                                           email=item['invitee'],
                                           document=d,
                                           sentence=sentence,
                                           pending=True)
                    model.save()

                    self.send_external_invite_email(request, model, sentence_index)

                return model

        return None

    def delete(self, request, *args, **kwargs):
        """
        Expected json {email: 'some@email.com'}
        Add external=True as an URL parameter to also search in ExternalInvites
        """
        data = json.loads(request.body)
        document = self.get_document(request, *args, **kwargs)
        if not document or document.owner != self.user:
            raise self.NotFoundException()

        allow, _ = has_permission(request, 'delete_invite', document=document)
        if not allow:
            logging.warning('%s tried to delete an invite without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to delete an invite with your subscription")

        if self.allow_external(request):
            try:
                external_invite = ExternalInvite.pending_objects.get(inviter=self.user,
                                                                     email=data['email'],
                                                                     document=document)
                external_invite.delete()
                return [external_invite.to_dict()]
            except ExternalInvite.DoesNotExist:
                pass

        try:
            invited_user = User.objects.get(email__iexact=data['email'])
            collaboration_invite = CollaborationInvite.objects.get(inviter=self.user,
                                                                   invitee=invited_user,
                                                                   document=document)

            collaboration_invite_pre_delete.send(
                sender=CollaborationInvite,
                request_user=request.user,
                instance=collaboration_invite
            )

            collaboration_invite.delete()
            # Send notification
            NotificationManager.create_user_message(invited_user, 'message', {
                'notif': NotificationManager.ServerNotifications.DOCUMENT_INVITE_RECEIVED_REVOKED_NOTIFICATION
            }).send()
            return [collaboration_invite.to_dict()]
        except (CollaborationInvite.DoesNotExist, User.DoesNotExist):
            raise self.NotFoundException("No Invitation for this user found")
        except Exception as e:
            raise self.BadRequestException(str(e))
