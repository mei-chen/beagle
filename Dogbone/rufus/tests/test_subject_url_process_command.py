import urllib
import StringIO
from collections import namedtuple
from django.test import TestCase
from mock import Mock, patch
from rufus.api import InternalAPI
from rufus.commands import SubjectURLProcessCommand

MockResponse = namedtuple('MockResponse', ['status_code', 'content'])


class SubjectURLProcessCommandTestCase(TestCase):

    def test_api_upload_document(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'http://apple.com/terms'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('rufus.api.InternalAPI.upload_url') as mock_upload_url:
            command = SubjectURLProcessCommand(msg)
            command.execute()
            mock_upload_url.assert_called_once_with('nobody@gmail.com', 'http://apple.com/terms')

    def test_api_upload_requests(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'http://apple.com/terms'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('rufus.commands.get_attachments',
                   return_value={'A_document.txt': StringIO.StringIO(), 'B_document.docx': StringIO.StringIO()}):
            with patch('rufus.api.requests.post', return_value=MockResponse(status_code=200, content="{}")) as mock_post:
                command = SubjectURLProcessCommand(msg)
                command.execute()
                api = InternalAPI()
                mock_post.assert_called_once_with(api.API_ENDPOINT_DOCUMENT_UPLOAD % urllib.quote('nobody@gmail.com'),
                                                  data='{"url": "http://apple.com/terms"}',
                                                  headers={'Content-type': 'application/json'},
                                                  )