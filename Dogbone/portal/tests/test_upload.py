import json
import os
import mock
from django.urls import reverse
from dogbone.testing.base import BeagleWebTest
from core.models import Document


class UploadDocumentTest(BeagleWebTest):
    # Local Tests

    def test_upload_invalid_source(self):
        """
        Test upload invalid source
        """

        self.make_paid(self.user)
        self.login()
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)
        data = {'info': '{"0":{"file":{},"file_name":"","filesource":"INVALID","fileurl":"","accessToken":""}}'}
        response = self.client.post(reverse('upload'), data)
        self.assertEqual(response.status_code, 302)

    def test_failed_local_upload(self):
        """
        Test failing upload
        """
        self.make_paid(self.user)
        self.login()
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        data = {'info': '{"0":{"file":{},"file_name":"","filesource":"local","fileurl":"","accessToken":""}}'}
        response = self.client.post(reverse('upload'), data)
        print(response)
        self.assertEqual(response.status_code, 302)

    # TODO Rewrite test using new functionality
    def test_success_local_upload(self):
        # Out of date
        pass
    # Google Drive Tests
    def test_failed_gdrive_upload(self):
        """
        Test a google drive upload
        """
        self.make_paid(self.user)
        self.login()
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        with mock.patch('core.tasks.process_document_conversion.delay') as mock_process_document_conversion:
            # file from google
            with mock.patch('richtext.importing.requests.get') as mock_get_request:
                data = {'info': '{"0":{"file":{},"file_name":"","filesource":"gdrive","fileurl":"","accessToken":""}}'}
                response = self.client.post(reverse('upload'), data)

                self.assertFalse(mock_get_request.called)
                self.assertFalse(mock_process_document_conversion.called)
                self.assertEqual(response.status_code, 302)

                created_documents = Document.objects.all()

                self.assertEqual(len(created_documents), 0)

    def test_success_gdrive_upload(self):
        """
        Test a google drive upload
        """
        FAKE_URL = 'http://someurl.com/v1/some/fake/endpoint'
        FAKE_ACCESS_TOKEN = 'XXXXX4CC3$$T0K3NXXXXXXX'
        FAKE_FILE_NAME = 'Fake_File.txt'

        self.make_paid(self.user)
        self.login()
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        with mock.patch('core.tasks.process_document_conversion.delay') as mock_process_document_conversion:
            # file from google
            with mock.patch('richtext.importing.requests.get') as mock_get_request:
                with mock.patch('portal.models.update_intercom_document_count.delay') as _:
                    data = {'info': '{"0":{"file":{},"file_name":"'+FAKE_FILE_NAME+'","filesource":"gdrive","fileurl":"'+FAKE_URL+'","accessToken":"'+FAKE_ACCESS_TOKEN+'"}}'}
                    response = self.client.post(reverse('upload'), data)

                    mock_get_request.assert_called_once_with(FAKE_URL, headers={'stream': True,
                                                                                'Authorization': 'Bearer ' + FAKE_ACCESS_TOKEN})

                    created_documents = Document.objects.all()

                    self.assertEqual(len(created_documents), 1)
                    document = created_documents[0]

                    mock_process_document_conversion.assert_called_once_with(document.pk, mock.ANY, True)

                    self.assertEqual(response.status_code, 200)

    # Url Tests (From Dropbox)
    def test_upload_url_plaintext(self):
        """
        Test url .txt file
        """
        FAKE_FILE_URL = "http://someurl.com/somefile.txt"

        self.make_paid(self.user)
        self.login()
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        with mock.patch('richtext.importing.requests.get') as mock_get_request:
            with mock.patch('portal.models.update_intercom_document_count.delay') as _:
                data = {'info': '{"0":{"file":{},"file_name":"","filesource":"url","fileurl":"'+FAKE_FILE_URL+'","accessToken":""}}'}
                self.client.post(reverse('upload'), data)
                mock_get_request.assert_called_once_with(FAKE_FILE_URL, stream=True)

DOC_PREFIX = 'portal/test_documents'
files = [path for path in os.listdir(DOC_PREFIX) if not path.startswith('.')]


# TODO Rewrite test using new functionality
# Out of date
# class TestSequenceMeta(type):
#     def __new__(mcs, name, bases, dict):
#
#         def gen_test(abs_filename):
#             def test(self):
#                 self.login()
#                 response = self.client.get(reverse('upload_file'))
#                 self.assertEqual(response.status_code, 200)
#                 response = self.client.post(reverse('upload'), {
#                     'filesource': 'local',
#                     'file': open(abs_filename, 'r')
#                 }, follow=True)
#                 self.assertEqual(response.status_code, 200)
#             return test
#
#         for rel_path in files:
#             abs_filename = os.path.abspath(DOC_PREFIX+'/'+rel_path)
#             test_name = 'test_'+os.path.basename(abs_filename) \
#                                        .replace('.', '_') \
#                                        .replace(' ', '_').lower()
#             dict[test_name] = gen_test(abs_filename)
#         return type.__new__(mcs, name, bases, dict)
#
# class TestSequence(BeagleWebTest):
#     __metaclass__ = TestSequenceMeta
