import urllib
from collections import namedtuple
from django.test import TestCase
from mock import Mock, patch
from rufus.api import InternalAPI
from rufus.commands import DocumentNotFoundAlertCommand

MockResponse = namedtuple('MockResponse', ['status_code', 'content'])


class DocumentNotFoundAlertCommandTestCase(TestCase):

    def test_api_alert_not_found(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Some Subject ... nothing to see here ... move along ...'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('rufus.api.InternalAPI.send_attachments_not_found') as mock_send_attachments_not_found:
            command = DocumentNotFoundAlertCommand(msg)
            command.execute()
            mock_send_attachments_not_found.assert_called_once_with('nobody@gmail.com')

    def test_api_alert_not_found_requests_post(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Awesome title'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('rufus.api.requests.post', return_value=MockResponse(status_code=200, content="{}")) as mock_post:
            command = DocumentNotFoundAlertCommand(msg)
            command.execute()
            api = InternalAPI()
            mock_post.assert_called_once_with(api.API_SEND_ATTACHMENTS_NOT_FOUND_NOTIFICATION % urllib.quote('nobody@gmail.com'),
                                              headers={'Content-type': 'application/json'},
                                              )