import urllib
from collections import namedtuple
from django.test import TestCase
from mock import Mock, patch
from rufus.api import InternalAPI
from rufus.commands import BodyProcessCommand

MockResponse = namedtuple('MockResponse', ['status_code', 'content'])


class SubjectURLProcessCommandTestCase(TestCase):

    def test_api_upload_document(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Document in body'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('rufus.commands.get_body', return_value='*' * 1000) as mock_get_body:
            with patch('rufus.api.InternalAPI.upload_text') as mock_upload_text:
                command = BodyProcessCommand(msg)
                command.execute()
                mock_upload_text.assert_called_once_with('nobody@gmail.com', 'Document in body', '*' * 1000)

    def test_api_upload_requests(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Awesome title'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('rufus.commands.get_body', return_value='*' * 5) as mock_get_body:
            with patch('rufus.api.requests.post', return_value=MockResponse(status_code=200, content="{}")) as mock_post:
                command = BodyProcessCommand(msg)
                command.execute()
                api = InternalAPI()
                mock_post.assert_called_once_with(api.API_ENDPOINT_DOCUMENT_UPLOAD % urllib.quote('nobody@gmail.com'),
                                                  data='{"text": "*****", "title": "Awesome title"}',
                                                  headers={'Content-type': 'application/json'},
                                                  )