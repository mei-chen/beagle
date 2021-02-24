import os
import json
import email

# Django
from django.test import TestCase, override_settings

# Project
from core.process_mail import main
from core.process_mail import call_main
from core.tests.base import  MockResponse
from server.models import Detail

# Third Party
import mock


@override_settings(DEFAULT_FILE_STORAGE='inmemorystorage.InMemoryStorage')
class RufusTestCase(TestCase):
    def setUp(self):
        self.CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
        self.TEST_EMAIL_FOLDER = os.path.join(self.CURRENT_FOLDER, 'test_emails')
        self.EMAIL_FILENAME = 'test.email'
        self.INVALID_FROM_EMAIL_FILENAME = 'invalid_from.email'
        self.PPTX_ATTACHED_AS_TEST_EMAIL_FILENAME = 'pptx_text_file.email'

        Detail.objects.get_or_create(
            email_domain='LOCAL',
            endpoint_protocol='http',
            endpoint_domain='localhost:8000'
        )
        super(RufusTestCase, self).setUp()

    def test_main_call(self):
        """
        Test how the main routine is being called inside process_mail.py
        :return:
        """
        with open(os.path.join(self.TEST_EMAIL_FOLDER, self.EMAIL_FILENAME), 'r') as input_email:
            email_content = input_email.read()

            with mock.patch('core.process_mail.get_module_name', return_value='__main__'):
                with mock.patch('core.process_mail.read_input', return_value=email_content):
                    with mock.patch('core.process_mail.main') as mock_main:
                        call_main()
                        mock_main.assert_called_once_with(mock.ANY, 'TEST')




    def test_paid(self):
        def mocked_requests_get(*args, **kwargs):
            if args[0] == 'http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com':
                return MockResponse(json.dumps({'is_paid': True, 'had_trial': True}), 200)
            return MockResponse("404", 404)

        def mocked_requests_post(*args, **kwargs):
            if args[0] == 'http://localhost:8000/api/v1/_internal/document/upload?from=bogdan.semantickle%2Ba3%40gmail.com&send_upload_via_email=true':
                return MockResponse(json.dumps({}), 200)
            elif args[0] == 'http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com/subscription/ALL_ACCESS_TRIAL':
                return MockResponse(json.dumps({}), 200)

        with open(os.path.join(self.TEST_EMAIL_FOLDER, self.EMAIL_FILENAME), 'r') as input_email:
            email_content = input_email.read()
            msg = email.message_from_string(email_content)
            with mock.patch('core.api.requests.get', side_effect=mocked_requests_get) as mock_get:
                with mock.patch('core.api.requests.post', side_effect=mocked_requests_post) as mock_post:
                    main(msg, 'LOCAL', 'email content mock')
                    mock_get.assert_called_with('http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com')

                    mock_post.assert_called_with('http://localhost:8000/api/v1/_internal/document/upload?from=bogdan.semantickle%2Ba3%40gmail.com&send_upload_via_email=true', files=mock.ANY)

    def test_not_paid_no_trial(self):
        def mocked_requests_get(*args, **kwargs):
            if args[0] == 'http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com':
                return MockResponse(json.dumps({'is_paid': False, 'had_trial': False}), 200)
            return MockResponse("404", 404)

        def mocked_requests_post(*args, **kwargs):
            if args[0] == 'http://localhost:8000/api/v1/_internal/document/upload?from=bogdan.semantickle%2Ba3%40gmail.com&send_upload_via_email=true':
                return MockResponse(json.dumps({}), 200)
            elif args[0] == 'http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com/subscription/ALL_ACCESS_TRIAL':
                return MockResponse(json.dumps({}), 200)

        with open(os.path.join(self.TEST_EMAIL_FOLDER, self.EMAIL_FILENAME), 'r') as input_email:
            email_content = input_email.read()
            msg = email.message_from_string(email_content)
            with mock.patch('core.api.requests.get', side_effect=mocked_requests_get) as mock_get:
                with mock.patch('core.api.requests.post', side_effect=mocked_requests_post) as mock_post:
                    main(msg, 'LOCAL', 'email content mock')
                    mock_get.assert_called_with('http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com')

                    self.assertEqual(mock_post.mock_calls, [
                        mock.call('http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com/subscription/ALL_ACCESS_TRIAL'),
                        mock.call('http://localhost:8000/api/v1/_internal/document/upload?from=bogdan.semantickle%2Ba3%40gmail.com&send_upload_via_email=true', files={'Dropbox Terms of Service.txt': mock.ANY})])

    def test_not_paid_had_trial(self):
        def mocked_requests_get(*args, **kwargs):
            if args[0] == 'http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com':
                return MockResponse(json.dumps({'is_paid': False, 'had_trial': True}), 200)
            return MockResponse("404", 404)

        def mocked_requests_post(*args, **kwargs):
            if args[0] == 'http://localhost:8000/api/v1/_internal/document/upload?from=bogdan.semantickle%2Ba3%40gmail.com&send_upload_via_email=true':
                return MockResponse(json.dumps({}), 200)

        with open(os.path.join(self.TEST_EMAIL_FOLDER, self.EMAIL_FILENAME), 'r') as input_email:
            email_content = input_email.read()
            msg = email.message_from_string(email_content)
            with mock.patch('core.api.requests.get', side_effect=mocked_requests_get) as mock_get:
                with mock.patch('core.api.requests.post', side_effect=mocked_requests_post) as mock_post:
                    main(msg, 'LOCAL', 'email content mock')
                    mock_get.assert_called_with('http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com')

                    # For now, we upload the document for everyone.
                    mock_post.assert_called_with('http://localhost:8000/api/v1/_internal/document/upload?from=bogdan.semantickle%2Ba3%40gmail.com&send_upload_via_email=true', files=mock.ANY)

    def test_invalid_from(self):
        with open(os.path.join(self.TEST_EMAIL_FOLDER, self.INVALID_FROM_EMAIL_FILENAME), 'r') as input_email:
            email_content = input_email.read()
            msg = email.message_from_string(email_content)
            with mock.patch('core.api.requests.get') as mock_get:
                with mock.patch('core.api.requests.post') as mock_post:
                    main(msg, 'LOCAL', 'email content mock')
                    self.assertFalse(mock_get.called)
                    self.assertFalse(mock_post.called)

    def test_pptx_attached(self):
        def mocked_requests_get(*args, **kwargs):
            if args[0] == 'http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com':
                return MockResponse(json.dumps({'is_paid': True, 'had_trial': True}), 200)
            return MockResponse("404", 404)

        def mocked_requests_post(*args, **kwargs):
            if args[0] == 'http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com/notify/attachments_not_found':
                return MockResponse(json.dumps({'success': True}), 200)

        with open(os.path.join(self.TEST_EMAIL_FOLDER, self.PPTX_ATTACHED_AS_TEST_EMAIL_FILENAME), 'r') as input_email:
            email_content = input_email.read()
            msg = email.message_from_string(email_content)
            with mock.patch('core.api.requests.get', side_effect=mocked_requests_get) as mock_get:
                with mock.patch('core.api.requests.post', side_effect=mocked_requests_post) as mock_post:
                    main(msg, 'LOCAL', 'email content mock')

                    mock_get.assert_called_with('http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com')
                    self.assertEqual(mock_post.mock_calls, [mock.call('http://localhost:8000/api/v1/_internal/user/bogdan.semantickle%2Ba3%40gmail.com/notify/attachments_not_found', headers={'Content-type': 'application/json'})])
