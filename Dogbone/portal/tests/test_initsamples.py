import mock
from unittest import skip
from django.test import TestCase
from django.contrib.auth.models import User
from core.tools import init_sample_docs
from core.tasks import initialize_sample_docs
from core.models import Document


class InitSamplesTest(TestCase):

    def test_celery_task_called(self):
        """ Checks that the celery task that inits the sample docs is called """
        with mock.patch('core.tasks.initialize_sample_docs.delay') as mock_task:
            user = User.objects.create(username='Tester1')
            mock_task.assert_called_once_with(user)

    # TODO: unskip this when we add initial samples back
    @skip('No docs to test on at the moment')
    def test_db_models_generated(self):
        """ Checks that the sample docs are created """
        # Create a user with init-samples creation task mocked so it won't run
        with mock.patch('core.tasks.initialize_sample_docs.delay'):
            user = User.objects.create(username='Tester2')

        # Don't try to update HubSpot document count
        with mock.patch('integrations.hubspot.HubspotAPI.get_contact_vid') as mock_submit_form:
            mock_submit_form.return_value = None
            # Now manually call the task synchronously
            with mock.patch('core.tasks.process_document_conversion.delay') as mock_conversion:
                with mock.patch('core.tasks.BeagleMailer.document_complete_notification') as mock_email_notify:
                    sample_docs = init_sample_docs()

                    initialize_sample_docs(user)
                    self.assertEquals(len(sample_docs), len(Document.objects.filter(owner=user)))

                    self.assertEqual(mock_conversion.call_args_list, [
                        mock.call(mock.ANY, mock.ANY, send_emails=False, send_notifications=True),
                        mock.call(mock.ANY, mock.ANY, send_emails=False, send_notifications=True)])

                    self.assertFalse(mock_email_notify.called)
