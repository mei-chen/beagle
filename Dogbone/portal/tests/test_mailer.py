import mock
import urllib.parse
import unittest
from datetime import datetime, timedelta

from django.template import Template
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from notifications.models import Notification
from django.test.utils import override_settings

from dogbone.testing.base import BeagleWebTest
from dogbone.tools import absolutify
from portal.mailer import Mailer, BeagleMailer
from core.models import CollaborationInvite
from core.tasks import store_activity_notification
from authentication.models import OneTimeLoginHash


class MailerTest(BeagleWebTest):

    def test_send_mail(self):
        with mock.patch('portal.mailer.get_template') as mock_get_template:
            mock_get_template.return_value = Template("Hello {{ name }}")
            with mock.patch('portal.mailer.EmailMultiAlternatives') as mock_send_mail:
                result = Mailer.send('to@email.com', 'from@email.com', 'Title', 'the_template.html', 'the_html.html',
                                     args={'name': 'Jorje'})
                mock_send_mail.assert_has_calls([mock.call('Title',
                                                           'Hello Jorje',
                                                           'from@email.com',
                                                           ['to@email.com']),
                                             mock.call().attach_alternative(mock.ANY, "text/html"),
                                             mock.call().send(fail_silently=True)])
                self.assertTrue(result)

    def test_multiple_emails(self):
        with mock.patch('portal.mailer.get_template') as mock_get_template:
            mock_get_template.return_value = Template("Hello {{ name }}")
            with mock.patch('portal.mailer.EmailMultiAlternatives') as mock_send_mail:
                result = Mailer.send(['to@email.com', 'another@email.com'], 'from@email.com',
                                     'Title', 'the_template.html', 'the_html.html', args={'name': 'Jorje'})

                mock_send_mail.assert_has_calls([mock.call('Title',
                                                           'Hello Jorje',
                                                           'from@email.com',
                                                           ['to@email.com', 'another@email.com']),
                                             mock.call().attach_alternative(mock.ANY, "text/html"),
                                             mock.call().send(fail_silently=True)])
                self.assertTrue(result)

    def test_something_wrong(self):
        with mock.patch('portal.mailer.get_template') as mock_get_template:
            mock_get_template.return_value = Template("Hello {{ name }}")
            with mock.patch('portal.mailer.EmailMultiAlternatives') as mock_send_mail:
                mock_send_mail.side_effect = Exception("Something went wrong")
                result = Mailer.send(['to@email.com', 'another@email.com'], 'from@email.com',
                                     'Title', 'the_template.html', 'the_html_template.html', args={'name': 'Jorje'})

                mock_send_mail.assert_has_calls([mock.call('Title',
                                                           'Hello Jorje',
                                                           'from@email.com',
                                                           ['to@email.com', 'another@email.com']),])
                self.assertFalse(result)


class BeagleMailerAddressUserTest(BeagleWebTest):
    def test_having_just_username_eq_email(self):
        u = User(email='aaa@gmail.com', username='aaa@gmail.com')
        u.save()

        self.assertEqual(BeagleMailer.address_user(u), 'aaa')

    def test_having_username(self):
        u = User(email='aaa@gmail.com', username='mark1234')
        u.save()

        self.assertEqual(BeagleMailer.address_user(u), 'mark1234')

    def test_having_firstname(self):
        u = User(email='aaa@gmail.com', username='mark69', first_name='mark')
        u.save()

        self.assertEqual(BeagleMailer.address_user(u), 'Mark')

    def test_having_lastname(self):
        u = User(email='aaa@gmail.com', username='mark69', last_name='Brown')
        u.save()

        self.assertEqual(BeagleMailer.address_user(u), 'Brown')

    def test_having_both(self):
        u = User(email='aaa@gmail.com', username='mark69', first_name='Mark', last_name='Brown')
        u.save()

        self.assertEqual(BeagleMailer.address_user(u), 'Mark')

    def test_sir_madam(self):
        u = User(email='aaa@gmail.com', username='contact@gmail.com')
        u.save()

        self.assertEqual(BeagleMailer.address_user(u), 'Sir/Madam')


class BeagleMailerSendDigestTestCase(BeagleWebTest):

    @unittest.skip('TODO: why is this failing?')
    def test_simple_text(self):
        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document',
                                                 sentences, self.user)

        from core.models import Sentence
        s1model = Sentence.objects.get(id=document.sentences_ids[0])
        s1model.add_tag(None, 'RESPONSIBILITY', party='them')
        s1model.add_tag(None, 'TERMINATION', party='them')
        s1model.add_tag(None, 'LIABILITY', party='you')

        s2model = Sentence.objects.get(id=document.sentences_ids[1])

        s2model.add_tag(None, 'TERMINATION', party='them')
        s2model.add_tag(None, 'LIABILITY', party='them')
        s2model.add_tag(None, 'NON_STANDARD')

        with mock.patch('portal.mailer.EmailMultiAlternatives') as mock_send_mail:
                BeagleMailer.send_document_digest(self.user, document)
                mock_send_mail.assert_called_with('Beagle has processed your document',
                                                  mock.ANY,
                                                  BeagleMailer.DEFAULT_FROM_EMAIL,
                                                  [self.DUMMY_EMAIL])
                text_email = mock_send_mail.call_args[0][1]
                self.assertIn('Liabilities: 2 clauses', text_email)
                self.assertIn('Responsibilities: 1 clauses', text_email)
                self.assertIn('Terminations: 2 clauses', text_email)

    @unittest.skip('TODO: why is this failing?')
    def test_simple_html(self):
        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document',
                                                 sentences, self.user)

        from core.models import Sentence
        s1model = Sentence.objects.get(id=document.sentences_ids[0])
        s1model.add_tag(None, 'RESPONSIBILITY', party='them')
        s1model.add_tag(None, 'TERMINATION', party='them')
        s1model.add_tag(None, 'LIABILITY', party='you')

        s2model = Sentence.objects.get(id=document.sentences_ids[1])

        s2model.add_tag(None, 'TERMINATION', party='them')
        s2model.add_tag(None, 'LIABILITY', party='them')
        s2model.add_tag(None, 'NON_STANDARD')

        with mock.patch('portal.mailer.EmailMultiAlternatives') as mock_send_mail:
            BeagleMailer.send_document_digest(self.user, document)
            mock_send_mail.assert_has_calls([mock.call().attach_alternative(mock.ANY, 'text/html')])
            html_email = mock_send_mail.mock_calls[1][1][0]
            self.assertIn('<strong>Liabilities:</strong> 2 clauses', html_email)
            self.assertIn('<strong>Responsibilities:</strong> 1 clauses', html_email)
            self.assertIn('<strong>Terminations:</strong> 2 clauses', html_email)

    @unittest.skip('TODO: Test is not working because annotation is stored in sentences but to_dict uses the cached analysis?')
    @override_settings(CLIENT='WESTPAC')
    def test_simple_client_html(self):
        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document',
                                                 sentences, self.user)

        from core.models import Sentence
        s1model = Sentence.objects.get(id=document.sentences_ids[0])
        s1model.add_tag(None, 'RESPONSIBILITY', party='them')
        s1model.add_tag(None, 'TERMINATION', party='them')
        s1model.add_tag(None, 'LIABILITY', party='you')

        s2model = Sentence.objects.get(id=document.sentences_ids[1])

        s2model.add_tag(None, 'TERMINATION', party='them')
        s2model.add_tag(None, 'LIABILITY', party='them')
        s2model.add_tag(None, 'NON_STANDARD')

        with mock.patch('portal.mailer.EmailMultiAlternatives') as mock_send_mail:
            BeagleMailer.send_document_digest(self.user, document)
            mock_send_mail.assert_has_calls([mock.call().attach_alternative(mock.ANY, 'text/html')])
            html_email = mock_send_mail.mock_calls[1][1][0]
            self.assertIn('<strong>Liabilities:</strong> 2 clauses', html_email)
            self.assertIn('<strong>Responsibilities:</strong> 1 clauses', html_email)
            self.assertIn('<strong>Terminations:</strong> 2 clauses', html_email)


class BeagleMailerTest(BeagleWebTest):
    def test_collaboration_invite(self):
        inviter = self.create_user('inviter_email@gmail.com', 'inviter_username', 'inviter_password',
                                   first_name='inviter_first_name', last_name='inviter_last_name')
        invitee = self.create_user('invitee_email@gmail.com', 'invitee_username', 'invitee_password')
        document = self.create_document('Some Title', self.user, pending=False)
        invite = CollaborationInvite.objects.create(inviter=inviter, invitee=invitee, document=document)

        with mock.patch('portal.mailer.EmailMultiAlternatives') as mock_send_mail:
            BeagleMailer.send_collaboration_invite(invite, 'http://some.url')
            mock_send_mail.assert_has_calls([
                mock.call('Inviter_first_name invited you to collaborate on Beagle.ai', mock.ANY,
                          'Beagle.ai Collaboration Invitation <noreply@beagle.ai>', ['invitee_email@gmail.com']),
                mock.call().attach_alternative(mock.ANY, 'text/html')
            ])

    def test_document_uploaded_via_email_notification(self):
        document = self.create_document('SomeImportantDoc', owner=self.user, pending=False)

        with mock.patch('portal.mailer.Mailer.send') as mock_mailer_send:
            BeagleMailer.document_uploaded_via_email_notification(document)

            mock_mailer_send.assert_called_once_with(to_email=self.DUMMY_EMAIL,
                                                     args={
                                                         'document_title': 'SomeImportantDoc',
                                                         'first_name': self.DUMMY_USERNAME
                                                     },
                                                     from_email=BeagleMailer.DEFAULT_FROM_EMAIL,
                                                     template='email/document_uploaded_via_email.html',
                                                     html_template='email/html/document_uploaded_via_email.html',
                                                     subject='Beagle has received your document and will now process it.')

    def test_document_processing_error_notification(self):
        document = self.create_document('SomeImportantDoc', owner=self.user, pending=False)

        with mock.patch('portal.mailer.Mailer.send') as mock_mailer_send:
            BeagleMailer.document_processing_error_notification(document)

            mock_mailer_send.assert_called_once_with(to_email=self.DUMMY_EMAIL,
                                                     args={
                                                         'first_name': self.DUMMY_USERNAME,
                                                         'document_title': 'SomeImportantDoc'
                                                     },
                                                     from_email=BeagleMailer.DEFAULT_FROM_EMAIL,
                                                     template='email/document_processing_error.html',
                                                     html_template='email/html/document_processing_error.html',
                                                     subject='We\'re having trouble processing your contract')

    def test_unsupported_file_type_error_notification(self):
        with mock.patch('portal.mailer.Mailer.send') as mock_mailer_send:
            BeagleMailer.unsupported_file_type_error_notification(self.user, "Unsupported_Document.doc")

            mock_mailer_send.assert_called_once_with(to_email=self.DUMMY_EMAIL,
                                                     args={
                                                         'first_name': self.DUMMY_USERNAME,
                                                         'title': 'Unsupported_Document.doc'
                                                     },
                                                     from_email=BeagleMailer.DEFAULT_FROM_EMAIL,
                                                     template='email/file_type_error.html',
                                                     html_template='email/html/file_type_error.html',
                                                     subject="We don't support this file type")

    def test_auto_account_creation_notification(self):
        h = OneTimeLoginHash.create(self.user)

        with mock.patch('portal.mailer.Mailer.send') as mock_mailer_send:
            BeagleMailer.auto_account_creation_notification(h)

            mock_mailer_send.assert_called_once_with(to_email=self.DUMMY_EMAIL,
                                                     args={'first_name': self.DUMMY_USERNAME,
                                                           'follow_url': mock.ANY},
                                                     from_email=BeagleMailer.SUPPORT_FROM_EMAIL,
                                                     template='email/auto_account_created.html',
                                                     html_template='email/html/auto_account_created.html',
                                                     subject='Meet Rufus: Your Automatic Contract Guide')

            url = mock_mailer_send.call_args_list[0][1]['args']['follow_url']
            o = urllib.parse.urlparse(url)
            str_hash = dict(urllib.parse.parse_qsl(o.query))['hash']
            hash_model = OneTimeLoginHash.get_onetime_model(str_hash)
            self.assertEqual(hash_model, h)

    def test_notification_reminders(self):
        other_user = self.create_user('ivanov.george.bogdan@gmail.com', 'ivanov.g', 'lambada')
        self.make_paid(other_user)
        document = self.create_document('SomeImportantDoc', owner=self.user, pending=False)
        notif1_pk = store_activity_notification(actor_id=other_user.id,
                                                recipient_id=self.user.id,
                                                verb='did',
                                                target_id=other_user.id,
                                                target_type="User",
                                                action_object_id=document.id,
                                                action_object_type="Document",
                                                render_string="(actor) did something to (target) using (action_object)",
                                                created=datetime.now() - timedelta(minutes=20))

        notif2_pk = store_activity_notification(actor_id=self.user.id,
                                                recipient_id=other_user.id,
                                                verb='did',
                                                target_id=other_user.id,
                                                target_type="User",
                                                action_object_id=document.id,
                                                action_object_type="Document",
                                                render_string="(actor) did something to (target) using (action_object)",
                                                created=datetime.now() - timedelta(minutes=20))

        notif1 = Notification.objects.get(pk=notif1_pk)
        notif2 = Notification.objects.get(pk=notif2_pk)

        with mock.patch('portal.mailer.Mailer.send') as mock_mailer_send:
            BeagleMailer.notification_reminders(other_user, [notif1, notif2])
            mock_mailer_send.assert_called_once_with(to_email='ivanov.george.bogdan@gmail.com',
                                                     args={'account_url': absolutify(reverse('account')),
                                                           'notifications': [
                                                               {'notification_timestamp': mock.ANY,
                                                                'avatar_url': absolutify('/static/img/mug.png'),
                                                                'notification_url': absolutify(reverse('report', kwargs={'uuid': document.uuid})),
                                                                'notification_display': 'ivanov.g did something to ivanov.g using SomeImportantDoc'},
                                                               {'notification_timestamp': mock.ANY,
                                                                'avatar_url': absolutify('/static/img/mug.png'),
                                                                'notification_url': absolutify(reverse('report', kwargs={'uuid': document.uuid})),
                                                                'notification_display': 'dummy_user did something to You using SomeImportantDoc'}],
                                                           'first_name': other_user.username},
                                                     from_email=BeagleMailer.DEFAULT_FROM_EMAIL,
                                                     template='email/notification_reminders.html',
                                                     html_template='email/html/notification_reminders.html',
                                                     subject='You have some notifications on Beagle that may need your attention')
