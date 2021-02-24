import StringIO
from django.test import TestCase
from mock import Mock, patch

# App
from core.commands import (
    RufusCommandDispatcher, HelpCommand, SubjectURLProcessCommand,
    DefaultDocumentProcessCommand, AttachmentProcessCommand, BodyProcessCommand,
    DocumentNotFoundAlertCommand, RufusCommand
)
from server.models import Detail

class RufusCommandsTestCase(TestCase):
    def setUp(self):
        self.email_domain = 'LOCAL'
        Detail.objects.get_or_create(
            email_domain=self.email_domain,
            endpoint_protocol='http',
            endpoint_domain='localhost:8000'
        )
        super(RufusCommandsTestCase, self).setUp()

    def test_help_command(self):
        msg = Mock()

        msg.get = Mock(return_value='Help')
        dispatcher = RufusCommandDispatcher(msg, self.email_domain)
        self.assertEqual(dispatcher.select(), HelpCommand)

        msg.get = Mock(return_value='HELP')
        dispatcher = RufusCommandDispatcher(msg, self.email_domain)
        self.assertEqual(dispatcher.select(), HelpCommand)

        msg.get = Mock(return_value='Help!')
        dispatcher = RufusCommandDispatcher(msg, self.email_domain)
        self.assertEqual(dispatcher.select(), HelpCommand)

    def test_subject_url_process_command(self):
        msg = Mock()

        msg.get = Mock(return_value='http://google.com')
        dispatcher = RufusCommandDispatcher(msg, self.email_domain)
        self.assertEqual(dispatcher.select(), SubjectURLProcessCommand)

    def test_default_document_process_command(self):
        msg = Mock()

        msg.get = Mock(return_value='Twitter ToS')
        dispatcher = RufusCommandDispatcher(msg, self.email_domain)
        self.assertEqual(dispatcher.select(), DefaultDocumentProcessCommand)

    @patch('core.commands.get_attachments')
    def test_attachment_process_command(self, mock_get_attachments):
        msg = Mock()

        mock_get_attachments.return_value = {
            'a_document.docx': StringIO.StringIO(),
            'another_document.pdf': StringIO.StringIO(),
        }

        msg.get = Mock(return_value='Hello Rufus')
        dispatcher = RufusCommandDispatcher(msg, self.email_domain)
        self.assertEqual(dispatcher.select(), AttachmentProcessCommand)

    @patch('core.commands.get_body')
    @patch('core.commands.get_attachments')
    def test_body_process_command(self, mock_get_attachments, mock_get_body):
        msg = Mock()

        mock_get_attachments.return_value = {}
        mock_get_body.return_value = 'a' * 300

        msg.get = Mock(return_value='Hello Rufus')
        dispatcher = RufusCommandDispatcher(msg, self.email_domain)
        self.assertEqual(dispatcher.select(), BodyProcessCommand)

    @patch('core.commands.get_body')
    @patch('core.commands.get_attachments')
    def test_document_not_found_alert_command(self, mock_get_attachments, mock_get_body):
        msg = Mock()

        mock_get_attachments.return_value = {}
        mock_get_body.return_value = 'a' * 3

        msg.get = Mock(return_value='Hello Rufus')
        dispatcher = RufusCommandDispatcher(msg, self.email_domain)
        self.assertEqual(dispatcher.select(), DocumentNotFoundAlertCommand)

    def test_user_email_simple(self):
        msg = Mock()
        msg.get = Mock(return_value='something@gmail.com')

        command = RufusCommand(msg, self.email_domain)
        self.assertEqual(command.user_email(), 'something@gmail.com')

    def test_user_email_complex(self):
        msg = Mock()
        msg.get = Mock(return_value='Somebody New <something@gmail.com>')

        command = RufusCommand(msg, self.email_domain)
        self.assertEqual(command.user_email(), 'something@gmail.com')


