import urllib
from collections import namedtuple
from django.test import TestCase
from mock import Mock, patch
from rufus.api import InternalAPI
from rufus.commands import HelpCommand

MockResponse = namedtuple('MockResponse', ['status_code', 'content'])


class HelpCommandTestCase(TestCase):

    def test_api_help(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'HELP'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('rufus.api.InternalAPI.send_help_notification') as mock_send_help_notification:
            command = HelpCommand(msg)
            command.execute()
            mock_send_help_notification.assert_called_once_with('nobody@gmail.com')

    def test_api_help_requests_post(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Awesome title'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('rufus.api.requests.post', return_value=MockResponse(status_code=200, content="{}")) as mock_post:
            command = HelpCommand(msg)
            command.execute()
            api = InternalAPI()
            mock_post.assert_called_once_with(api.API_SEND_HELP_NOTIFICATION % urllib.quote('nobody@gmail.com'),
                                              headers={'Content-type': 'application/json'},
                                              )