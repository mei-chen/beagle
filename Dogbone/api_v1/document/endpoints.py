import os
import json
import uuid
import urllib
import logging
import requests
from datetime import datetime
from newspaper import Article
from tempfile import TemporaryFile

from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.utils.timezone import now, get_current_timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
from django.utils.decorators import method_decorator

from core.tasks import (
    process_document_task, store_activity_notification,
    prepare_docx_export, send_document_uploaded_via_email_notification
)
from core.tools import disconnect_signal
from core.models import (
    Document,
    Batch,
    ExternalInvite,
    DelayedNotification,
    CollaborationInvite,
    UserLastViewDate,
    notify_collaboration_invite_creation,
)
from portal.models import WrongAnalysisFlag
from portal.services import get_annotations
from nlplib.utils import split_sentences
from utils import remove_extension
from beagle_simpleapi.endpoint import DetailView, ListView, ActionView, ComputeView
from beagle_simpleapi.mixin import DeleteDetailModelMixin
from beagle_realtime.notifications import NotificationManager
from integrations.tasks import send_slack_message
from dogbone.actions import has_permission
from richtext.importing import source_handler
from integrations.s3 import get_s3_bucket_manager
from utils.functional import first, hide_exceptions
from utils.http import filename_from_url
from utils.django_utils.query import get_user_by_identifier


class DocumentDetailView(DeleteDetailModelMixin, DetailView):
    model = Document
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)$'
    endpoint_name = 'document_detail_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    @classmethod
    def to_dict(cls, model):
        return model.to_dict(include_docstats=True)

    def delete(self, request, *args, **kwargs):
        self.validate_delete(request, *args, **kwargs)
        instance = self.get_object(request, *args, **kwargs)
        instance = self.delete_model(instance, request, *args, **kwargs)

        serialized = instance.to_dict(include_analysis=False)

        # Send a notification to let UI know that this doc got deleted
        message = NotificationManager.create_document_message(
            instance, 'message', {
                'notif': NotificationManager.ServerNotifications.DOCUMENT_DELETED_NOTIFICATION,
                'document': instance.to_dict(include_raw=False, include_analysis=False)})
        message.send()

        url = self.get_url(instance)

        if url:
            serialized['url'] = url

        return serialized

    def upon_successful_get(self, request, *args, **kwargs):
        """ Record last view datetime. """

        UserLastViewDate.create_or_update(
            document=self.instance,
            user=self.user,
            date=now()
        )


class DocumentViewedByView(DetailView):
    """
    Displays which users seen specific document and when.

    Format is: { str:username: str:last_view_date }
    """

    model = Document
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/viewed_by$'
    endpoint_name = 'document_viewed_by_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    @classmethod
    def to_dict(cls, model):
        return model.get_user_view_dates_str()


class DocumentListView(ListView):
    model = Batch
    url_pattern = r'document$'
    endpoint_name = 'document_list_view'

    _cached_object_count = None

    DEFAULT_RESULTS_PER_PAGE = 5

    @classmethod
    def to_dict(cls, model):
        return model.to_dict(include_raw=False,
                             include_analysis=False,
                             include_docstats=True)

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
        filtering_options = {'owner': self.user}
        if 'q' in request.GET:
            filtering_options['name__icontains'] = request.GET['q']
        queryset = self.model.objects.filter(**filtering_options)
        self._cached_object_count = queryset.count()
        return queryset.order_by('-created')


class DocumentSortedListView(DocumentListView):
    """
    Shows a list of Documents, sorted by last viewdate by current user.

    By default shows recent documents first. Order can be reversed by providing
    ?order=dsc in query params.
    """

    model = Document
    url_pattern = r'document-sorted$'
    endpoint_name = 'document_sorted_list_view'

    def _sort_by_viewdate(self, queryset, user, reversed):
        def _sort_func(document):
            try:
                vd = UserLastViewDate.objects.get(document=document, user=user)
                return vd.date
            except UserLastViewDate.DoesNotExist:
                return datetime.min.replace(tzinfo=get_current_timezone())

        sorted_queryset = sorted(
            queryset,
            key=_sort_func,
            reverse=reversed
        )

        return sorted_queryset

    def get_object_count(self):
        """
        Determine total number of objects in this list view.
        Returns a cached object count, no queries are made
        """
        # if the cached_object_count is none, no query was ever run. This
        # shouldn't ever be the case. But return 0 either way
        if self.request.GET.get('q'):
            return Document.objects.filter(
                owner=self.user, name__icontains=self.request.GET['q']
            ).count()
        else:
            return Document.objects.filter(owner=self.user).count()

    def get_list(self, request, *args, **kwargs):
        """
        Get the document list and make sure we don't SELECT the `cached_analysis` field
        This can cause overloading memory with unnecessary data
        """

        upload = Document.objects.filter(owner=self.user).order_by('-created')
        if self.request.GET.get('q'):
            upload = upload.filter(name__icontains=self.request.GET['q'])

        reversed = self.request.GET.get('order')
        upload = self._sort_by_viewdate(upload, request.user, reversed != 'dsc')

        return upload[self.get_slice()]


class DocumentAggregatedListView(ListView):
    model = Document
    url_pattern = r'document/aggregated$'
    endpoint_name = 'document_aggregated_list_view'

    @classmethod
    def to_dict(cls, model):
        return model.to_dict(include_raw=False,
                             include_analysis=False)

    def get_list(self, request, *args, **kwargs):
        return Document.get_aggregated_documents(self.user)[self.get_slice()]


class FlagDocumentActionView(ActionView):
    model = Document
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/flag$'
    endpoint_name = 'document_flag_action_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        data = json.loads(request.body)
        if 'comments' not in data:
            return {'status': 0, 'message': "Please provide a comment"}

        flag = WrongAnalysisFlag(user=self.user,
                                 doc=self.instance,
                                 comments=data['comments'])
        flag.save()
        return {'status': 1, 'message': "OK"}


class ChangePartiesActionView(ActionView):
    model = Document
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/parties$'
    endpoint_name = 'document_change_parties_action_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        data = json.loads(request.body)

        try:
            you_party, them_party = data['parties']
        except KeyError:
            return {'status': 0, 'message': 'Please provide parties'}
        except ValueError:
            return {'status': 0, 'message': '2 parties should be provided'}

        if self.instance.doclevel_analysis is None:
            # If no existing doclevel analysis default null string parties with zero confidence
            self.instance.doclevel_analysis = {
                'parties': {'them': {'name': '', 'confidence': 0}, 'you': {'name': '', 'confidence': 0}}}

        beforeThem = self.instance.doclevel_analysis['parties']['them']
        beforeYou = self.instance.doclevel_analysis['parties']['you']

        # Set confidence to 101 because over 100 is considered manually set
        self.instance.doclevel_analysis['parties']['them'] = {'name': them_party, 'confidence': 101}
        self.instance.doclevel_analysis['parties']['you'] = {'name': you_party, 'confidence': 101}

        self.instance.invalidate_analysis()
        self.instance.pending = True
        self.instance.save()

        # Trigger an analysis task
        process_document_task.delay(self.instance.pk, doclevel=False, is_reanalisys=True)

        if settings.DEBUG is False:
            # Collect slack message data (if on prod)
            beforePartyA = beforeThem['name']
            beforePartyAConfidence = beforeThem['confidence']
            beforePartyB = beforeYou['name']
            beforePartyBConfidence = beforeYou['confidence']
            afterPartyA = them_party
            afterPartyB = you_party
            actorFirst = self.user.first_name
            actorLast = self.user.last_name
            actorEmail = self.user.email
            docTitle = self.instance.title
            # Compile message
            message = "*{0} {1}* ({2}) updated parties:\n*Original Parties*\nParty A: *{3}* _confidence: {4}%_\nParty B: *{5}* _confidence: {6}%_\n*New Parties*\nParty A: *{7}*\nParty B: *{8}*\nOn report _{9}_".format(
                actorFirst, actorLast, actorEmail, beforePartyA, beforePartyAConfidence, beforePartyB,
                beforePartyBConfidence, afterPartyA, afterPartyB, docTitle)
            # Slack it
            send_slack_message(message, '#intercom')

        return {'status': 1, 'message': 'OK'}


class ReanalysisActionView(ActionView):
    model = Document
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/reanalysis$'
    endpoint_name = 'document_reanalysis_action_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        self.instance.invalidate_analysis()
        self.instance.pending = True
        self.instance.save()

        # Trigger an analysis task
        process_document_task.delay(self.instance.pk, doclevel=False, is_reanalisys=True)

        return {'status': 1, 'message': 'OK'}


class ChangeOwnerActionView(ActionView):
    model = Document
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/owner$'
    endpoint_name = 'document_change_owner_action_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        if self.instance.owner != self.user:
            raise self.UnauthorizedException("You can only change the owner of your documents")

        data = json.loads(request.body)

        try:
            owner_identifier = data['owner']
        except KeyError:
            raise self.BadRequestException("Please provide the new 'owner'")

        owner = get_user_by_identifier(owner_identifier)
        if owner is None:
            raise self.BadRequestException("The new owner can't be found")

        if not self.instance.has_access(owner):
            raise self.BadRequestException("The new owner doesn't have access to the document")

        if self.instance.owner == owner:
            raise self.BadRequestException("The new owner is the same as the old one")

        self.instance.change_owner(owner)

        # Don't send a notification to the issuer that he/she was invited to his/her own document
        with disconnect_signal(models.signals.post_save, notify_collaboration_invite_creation, CollaborationInvite):

            # Create an invitation for the old owner
            CollaborationInvite.objects.get_or_create(inviter=owner, invitee=self.user, document=self.instance)

            # Delete invitations of the new owner
            CollaborationInvite.objects.filter(invitee=owner, document=self.instance).delete()

        # Send a notification to all the collaborators (to change the UI)
        NotificationManager.create_document_message(self.instance, 'message', {
            'notif': NotificationManager.ServerNotifications.DOCUMENT_OWNER_CHANGED_NOTIFICATION,
            'document': self.instance.to_dict(include_raw=False, include_analysis=False)
        }).send()

        store_activity_notification.delay(
            actor_id=self.user.id,
            recipient_id=owner.id,
            verb='assigned ownership',
            target_id=owner.id,
            target_type="User",
            action_object_id=self.instance.id,
            action_object_type="Document",
            render_string="(actor) assigned ownership of (action_object) to (target)",
            transient=True,
        )

        return {'status': 1, 'message': 'OK'}


class IssueSentenceInvitesActionView(ActionView):
    model = Document
    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/sentence/assign$'
    endpoint_name = 'document_sentence_assign_action_view'

    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        data = json.loads(request.body)
        if 'sentences' not in data:
            raise self.BadRequestException("Please provide a list of sentences")

        if 'email' not in data:
            raise self.BadRequestException("Please provide the email for the invitee")

        try:
            invitee = User.objects.get(email__iexact=data['email'])

            # create some Notifications
            if not self.instance.has_access(invitee):
                logging.error("The invitee does not have access to this document in "
                              "IssueSentenceInvitesActionView inviter=%s, invitee=%s" % (self.user, invitee))
                raise self.UnauthorizedException("The invitee does not have access to this document")

            for sentence_idx in data['sentences']:
                try:
                    sentence = self.instance.get_sentence_by_index(int(sentence_idx))
                    if sentence is None:
                        continue

                    store_activity_notification.delay(
                        actor_id=self.user.id,
                        recipient_id=invitee.id,
                        verb='assigned',
                        target_id=invitee.id,
                        target_type="User",
                        action_object_id=sentence.id,
                        action_object_type="Sentence",
                        render_string="(actor) assigned (target) to a clause on (action_object)",
                        transient=False, )

                except ValueError:
                    pass

        except User.DoesNotExist:
            # Check if there is an external invite for this email
            try:
                ExternalInvite.objects.get(email__iexact=data['email'])
            except ExternalInvite.DoesNotExist:
                logging.error("There is no external invite for this email='%s', please send one first" % data['email'])
                raise self.UnauthorizedException("There is no external invite for this email='%s', "
                                                 "please send one first" % data['email'])

            # Create some delayed notifications
            for sentence_idx in data['sentences']:
                try:
                    sentence = self.instance.get_sentence_by_index(int(sentence_idx))
                    if sentence is None:
                        continue

                    DelayedNotification.delay_notification(
                        email=data['email'],
                        delayed_fields=['recipient', 'target'],
                        actor=self.user,
                        verb='assigned',
                        action_object=sentence,
                        render_string="(actor) assigned (target) to a clause on (action_object)",
                        transient=False, )

                except ValueError as e:
                    logging.error('Value error in IssueSentenceInvitesActionView: %s' % e)

        return {'status': 1, 'message': "OK"}


class UploadRawTextComputeView(ComputeView):
    url_pattern = r'document/upload/text'
    endpoint_name = 'document_upload_text_compute_view'

    def has_access(self):
        return True

    def compute(self, request, *args, **kwargs):
        request_dict = json.loads(request.body)

        try:
            text = request_dict['text']
            url = request_dict['url']
            username = request_dict['username']
        except KeyError as e:
            raise self.BadRequestException("%s not present" % str(e))

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise self.NotFoundException("The user does not exist")

        raw_sentences = split_sentences(text)

        batch = Batch.objects.create(name=url, owner=user, pending=True)
        timezone = request.session.get('user_time_zone')

        document = Document(owner=user,
                            original_name=url,
                            title=url,
                            pending=True,
                            batch=batch,
                            time_zone=timezone)

        document.init(raw_sentences)
        document.save()

        # Send the file to Celery
        process_document_task.delay(document.pk)

        return {'running': True}


class DocumentUploadComputeView(ComputeView):
    url_pattern = r'document/upload$'
    endpoint_name = 'document_upload_compute_view'

    HTML_CONTENT_TYPES = ('text/html', 'text/plain', 'application/xhtml+xml', 'application/xml')
    DOCX_CONTENT_TYPES = ('application/vnd.openxmlformats-officedocument.wordprocessingml.document',)
    DOC_CONTENT_TYPES = ('application/msword',)
    PDF_CONTENT_TYPES = ('application/pdf', 'application/x-pdf')

    class URLDocumentParseException(Exception):
        """
        Raised when we can't parse a page
        """
        status_code = 400
        error_type = 'error'

    class UnknownDocumentFormatException(Exception):
        """
        Raised when we can't parse a page
        """
        status_code = 400
        error_type = 'error'

    def has_access(self):
        return True

    def allow(self):
        allow, _ = has_permission(self.request, 'api_upload')
        return allow

    @method_decorator(hide_exceptions(lambda _: None))
    def handle_url(self, source_url, title=None):
        """
        Handles the url flow
        returns a core.models.Document
        """
        response = requests.get(source_url)
        if any(list(map(lambda ct: ct in response.headers.get('content-type'), self.HTML_CONTENT_TYPES))):
            return self.handle_html(html=response.content, title=title, source_url=source_url)

        elif any(list(map(lambda ct: ct in response.headers.get('content-type'), self.DOCX_CONTENT_TYPES))):
            filename = filename_from_url(source_url, 'file.docx', 'docx')
            input_file = TemporaryFile()

            input_file.write(response.content)
            input_file.seek(0)
            return self.handle_attached_file(filename=filename, uploaded_file=input_file)

        elif any(list(map(lambda ct: ct in response.headers.get('content-type'), self.DOC_CONTENT_TYPES))):
            filename = filename_from_url(source_url, 'file.doc', 'doc')
            input_file = TemporaryFile()

            input_file.write(response.content)
            input_file.seek(0)
            return self.handle_attached_file(filename=filename, uploaded_file=input_file)

        elif any(list(map(lambda ct: ct in response.headers.get('content-type'), self.PDF_CONTENT_TYPES))):
            filename = filename_from_url(source_url, 'file.pdf', 'pdf')
            input_file = TemporaryFile()

            input_file.write(response.content)
            input_file.seek(0)
            return self.handle_attached_file(filename=filename, uploaded_file=input_file)

        logging.error("Could not handle URL=%s. Response MIME type=%s" % (
            source_url, response.headers.get('content-type')))
        raise self.UnknownDocumentFormatException("Improper MIME type")

    @method_decorator(hide_exceptions(lambda _: (None, None, None)))
    def handle_html(self, source_url, title, html=None):
        article = Article(source_url)
        article.download(input_html=html)
        article.parse()

        text = article.text
        title = first((title, article.title, text[:50], str(now())), predicate=lambda item: item)

        if not text:
            raise self.URLDocumentParseException("The page could not be parsed")

        return self.handle_text(text, title)

    @method_decorator(hide_exceptions(lambda _: (None, None, None)))
    def handle_text(self, text, title=None):
        if not text:
            raise self.URLDocumentParseException("The page could not be parsed")

        # Get the title value, the first non-None value from the list
        title = first((title, text[:50], str(now())), predicate=lambda item: item)
        filename = urllib.parse.quote_plus(title.encode('utf8')) + '.txt'
        return title, filename, text

    @method_decorator(hide_exceptions(lambda _: (None, None, None)))
    def handle_attached_file(self, filename, uploaded_file):
        # Get the proper uploader
        upload_handler = source_handler('local')

        # Process the upload request
        is_success, payload = upload_handler.process(uploaded_file=uploaded_file)

        # Something went wrong during the file processing, refresh
        if not is_success:
            raise self.BadRequestException("Could not process file")

        _, temp_file_handle = payload
        title = remove_extension(filename).replace('_', ' ')

        content = temp_file_handle.read()

        return title, filename, content

    @staticmethod
    def save_tempfile(content):
        temp_path = default_storage.save(str(uuid.uuid4()), ContentFile(content))
        temp_filename = os.path.join(settings.MEDIA_ROOT, temp_path)
        return temp_filename

    def process_document(self, title, filename, content, source, time_zone=None):
        if not content or not filename or not title:
            return None

        temp_filename = self.save_tempfile(content)
        batch = Batch.objects.create(name=filename, owner=self.user, pending=True)

        return Document.analysis_workflow_start(uploader=self.user,
                                                file_path=temp_filename,
                                                upload_source=source,
                                                original_filename=filename,
                                                title=title,
                                                batch=batch,
                                                time_zone=time_zone)

    def compute(self, request, *args, **kwargs):
        if not self.allow():
            logging.warning('%s tried upload document via API without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to upload document via API with your subscription")

        try:
            request_dict = json.loads(request.body)
        except ValueError:
            logging.error('Value error on json.loads(request.body), request.body = %s' % request.body)
            request_dict = {}

        document = None
        upload_source = first(
            (
                request.GET.get('source'),
                'email' if 'send_upload_via_email' in request.GET else None,
                'local'
            ),
            predicate=lambda item: item)

        ###############################################################################################
        #
        #  Uploading files
        #
        ###############################################################################################
        if request.FILES:
            for filename in request.FILES:
                title, filename, content = self.handle_attached_file(filename, request.FILES[filename])
                user_time_zone = request.session.get('user_time_zone')
                document = self.process_document(title, filename, content, upload_source, user_time_zone)

        ###############################################################################################
        #
        #  Sending URLs or text
        #
        ###############################################################################################
        else:
            url = request_dict.get('url')
            text = request_dict.get('text')
            title = request_dict.get('title')

            if not url:
                logging.warning('URL not provided')
            if not text:
                logging.warning('Text not provided')

            if not url and not text:
                raise self.BadRequestException("Both URL and Text not provided")

            if text:
                title, filename, content = self.handle_text(text=text, title=title)
            else:
                title, filename, content = self.handle_url(source_url=url, title=title)
            user_time_zone = request.session.get('user_time_zone')

            document = self.process_document(title, filename, content, upload_source, user_time_zone)

        if not document:
            logging.warning('Could not process any documents for user=%s' % self.user)
            raise self.BadRequestException("Something went wrong. Could not process the documents.")

        if request.GET.get('send_upload_via_email'):
            send_document_uploaded_via_email_notification.delay(document.pk)

        # In case everything went well, send the data back to the user
        return document.to_dict(include_raw=False, include_analysis=False)


class DocumentPrepareExportView(ActionView):
    """
    This only triggers the celery task that generates the exported file
    (See DocumentExportView to actually serve this file after it's generated)
    """

    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/prepare_export'
    endpoint_name = 'document_prepare_export_view'
    model = Document
    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        """
        - Check that the user is authenticated
        - Set the appropriate HTTP status
        - In case an exception occurs, handle the response accordingly
        - Generate proper DOCX file in the Media folder (async)
        """
        try:
            self.check_model()
            self.instance = self.get_object(request, *args, **kwargs)

            self.user = self.authenticate_user()

            if not self.has_access(self.instance):
                raise self.UnauthorizedException("You don't have access to this resource")

            allow, _ = has_permission(request, 'export', document=self.instance)
            if not allow:
                logging.warning('%s tried to export without proper subscription' % self.user)
                raise self.UnauthorizedException("You are not allowed to export with your subscription")

            s3_path = settings.S3_EXPORT_PATH % self.instance.uuid

            include_comments = False
            include_track_changes = False
            included_annotations = None

            try:
                if request.body:
                    data = json.loads(request.body)

                    include_comments = data.get('include_comments')
                    include_track_changes = data.get('include_track_changes')
                    included_annotations = data.get('included_annotations')
            except Exception as e:
                logging.error('%s' % e)

            prepare_docx_export.delay(
                self.instance.pk,
                s3_path,
                include_comments=include_comments,
                include_track_changes=include_track_changes,
                included_annotations=included_annotations,
                user_id=self.user.id
            )

            return {'status': 1, 'message': 'OK', 'filepath': s3_path}
        except Exception as e:
            result = self.build_error_response_from_exception(e)
            return result


class DocumentExportView(DetailView):
    """
    This serves the exported file from the /media folder.
    Note: it has to be generated first, by a call to DocumentPrepareExportView
    """

    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/export'
    endpoint_name = 'document_export_view'
    model = Document
    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def dispatch(self, request, *args, **kwargs):
        """
        - Check that the user is authenticated
        - Set the appropriate HTTP status
        - In case an exception occurs, handle the response accordingly
        - Serve the proper DOCX file to the client
        """
        try:
            self.check_model()
            self.instance = self.get_object(request, *args, **kwargs)

            self.user = self.authenticate_user()

            if not self.has_access(self.instance):
                raise self.UnauthorizedException("You don't have access to this resource")

            allow, _ = has_permission(request, 'export', document=self.instance)
            if not allow:
                logging.warning('%s tried to export without proper subscription' % self.user)
                raise self.UnauthorizedException("You are not allowed to export with your subscription")

            out_filename = '%s.beagle.docx' % remove_extension(
                os.path.basename(self.instance.original_name)
            )
            s3_path = settings.S3_EXPORT_PATH % self.instance.uuid

            # TODO: Get the file handle from S3

            s3_bucket = get_s3_bucket_manager(settings.UPLOADED_DOCUMENTS_BUCKET)
            exported_file = s3_bucket.read_to_file(s3_path)

            if exported_file is None:
                raise self.NotFoundException("Exported file not found")

            # Prepare document for download
            response = HttpResponse(
                exported_file.read(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = 'attachment; filename=' + out_filename
            return response

        except Exception as e:
            result = self.build_error_response_from_exception(e)
            return HttpResponse(self.serialize(result, request.GET.get('format', 'json')),
                                status=result['http_status'], content_type='application/json')


class DocumentAnnotationsView(DetailView):
    """ Returns all non-keyword tags that exist in provided document. """

    url_pattern = r'document/(?P<uuid>[a-z0-9\-]+)/annotations'
    endpoint_name = 'document_annotations_view'
    model = Document
    model_key_name = 'uuid'
    url_key_name = 'uuid'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def to_dict(cls, model):
        return get_annotations(model)
