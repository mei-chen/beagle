import urllib
from collections import namedtuple

# Django
from django.test import TestCase

# Project
from core.api import InternalAPI
from core.commands import DocumentNotFoundAlertCommand
from server.models import Detail

# Third Party
from mock import Mock, patch

MockResponse = namedtuple('MockResponse', ['status_code', 'content'])


class DocumentNotFoundAlertCommandTestCase(TestCase):
    def setUp(self):
        self.email_domain = 'LOCAL'
        Detail.objects.get_or_create(
            email_domain=self.email_domain,
            endpoint_protocol='http',
            endpoint_domain='localhost:8000'
        )
        super(DocumentNotFoundAlertCommandTestCase, self).setUp()


    def test_api_alert_not_found(self):
        msg = Mock()

        def mocked_message_get(*args, **kwargs):
            if args[0] == 'From':
                return 'Somebody New <nobody@gmail.com>'
            elif args[0] == 'Subject':
                return 'Some Subject ... nothing to see here ... move along ...'

        msg.get = Mock(side_effect=mocked_message_get)

        with patch('core.api.InternalAPI.send_attachments_not_found') as mock_send_attachments_not_found:
            command = DocumentNotFoundAlertCommand(msg, self.email_domain)
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

        with patch('core.api.requests.post', return_value=MockResponse(status_code=200, content="{}")) as mock_post:
            command = DocumentNotFoundAlertCommand(msg, self.email_domain)
            command.execute()
            api = InternalAPI(self.email_domain)
            mock_post.assert_called_once_with(api.API_SEND_ATTACHMENTS_NOT_FOUND_NOTIFICATION % urllib.quote('nobody@gmail.com'),
                                              headers={'Content-type': 'application/json'},
                                              )
