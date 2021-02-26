import urllib
from collections import namedtuple
from django.test import TestCase
from mock import Mock, patch, ANY
from rufus.api import InternalAPI
from rufus.commands import DefaultDocumentProcessCommand

MockResponse = namedtuple('MockResponse', ['status_code', 'content'])


class DefaultDocumentProcessCommandTestCase(TestCase):

    def test_api_upload_default_document(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Google  Construction   Agreement'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('rufus.api.InternalAPI.upload_document') as mock_upload_document:
            command = DefaultDocumentProcessCommand(msg)
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

        with patch('rufus.api.requests.post', return_value=MockResponse(status_code=200, content="{}")) as mock_post:
            command = DefaultDocumentProcessCommand(msg)
            command.execute()
            api = InternalAPI()
            mock_post.assert_called_once_with(api.API_ENDPOINT_DOCUMENT_UPLOAD % urllib.quote('nobody@gmail.com'),
                                              files={'Google Construction Agreement.txt': ANY})