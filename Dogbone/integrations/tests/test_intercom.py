from django.contrib.auth.models import User
import intercom
import mock

from dogbone.testing.base import BeagleWebTest
from integrations.tasks import (
    update_intercom_document_count,
    update_intercom_custom_attribute,
    log_intercom_custom_event,
)
from portal.tasks import send_intercom_inapp_message


class IntercomTest(BeagleWebTest):

    def test_send_intercom_inapp_message(self):
        with mock.patch('integrations.intercom_api.requests.post') as mock_post:
            send_intercom_inapp_message(from_id=1234, to_email='aaa@bbb.com', message='aaa123456')

            mock_post.assert_called_with('https://api.intercom.io/messages',
                                         headers={'Accept': 'application/json'},
                                         json={'body': 'aaa123456', 'from': {'type': 'admin', 'id': '1234'},
                                               'message_type': 'inapp', 'to': {'type': 'user', 'email': 'aaa@bbb.com'}},
                                         auth=mock.ANY)

    @mock.patch('integrations.tasks.IntercomUser.save')
    @mock.patch('integrations.tasks.IntercomUser.find')
    def test_document_count_update(self, mock_find, mock_save):
        mock_find.return_value = intercom.User()
        update_intercom_document_count(self.user.email)
        mock_save.assert_called_once()

    @mock.patch('integrations.tasks.IntercomUser.save')
    @mock.patch('integrations.tasks.IntercomUser.find')
    def test_document_count_update_no_intercom_user_found(self, mock_find, mock_save):
        mock_find.side_effect = intercom.HttpError()
        update_intercom_document_count(self.user.email)
        self.assertFalse(mock_save.called)

    @mock.patch('integrations.tasks.IntercomUser.save')
    @mock.patch('integrations.tasks.IntercomUser.find')
    def test_document_count_update_no_beagle_user_found(self, mock_find, mock_save):
        update_intercom_document_count.side_effect = User.DoesNotExist()
        update_intercom_document_count(self.user.email)
        self.assertFalse(mock_save.called)

    @mock.patch('integrations.tasks.IntercomEvent.create')
    def test_log_intercom_custom_event(self, mock_event):
        example_metadata = {"example" : "test"}
        example_event = "Example Event"
        example_created_at = 1450699200

        success = log_intercom_custom_event(self.user.email, example_event, example_metadata, example_created_at)
        mock_event.assert_called_once()
        self.assertTrue(success)

    @mock.patch('integrations.tasks.IntercomEvent.create')
    def test_log_intercom_custom_event_no_metadata(self, mock_event):
        example_event = "Example Event"

        success = log_intercom_custom_event(self.user.email, example_event)
        mock_event.assert_called_once()
        self.assertTrue(success)

    @mock.patch('integrations.tasks.IntercomEvent.create')
    def test_log_intercom_custom_event_no_created_at(self, mock_event):
        example_metadata = {"example" : "test"}
        example_event = "Example Event"

        success = log_intercom_custom_event(self.user.email, example_event, example_metadata)
        mock_event.assert_called_once()
        self.assertTrue(success)

    @mock.patch('integrations.tasks.IntercomEvent.create')
    def test_log_intercom_custom_event_no_intercom_user_found(self, mock_event):
        example_metadata = {"example" : "test"}
        example_event = "Example Event"

        mock_event.side_effect = intercom.ResourceNotFound()
        success = log_intercom_custom_event(self.user.email, example_event, example_metadata)
        self.assertFalse(success)

    @mock.patch('integrations.tasks.IntercomUser.save')
    @mock.patch('integrations.tasks.IntercomUser.find')
    def test_update_intercom_custom_attribute(self, mock_find, mock_save):
        mock_custom_attribute_name = "test-count"
        mock_custom_attribute_value = 32

        mock_find.return_value = intercom.User()
        update_intercom_custom_attribute(self.user.email, mock_custom_attribute_name, mock_custom_attribute_value)
        mock_save.assert_called_once()

    @mock.patch('integrations.tasks.IntercomUser.save')
    @mock.patch('integrations.tasks.IntercomUser.find')
    def test_update_intercom_custom_attribute_no_intercom_user_found(self, mock_find, mock_save):
        mock_custom_attribute_name = "test-count"
        mock_custom_attribute_value = 32

        mock_find.side_effect = intercom.HttpError()
        update_intercom_custom_attribute(self.user.email, mock_custom_attribute_name, mock_custom_attribute_value)
        self.assertFalse(mock_save.called)
