import mock
import os
import shutil

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from dogbone.tools import absolutify
from dogbone.testing.base import BeagleWebTest
from core.tasks import (
    process_document_task, process_document_conversion,
    send_document_complete_notification, send_password_request,
    send_external_invite, prepare_docx_export, InvalidDocumentTypeException,
    EasyPDFCloudHTTPException
)
from portal.mailer import BeagleMailer
from portal.models import ExternalInvite
from core.models import Sentence, SentenceAnnotations, Document
from authentication.models import PasswordResetRequest, OneTimeLoginHash
from keywords.models import SearchKeyword

TEST_DOCX_COMMENT = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'resources', 'TestCommenting.docx')
TEST_DOCX_REDLINE = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'resources', 'TestChangeTracking.docx')


def get_sample_filename(filename):
    return '%s_sample%s' % os.path.splitext(filename)


def get_or_create_user(username):
    user, _ = User.objects.get_or_create(
        username='%s_test' % username, email='%s_test@test.test' % username
    )
    return user


def get_or_create_document(filename, user, batch):
    sample_filename = get_sample_filename(filename)
    document, _ = Document.objects.get_or_create(
        original_name=sample_filename, owner=user, batch=batch
    )
    return document


class ProcessDocumentConversionTest(BeagleWebTest):

    def test_process_document_conversion_success(self):
        batch = self.create_batch('Some title', self.user)
        doc = self.create_document('Some title', self.user, pending=True, batch=batch)
        with mock.patch('core.tasks.process_document_task.delay') as mock_process_document_task:
            with mock.patch('core.tasks.conversion.document2sentences') as mock_conversion_document2sentences:
                with mock.patch(
                    'core.tasks.NotificationManager.create_document_message') as mock_create_document_message:
                    # Test the document2sentences
                    mock_conversion_document2sentences.return_value = ([u'Sentence One__/BR/__',
                                                                        u'Sentence Two__/BR/__',
                                                                        u'Sentence Three__/BR/__', ], None, None)
                    success = process_document_conversion(doc_id=doc.id, temp_filename='/media/dummy.txt')
                    mock_conversion_document2sentences.assert_called_once_with(doc, '/media/dummy.txt', u'.pdf')
                    # Test document process task IS called
                    mock_process_document_task.assert_called_once_with(send_emails=True, doc_id=doc.id,
                                                                       send_notifications=True)
                    # Test Beagle Realtime Notification Sent
                    self.assertTrue(mock_create_document_message.called)
                    # see that the task returns TRUE
                    self.assertTrue(success)

    def test_process_document_conversion_invalid_file_type(self):
        batch = self.create_batch('Some title', self.user)
        doc = self.create_document('Some title', self.user, pending=True, batch=batch)
        with mock.patch('core.tasks.process_document_task.delay') as mock_process_document_task:
            with mock.patch('core.tasks.conversion.document2sentences',
                            side_effect=InvalidDocumentTypeException()) as mock_conversion_document2sentences:
                with mock.patch('core.tasks.NotificationManager.create_document_message') as mock_create_document_message:
                    with mock.patch('core.tasks.log_intercom_custom_event.delay') as mock_log_intercom_custom_event, \
                            mock.patch('core.tasks.log_statistic_event.delay') as mock_log_statistic_event:
                        mock_conversion_document2sentences.return_value = None
                        success = process_document_conversion(doc_id=doc.id, temp_filename='/media/dummy.txt')
                        # Test the document2sentences
                        mock_conversion_document2sentences.assert_called_once_with(doc, '/media/dummy.txt', u'.pdf')
                        # Test document process task is NOT called
                        self.assertFalse(mock_process_document_task.called)
                        # Test Beagle Real time Notification (failure) Sent
                        self.assertTrue(mock_create_document_message.called)
                        event_metadata = {
                            'Error': u'Document format not supported (pdf)',
                            'Title': u'Some title'
                        }
                        # Test Intercom Event Is Sent
                        mock_log_intercom_custom_event.assert_called_once_with(event_name='Document Conversion Error',
                                                                               email=self.user.email,
                                                                               metadata=event_metadata)
                        # Test Statistics Event Is Sent
                        mock_log_statistic_event.assert_called_once_with(event_name='document_conversion_error',
                                                                         event_user=self.user,
                                                                         event_data=event_metadata)

                        # see that the task returns FALSE
                        self.assertFalse(success)

    def test_process_document_conversion_easyPDF_error(self):
        batch = self.create_batch('Some title', self.user)
        doc = self.create_document('Some title', self.user, pending=True, batch=batch)
        with mock.patch('core.tasks.process_document_task.delay') as mock_process_document_task:
            with mock.patch('core.tasks.conversion.document2sentences',
                            side_effect=EasyPDFCloudHTTPException(403, 'reason', 'error',
                                                                  'description')) as mock_conversion_document2sentences:
                with mock.patch('core.tasks.NotificationManager.create_document_message') as mock_create_document_message:
                    with mock.patch('core.tasks.log_intercom_custom_event.delay') as mock_log_intercom_custom_event, \
                            mock.patch('core.tasks.log_statistic_event.delay') as mock_log_statistic_event:
                        with mock.patch('core.tasks.send_intercom_inapp_message.delay') as mock_send_intercom_inapp_message:
                            mock_conversion_document2sentences.return_value = None
                            success = process_document_conversion(doc_id=doc.id, temp_filename='/media/dummy.txt')

                            # Test the document2sentences
                            mock_conversion_document2sentences.assert_called_once_with(doc, '/media/dummy.txt', u'.pdf')

                            # Test document process task is NOT called
                            self.assertFalse(mock_process_document_task.called)

                            # Test Beagle Realtime Notification (failure) Sent
                            self.assertTrue(mock_create_document_message.called)

                            # Test intercom inapp message is sent
                            mock_send_intercom_inapp_message.assert_called_once_with(
                                message='Hi {{first_name | fallback: "there" }},\n\nWe noticed that there was a problem with the PDF you uploaded. We apologize for the error and are looking into it. In the meantime please feel free to try a different document.\n\nWe appreciate your patience and feedback, thanks for using Beagle! ',
                                to_email=self.user.email, from_id=settings.INTERCOM_STAFF['BeagleSupport'])

                            event_metadata = {
                                'Error': 'EasyPDF error. Exception: 403: reason. Error: error. Description/Source: description.',
                                'Title': u'Some title'
                            }

                            # Test Intercom Event Is Sent
                            mock_log_intercom_custom_event.assert_called_once_with(event_name='Document Conversion Error',
                                                                                   email=self.user.email,
                                                                                   metadata=event_metadata)

                            # Test Statistics Event Is Sent
                            mock_log_statistic_event.assert_called_once_with(event_name='document_conversion_error',
                                                                             event_user=self.user,
                                                                             event_data=event_metadata)

                            # see that the task returns FALSE
                            self.assertFalse(success)

    def test_process_document_conversion_malformed_error(self):
        batch = self.create_batch('Some title', self.user)
        doc = self.create_document('Some title', self.user, pending=True, batch=batch)
        with mock.patch('core.tasks.process_document_task.delay') as mock_process_document_task:
            with mock.patch('core.tasks.conversion.document2sentences',
                            side_effect=Exception()) as mock_conversion_document2sentences:
                with mock.patch('core.tasks.NotificationManager.create_document_message') as mock_create_document_message:
                    with mock.patch('core.tasks.log_intercom_custom_event.delay') as mock_log_intercom_custom_event, \
                            mock.patch('core.tasks.log_statistic_event.delay') as mock_log_statistic_event:
                        mock_conversion_document2sentences.return_value = None
                        success = process_document_conversion(doc_id=doc.id, temp_filename='/media/dummy.txt')

                        # Test the document2sentences
                        mock_conversion_document2sentences.assert_called_once_with(doc, '/media/dummy.txt', u'.pdf')

                        # Test document process task is NOT called
                        self.assertFalse(mock_process_document_task.called)

                        # Test Beagle realtime Notification (failure) Sent
                        self.assertTrue(mock_create_document_message.called)

                        event_metadata = {
                            'Error': 'Exception: ',
                            'Title': u'Some title'
                        }

                        # Test Intercom Event Is Sent
                        mock_log_intercom_custom_event.assert_called_once_with(event_name='Document Conversion Error',
                                                                               email=self.user.email,
                                                                               metadata=event_metadata)

                        # Test Statistics Event Is Sent
                        mock_log_statistic_event.assert_called_once_with(event_name='document_conversion_error',
                                                                         event_user=self.user,
                                                                         event_data=event_metadata)

                        # see that the task returns FALSE
                        self.assertFalse(success)


class ProcessDocumentTaskTest(BeagleWebTest):

    def test_keyword_annotations(self):
        """
        Check that the Keyword annotation is working properly
        - Create a keyword
        - Create a document
        - Check that the keyword has been properly annotated in the document's sentences
        """
        kw = SearchKeyword.add(self.user, 'interesting')
        kw.exact_match = True
        kw.save()

        document = self.create_analysed_document(
            'A document',
            [
                'This is interesting!  ',
                'That\' what we are interestingly enough are looking for!',
                'Interesting!!!'
            ],
            self.user
        )

        sentences = Sentence.objects.filter(doc=document).order_by('pk')
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0].annotations, {
            'annotations': [
                {
                    'classifier_id': None,
                    'experiment_uuid': None,
                    'label': 'interesting',
                    'sublabel': None,
                    'user': self.DUMMY_USERNAME,
                    'party': None,
                    'type': SentenceAnnotations.KEYWORD_TAG_TYPE,
                    'approved': False
                }
            ]
        })

        self.assertIsNone(sentences[1].annotations)

        self.assertEqual(sentences[2].annotations, {
            'annotations': [
                {
                    'classifier_id': None,
                    'experiment_uuid': None,
                    'label': 'interesting',
                    'sublabel': None,
                    'user': self.DUMMY_USERNAME,
                    'party': None,
                    'type': SentenceAnnotations.KEYWORD_TAG_TYPE,
                    'approved': False
                }
            ]
        })

    def test_document_process_task_success(self):
        batch = self.create_batch('Some title', self.user)
        doc = self.create_document('Some title', self.user, pending=True, batch=batch)
        with mock.patch('core.tasks.send_document_digest.delay') as mock_send_digest:
            with mock.patch('core.tasks.log_intercom_custom_event.delay') as mock_log_intercom_custom_event, \
                    mock.patch('core.tasks.log_statistic_event.delay') as mock_log_statistic_event:
                with mock.patch('core.tasks.send_slack_message') as mock_send_slack_message:
                    process_document_task(doc.id)
                    mock_send_digest.assert_called_once_with(doc.id, False)
                    event_metadata = {
                        'Liabilities': 0,
                        'Title': u'Some title',
                        'Terminations': 0,
                        'Report Url': {
                            'url': absolutify(doc.get_report_url()),
                            'value': 'View Report'
                        },
                        'Responsibilities': 0,
                        'Party Confidence Mean': 0,
                        'External References': 0
                    }
                    mock_log_intercom_custom_event.assert_called_once_with(event_name='Document Processed',
                                                                           email=self.user.email,
                                                                           metadata=event_metadata)
                    mock_log_statistic_event.assert_called_once_with(event_name='document_processed',
                                                                     event_user=self.user,
                                                                     event_data=event_metadata)
                    mock_send_slack_message.assert_called_once_with('  ({0}) recieved a low party confidence mean of '
                                                                    '0%\nR: *0*\nL: *0*\nT: *0*\nE: *0*\n'
                                                                    'on document _Some title_'.format(self.user.email),
                                                                    '#intercom')


class PrepareExportTaskTest(BeagleWebTest):

    def test_document_process_task(self):
        batch = self.create_batch('Some title', self.user)
        doc = self.create_document('Some title', self.user, batch=batch, pending=True)

        s3_path = settings.S3_EXPORT_PATH % doc.uuid
        default = {
            'include_comments': False,
            'include_track_changes': False,
            'included_annotations': None
        }

        with mock.patch('richtext.exporting.document_to_docx') as document_to_docx_mock, \
                mock.patch('richtext.exporting.document_to_rich_docx') as document_to_rich_docx_mock:
            prepare_docx_export(doc.pk, s3_path)
            document_to_docx_mock.assert_called_once_with(doc, s3_path, **default)
            document_to_rich_docx_mock.assert_not_called()

        with mock.patch('core.models.get_s3_bucket_manager'):
            doc.save_docx(mock.ANY)

        with mock.patch('richtext.exporting.document_to_docx') as document_to_docx_mock, \
                mock.patch('richtext.exporting.document_to_rich_docx') as document_to_rich_docx_mock:
            prepare_docx_export(doc.pk, s3_path)
            document_to_docx_mock.assert_not_called()
            document_to_rich_docx_mock.assert_called_once_with(doc, s3_path, **default)


class SendDocumentCompleteNotificationTaskTest(BeagleWebTest):
    NEED_DEFAULT_USER = False

    def setUp(self):
        super(SendDocumentCompleteNotificationTaskTest, self).setUp()
        self.user = self.create_user()

    def test_send_document_complete_notification_task_with_tour(self):
        doc = self.create_document('Some title', self.user, pending=True)
        self.user.details.initial_tour = now()
        self.user.details.save()
        with mock.patch('core.tasks.BeagleMailer.document_complete_notification') as mock_notification:
            send_document_complete_notification(doc.pk)
            mock_notification.assert_called_once_with(self.user, doc, absolutify(doc.get_report_url()))

    def test_send_document_complete_notification_task_without_tour(self):
        doc = self.create_document('Some title', self.user, pending=True)
        with mock.patch('core.tasks.BeagleMailer.document_complete_notification') as mock_notification:
            with mock.patch('authentication.models.OneTimeLoginHash.get_hash', return_value='1234'):
                send_document_complete_notification(doc.pk)
                login_hash = OneTimeLoginHash.objects.all()
                self.assertEqual(len(login_hash), 1)
                mock_notification.assert_called_once_with(self.user, doc,
                                                          absolutify("%s?next=%s&hash=%s" % (
                                                              reverse('login'),
                                                              doc.get_report_url(),
                                                              login_hash[0].get_hash())))

    def test_beagle_mailer_send_document_complete_notification(self):
        self.user.first_name = "FIRST"
        self.user.last_name = "LAST"
        doc = self.create_document('Some title', self.user, pending=True)
        with mock.patch('portal.mailer.Mailer.send') as mock_send:
            BeagleMailer.document_complete_notification(self.user, doc, 'http://some.url')
            mock_send.assert_called_once_with(from_email=BeagleMailer.DEFAULT_FROM_EMAIL,
                                              to_email=self.DUMMY_EMAIL,
                                              args={
                                                  'follow_link': 'http://some.url',
                                                  'document_title': doc.title,
                                                  'first_name': 'First'},
                                              template='email/document_processed.html',
                                              html_template='email/html/document_processed.html',
                                              subject='Beagle has processed your documents')


class SendPasswordRequestTaskTest(BeagleWebTest):

    def test_send_password_request_task(self):
        pass_request = PasswordResetRequest.create(self.DUMMY_EMAIL)
        with mock.patch('core.tasks.BeagleMailer.send_password_request') as mock_notification:
            send_password_request(pass_request.pk, 'http://some.url')
            mock_notification.assert_called_once_with(pass_request, 'http://some.url')

    def test_beagle_mailer_send_password_request_task(self):
        pass_request = PasswordResetRequest.create(self.DUMMY_EMAIL)
        with mock.patch('portal.mailer.Mailer.send') as mock_send:
            BeagleMailer.send_password_request(pass_request, 'http://some.url')
            mock_send.assert_called_once_with(from_email=BeagleMailer.DEFAULT_FROM_EMAIL,
                                              to_email=self.DUMMY_EMAIL,
                                              args={'follow_link': 'http://some.url', 'firstname': 'dummy_user'},
                                              template='email/request_password.html',
                                              html_template='email/html/request_password.html',
                                              subject='Reset password on Beagle.ai')


class SendExternalInviteTaskTest(BeagleWebTest):
    NEED_DEFAULT_USER = False

    def setUp(self):
        super(SendExternalInviteTaskTest, self).setUp()
        self.user = self.create_user()

    def test_send_external_invite_task(self):
        doc = self.create_document('Some title', self.user, pending=True)
        external_invite = ExternalInvite(inviter=self.user, document=doc, email='123@yahoo.com')
        external_invite.save()
        with mock.patch('core.tasks.BeagleMailer.send_external_invite') as mock_notification:
            send_external_invite(external_invite.pk, 'http://some.url')
            mock_notification.assert_called_once_with(external_invite, 'http://some.url')

    def test_beagle_mailer_send_external_invite_task(self):
        self.user.first_name = "LALALA"
        doc = self.create_document('Some title', self.user, pending=True)
        external_invite = ExternalInvite(inviter=self.user, document=doc, email='123@yahoo.com')
        external_invite.save()
        with mock.patch('portal.mailer.Mailer.send') as mock_send:
            BeagleMailer.send_external_invite(external_invite, 'http://some.url')
            mock_send.assert_called_once_with(from_email='Beagle.ai Collaboration Invitation <noreply@beagle.ai>',
                                              to_email='123@yahoo.com',
                                              args={'follow_url': 'http://some.url',
                                                    'document_title': 'Some title',
                                                    'firstname': 'Lalala',
                                                    'sentence_text': None},
                                              template='email/external_invite.html',
                                              html_template='email/html/external_invite.html',
                                              subject='Lalala invited you to collaborate on Beagle.ai')


class UnsupportedFileTypeTaskTest(BeagleWebTest):

    def test_send_unsupported_file_type_notification(self):
        from core.tasks import send_unsupported_file_type_notification
        with mock.patch('core.tasks.BeagleMailer.unsupported_file_type_error_notification') as mock_notification:
            send_unsupported_file_type_notification(self.user.pk, "StrangeFileType.xxx")
            mock_notification.assert_called_with(self.user, 'StrangeFileType.xxx')

    def test_send_unsupported_file_type_notification_send(self):
        from core.tasks import send_unsupported_file_type_notification
        with mock.patch('core.tasks.BeagleMailer.send') as mock_send:
            send_unsupported_file_type_notification(self.user.pk, "StrangeFileType.xxx")
            mock_send.assert_called_with(to_email=self.DUMMY_EMAIL,
                                         args={
                                             'first_name': self.DUMMY_USERNAME,
                                             'title': 'StrangeFileType.xxx'
                                         },
                                         from_email='Beagle Support <support@beagle.ai>',
                                         template='email/file_type_error.html',
                                         html_template='email/html/file_type_error.html',
                                         subject="We don't support this file type")


class TestImportingComments(BeagleWebTest):
    ''' Tests full workflow of adding comments on document upload. '''

    NEED_DEFAULT_USER = False

    def test_docx_with_comments(self):
        sample_filename = get_sample_filename(TEST_DOCX_COMMENT)
        shutil.copy(TEST_DOCX_COMMENT, sample_filename)
        user = get_or_create_user('user_for_comments')
        batch = self.create_batch(TEST_DOCX_COMMENT, user)
        document_id = get_or_create_document(filename=TEST_DOCX_REDLINE,
                                             user=user, batch=batch).id
        with mock.patch('core.models.get_s3_bucket_manager'):
            success = process_document_conversion(document_id, sample_filename)
            self.assertTrue(success)
        document = Document.objects.get(pk=document_id)
        sentences = document.get_sorted_sentences()
        expected_comments = [(u'My favorite sentence!', True, u'Dmitriy Uvarenkov'),
                             (u'Mine too!', True, u'Dmitriy Uvarenkov'),
                             (u'Second commented sentence', True, u'Dmitriy Uvarenkov'),
                             (u'Commented range', True, u'Dmitriy Uvarenkov'),
                             (u'Commented range', True, u'Dmitriy Uvarenkov')]
        actual_comments = []
        for sentence in sentences:
            for comment in (sentence.comments or {}).get('comments', []):
                actual_comments.append((comment['message'],
                                        comment['is_imported'],
                                        comment['original_author']))
        self.assertEqual(expected_comments, actual_comments)


class TestImportingRedlines(BeagleWebTest):
    """ Tests full workflow of adding redlines on document upload. """

    NEED_DEFAULT_USER = False

    def test_docx_with_tracked_changes(self):
        sample_filename = get_sample_filename(TEST_DOCX_REDLINE)
        shutil.copy(TEST_DOCX_REDLINE, sample_filename)
        user = get_or_create_user('user_for_redlines')
        batch = self.create_batch(TEST_DOCX_REDLINE, user)
        document_id = get_or_create_document(filename=TEST_DOCX_REDLINE,
                                             user=user, batch=batch).id
        with mock.patch('core.models.get_s3_bucket_manager'):
            success = process_document_conversion(document_id, sample_filename)
            self.assertTrue(success)
        document = Document.objects.get(pk=document_id)
        sentences = document.get_sorted_sentences()
        changes = [
            (u'This sentence has no changes.', None, False),
            (u'This is a brand new sentence!', u'', False),
            (u'This sentence does not exist anymore!', u'This sentence does not exist anymore!', True),
            (u'This sentence has some insertions inside.', u'This sentence has some deletions inside.', False)
        ]
        for sentence, change in zip(sentences, changes):
            expected_new_text, expected_old_text, expected_is_deleted = change
            actual_new_text = sentence.text
            if sentence.prev_revision is not None:
                actual_old_text = sentence.prev_revision.text
            else:
                actual_old_text = None
            actual_is_deleted = sentence.deleted
            self.assertEqual(expected_new_text, actual_new_text)
            self.assertEqual(expected_old_text, actual_old_text)
            self.assertEqual(expected_is_deleted, actual_is_deleted)
