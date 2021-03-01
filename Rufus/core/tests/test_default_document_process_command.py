import urllib
from collections import namedtuple

# Django
from django.test import TestCase

# Project
from core.api import InternalAPI
from core.commands import DefaultDocumentProcessCommand
from server.models import Detail

# Third Party
from mock import Mock, patch, ANY


MockResponse = namedtuple('MockResponse', ['status_code', 'content'])


class DefaultDocumentProcessCommandTestCase(TestCase):

    def setUp(self):
        self.email_domain = 'LOCAL'
        Detail.objects.get_or_create(
            email_domain=self.email_domain,
            endpoint_protocol='http',
            endpoint_domain='localhost:8000'
        )
        super(DefaultDocumentProcessCommandTestCase, self).setUp()

    def test_api_upload_default_document(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Google  Construction   Agreement'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('core.api.InternalAPI.upload_document') as mock_upload_document:
            command = DefaultDocumentProcessCommand(msg, self.email_domain)
            command.execute()
            mock_upload_document.assert_called_once_with('nobody@gmail.com', {'Google Construction Agreement.txt': ANY})

    def test_api_upload_default_document_requests(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Google  Construction   Agreement'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('core.api.requests.post', return_value=MockResponse(status_code=200, content="{}")) as mock_post:
            command = DefaultDocumentProcessCommand(msg, self.email_domain)
            command.execute()
            api = InternalAPI(self.email_domain)
            mock_post.assert_called_once_with(api.API_ENDPOINT_DOCUMENT_UPLOAD % urllib.quote('nobody@gmail.com'),
                                              files={'Google Construction Agreement.txt': ANY})
