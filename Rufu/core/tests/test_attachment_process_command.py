import urllib
import StringIO
from collections import namedtuple

# Django
from django.test import TestCase

# Project
from core.api import InternalAPI
from core.commands import AttachmentProcessCommand
from server.models import Detail

# Third Party
from mock import Mock, patch, ANY


MockResponse = namedtuple('MockResponse', ['status_code', 'content'])


class AttachmentProcessCommandTestCase(TestCase):
    def setUp(self):
        self.email_domain = 'LOCAL'
        Detail.objects.get_or_create(
            email_domain=self.email_domain,
            endpoint_protocol='http',
            endpoint_domain='localhost:8000'
        )
        super(AttachmentProcessCommandTestCase, self).setUp()

    def test_api_upload_document(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Hello Rufus!'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('core.commands.get_attachments', return_value={'A_document.txt': StringIO.StringIO()}):
            with patch('core.api.InternalAPI.upload_document') as mock_upload_document:
                command = AttachmentProcessCommand(msg, self.email_domain)
                command.execute()
                mock_upload_document.assert_called_once_with('nobody@gmail.com', {'A_document.txt': ANY})

    def test_api_upload_document_multiple(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Hello Rufus!'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('core.commands.get_attachments',
                   return_value={'A_document.txt': StringIO.StringIO(), 'B_document.docx': StringIO.StringIO()}):
            with patch('core.api.InternalAPI.upload_document') as mock_upload_document:
                command = AttachmentProcessCommand(msg, self.email_domain)
                command.execute()
                mock_upload_document.assert_called_once_with('nobody@gmail.com', {'A_document.txt': ANY,
                                                                                  'B_document.docx': ANY})

    def test_api_upload_requests(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Hello Rufus!'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('core.commands.get_attachments',
                   return_value={'A_document.txt': StringIO.StringIO(), 'B_document.docx': StringIO.StringIO()}):
            with patch('core.api.requests.post', return_value=MockResponse(status_code=200, content="{}")) as mock_post:
                command = AttachmentProcessCommand(msg, self.email_domain)
                command.execute()
                api = InternalAPI(self.email_domain)
                mock_post.assert_called_once_with(api.API_ENDPOINT_DOCUMENT_UPLOAD % urllib.quote('nobody@gmail.com'),
                                                  files={'B_document.docx': ANY, 'A_document.txt': ANY})
