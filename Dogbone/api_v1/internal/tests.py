# -*- coding: utf-8 -*-
import json
import mock
import uuid
import tempfile

from django.urls import reverse
from django.contrib.auth.models import User

from dogbone.testing.base import BeagleWebTest
from core.models import Document
from authentication.models import OneTimeLoginHash
from marketing.models import PurchasedSubscription


class InternalUserDetailViewTestCase(BeagleWebTest):

    def test_200_username(self):
        user = self.create_user('myemail@yahoo.com', 'gigi-tarnac0p_A', 'p@ss')
        api_url = reverse('internal_user_detail_view', kwargs={'identifier': user.username})

        response = self.client.get(api_url, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            "avatar": "/static/img/mug.png",
            "company": None,
            "date_joined": mock.ANY,
            "email": user.email,
            "first_name": None,
            "is_paid": False,
            "had_trial": mock.ANY,
            "is_super": False,
            "job_title": None,
            "tags": mock.ANY,
            "keywords": mock.ANY,
            "settings": mock.ANY,
            "last_login": mock.ANY,
            "last_name": None,
            "username": user.username,
            "id": mock.ANY,
            "pending": False,
            "document_upload_count": 0,
            'phone': None,
        })

    def test_200_email(self):
        user = self.create_user('myemail@yahoo.com', 'gigi-tarnac0p_A', 'p@ss')
        api_url = reverse('internal_user_detail_view', kwargs={'identifier': user.email})

        response = self.client.get(api_url, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            "avatar": "/static/img/mug.png",
            "company": None,
            "date_joined": mock.ANY,
            "email": user.email,
            "first_name": None,
            "is_paid": False,
            "had_trial": mock.ANY,
            "is_super": False,
            "job_title": None,
            "tags": mock.ANY,
            "keywords": mock.ANY,
            "settings": mock.ANY,
            "last_login": mock.ANY,
            "last_name": None,
            "username": user.username,
            "id": mock.ANY,
            "pending": False,
            "document_upload_count": 0,
            "phone": None,
        })

    def test_200_id(self):
        user = self.create_user('myemail@yahoo.com', 'gigi-tarnac0p_A', 'p@ss')
        api_url = reverse('internal_user_detail_view', kwargs={'identifier': user.pk})

        response = self.client.get(api_url, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            "avatar": "/static/img/mug.png",
            "company": None,
            "date_joined": mock.ANY,
            "email": user.email,
            "first_name": None,
            "is_paid": False,
            "had_trial": mock.ANY,
            "is_super": False,
            "job_title": None,
            "tags": mock.ANY,
            "keywords": mock.ANY,
            "settings": mock.ANY,
            "last_login": mock.ANY,
            "last_name": None,
            "username": user.username,
            "id": mock.ANY,
            "pending": False,
            "document_upload_count": 0,
            "phone": None,
        })

    def test_not_internal(self):
        api_url = reverse('internal_user_detail_view', kwargs={'identifier': self.DUMMY_USERNAME})

        response = self.client.get(api_url, REMOTE_ADDR='220.10.44.1')
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Protected Endpoint',
                                'code': None,
                                'type': 'error',
                                'http_status': 403})

    def test404(self):
        self.login()
        api_url = reverse('internal_user_detail_view', kwargs={'identifier': 'Not_Found'})

        response = self.client.get(api_url, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'This username does not exist',
                                'code': None,
                                'type': 'error',
                                'http_status': 404})


class InternalUserListViewTestCase(BeagleWebTest):
    def test_post(self):
        with mock.patch('portal.tasks.hubspot_update_contact_properties.delay') as mock_hs_update:
            data = {
                'email': 'non.existing@email.com',
                'first_name': 'Some FN',
                'last_name': 'Some LN',
                'job_title': 'Professional hand model',
                'company': 'Hand Modelling Inc.',
                'phone': '555-555-5555',
                'password': 'p@ss',
            }

            api_url = reverse('internal_user_list_view')
            response = self.client.post(api_url, data=json.dumps(data),
                                        content_type='application/json',
                                        REMOTE_ADDR='127.0.0.1')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.content)

            self.assertEqual(data, [{'id': mock.ANY,
                                     'pending': False,
                                     'username': 'non.existing@email.com',
                                     'first_name': 'Some FN',
                                     'last_name': 'Some LN',
                                     'is_super': False,
                                     'is_paid': False,
                                     'had_trial': mock.ANY,
                                     'company': 'Hand Modelling Inc.',
                                     'tags': [],
                                     'keywords': [],
                                     'settings': mock.ANY,
                                     'last_login': mock.ANY,
                                     'avatar': '/static/img/mug.png',
                                     'job_title': 'Professional hand model',
                                     'email': 'non.existing@email.com',
                                     'date_joined': mock.ANY,
                                     "document_upload_count": 0,
                                     'phone': '555-555-5555'}])

            user = User.objects.get(username='non.existing@email.com')
            self.assertTrue(user.check_password('p@ss'))

            self.assertEqual(user.last_name, 'Some LN')
            self.assertEqual(user.first_name, 'Some FN')
            self.assertEqual(user.details.phone, '555-555-5555')
            self.assertEqual(user.details.company, 'Hand Modelling Inc.')
            self.assertEqual(user.details.job_title, 'Professional hand model')

            #check for HS update calls
            self.assertTrue(mock_hs_update.called)

    def test_post_with_send_auto_create(self):
        with mock.patch('portal.tasks.hubspot_update_contact_properties.delay') as _:
            data = {
                'email': 'non.existing@email.com',
                'first_name': 'Some FN',
                'last_name': 'Some LN',
                'job_title': 'Professional hand model',
                'company': 'Hand Modelling Inc.',
                'phone': '555-555-5555',
                'password': 'p@ss',
            }

            api_url = reverse('internal_user_list_view') + '?send_auto_create=true'

            # Check there are no Hashes created already
            self.assertEqual(OneTimeLoginHash.objects.all().count(), 0)

            with mock.patch('core.tasks.send_auto_account_created_notification.delay') as mock_send_auto_account_created_notification:

                response = self.client.post(api_url, data=json.dumps(data),
                                            content_type='application/json',
                                            REMOTE_ADDR='127.0.0.1')
                self.assertEqual(response.status_code, 200)
                user = User.objects.get(username='non.existing@email.com')
                h = OneTimeLoginHash.objects.get(user=user)

    def test_post_with_username(self):
        with mock.patch('portal.tasks.hubspot_update_contact_properties.delay') as mock_hs_update:
            data = {
                'email': 'non.existing@email.com',
                'first_name': 'Some FN',
                'last_name': 'Some LN',
                'job_title': 'Professional hand model',
                'company': 'Hand Modelling Inc.',
                'phone': '555-555-5555',
                'password': 'p@ss',
                'username': 'myname'
            }

            api_url = reverse('internal_user_list_view')
            response = self.client.post(api_url, data=json.dumps(data),
                                        content_type='application/json',
                                        REMOTE_ADDR='127.0.0.1')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.content)

            self.assertEqual(data, [{'id': mock.ANY,
                                     'pending': False,
                                     'username': 'myname',
                                     'first_name': 'Some FN',
                                     'last_name': 'Some LN',
                                     'is_super': False,
                                     'is_paid': False,
                                     'had_trial': mock.ANY,
                                     'company': 'Hand Modelling Inc.',
                                     'tags': [],
                                     'keywords': [],
                                     'settings': mock.ANY,
                                     'last_login': mock.ANY,
                                     'avatar': '/static/img/mug.png',
                                     'job_title': 'Professional hand model',
                                     'email': 'non.existing@email.com',
                                     'date_joined': mock.ANY,
                                     "document_upload_count": 0,
                                     'phone': '555-555-5555'}])

            user = User.objects.get(username='myname')
            self.assertTrue(user.check_password('p@ss'))

            self.assertEqual(user.last_name, 'Some LN')
            self.assertEqual(user.first_name, 'Some FN')
            self.assertEqual(user.details.phone, '555-555-5555')
            self.assertEqual(user.details.company, 'Hand Modelling Inc.')
            self.assertEqual(user.details.job_title, 'Professional hand model')

            #check for HS update calls
            self.assertTrue(mock_hs_update.called)

    def test_post_without_email(self):
        data = {
            'first_name': 'Some FN',
            'last_name': 'Some LN',
            'job_title': 'Professional hand model',
            'company': 'Hand Modelling Inc.',
            'phone': '555-555-5555',
            'password': 'p@ss',
            'username': 'myname'
        }

        api_url = reverse('internal_user_list_view')
        response = self.client.post(api_url, data=json.dumps(data),
                                    content_type='application/json',
                                    REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(User.objects.filter(username='myname').count(), 0)

    def test_post_without_password(self):
        data = {
            'first_name': 'Some FN',
            'last_name': 'Some LN',
            'job_title': 'Professional hand model',
            'company': 'Hand Modelling Inc.',
            'phone': '555-555-5555',
            'username': 'myname',
            'email': 'myemail@email.com'
        }

        api_url = reverse('internal_user_list_view')
        response = self.client.post(api_url, data=json.dumps(data),
                                    content_type='application/json',
                                    REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(User.objects.filter(username='myname').count(), 1)

    def test_post_existing_email(self):
        with mock.patch('portal.tasks.hubspot_update_contact_properties.delay') as mock_hs_update:
            data = {
                'email': 'non.existing@email.com',
                'first_name': 'Some FN',
                'last_name': 'Some LN',
                'job_title': 'Professional hand model',
                'company': 'Hand Modelling Inc.',
                'phone': '555-555-5555',
                'password': 'p@ss',
                'username': 'myname'
            }

            api_url = reverse('internal_user_list_view')
            response = self.client.post(api_url, data=json.dumps(data), content_type='application/json',
                                        REMOTE_ADDR='127.0.0.1')
            self.assertEqual(response.status_code, 200)

            response = self.client.post(api_url, data=json.dumps(data), content_type='application/json',
                                        REMOTE_ADDR='127.0.0.1')
            self.assertEqual(response.status_code, 400)

    def test_post_external_ip(self):
        with mock.patch('portal.tasks.hubspot_update_contact_properties.delay') as mock_hs_update:
            data = {
                'email': 'non.existing@email.com',
                'first_name': 'Some FN',
                'last_name': 'Some LN',
                'job_title': 'Professional hand model',
                'company': 'Hand Modelling Inc.',
                'phone': '555-555-5555',
                'password': 'p@ss',
                'username': 'myname'
            }

            api_url = reverse('internal_user_list_view')
            response = self.client.post(api_url, data=json.dumps(data), content_type='application/json',
                                        REMOTE_ADDR='220.220.220.220')
            self.assertEqual(response.status_code, 403)
            data = json.loads(response.content)

            self.assertEqual(data, {'code': None,
                                    'http_status': 403,
                                    'message': 'Protected Endpoint',
                                    'type': 'error'})


class InternalDocumentUploadComputeViewTestCase(BeagleWebTest):

    API_URL = reverse('internal_document_upload_compute_view')

    def test_get(self):
        self.assertEqual(self.client.get(self.API_URL + '?from=%s' % self.DUMMY_EMAIL, REMOTE_ADDR='127.0.0.1').status_code, 403)

    # TODO: example.com broken
    def test_post_url(self):
        data = {'url': 'http://example.com'}

        ARTICLE_TEXT = "This is a huge responsibility. Treat it as such!"
        ARTICLE_TITLE = "This is the title"

        self.assertEqual(len(Document.objects.all()), 0)

        with mock.patch('api_v1.document.endpoints.Article') as MockArticle:
            with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                type(MockArticle.return_value).text = mock.PropertyMock(return_value=ARTICLE_TEXT)
                type(MockArticle.return_value).title = mock.PropertyMock(return_value=ARTICLE_TITLE)
                response = self.client.post(self.API_URL + '?from=%s' % self.DUMMY_EMAIL, data=json.dumps(data),
                                            content_type='application/json',
                                            REMOTE_ADDR='127.0.0.1')

                self.assertEqual(len(Document.objects.all()), 1)
                document = Document.objects.all()[0]
                data = json.loads(response.content)

                self.assertEqual(data, {
                    "collaborators": [],
                    "created": mock.ANY,
                    "original_name": "This+is+the+title.txt",
                    "owner": {
                        "avatar": "/static/img/mug.png",
                        "company": None,
                        "date_joined": mock.ANY,
                        "document_upload_count": 1,
                        "email": self.DUMMY_EMAIL,
                        "first_name": None,
                        "had_trial": False,
                        "id": mock.ANY,
                        "is_paid": False,
                        "is_super": False,
                        "job_title": None,
                        "last_login": mock.ANY,
                        "last_name": None,
                        "pending": False,
                        "phone": None,
                        "tags": [],
                        "keywords": [],
                        "settings": mock.ANY,
                        "username": self.DUMMY_USERNAME
                    },
                    "report_url": "/report/%s" % document.uuid,
                    "title": ARTICLE_TITLE,
                    "url": "/api/v1/document/%s" % document.uuid,
                    "is_initsample": False,
                    "agreement_type": mock.ANY,
                    "agreement_type_confidence": mock.ANY,
                    "uuid": document.uuid,
                    'document_id': document.id,
                    "status": 0,
                    "failed": False,
                    "processing_begin_timestamp": mock.ANY,
                    "processing_end_timestamp": mock.ANY,
                })

    # TODO: example.com broken
    def test_post_url_and_title(self):
        data = {'url': 'http://example.com', 'title': 'Super title'}

        ARTICLE_TEXT = "This is a huge responsibility. Treat it as such!"

        self.assertEqual(len(Document.objects.all()), 0)

        with mock.patch('api_v1.document.endpoints.Article') as MockArticle:
            with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                type(MockArticle.return_value).text = mock.PropertyMock(return_value=ARTICLE_TEXT)
                response = self.client.post(self.API_URL + '?from=%s' % self.DUMMY_EMAIL, data=json.dumps(data), content_type='application/json',
                                            REMOTE_ADDR='127.0.0.1')

                self.assertEqual(len(Document.objects.all()), 1)
                document = Document.objects.all()[0]
                data = json.loads(response.content)

                self.assertEqual(data, {
                    "collaborators": [],
                    "created": mock.ANY,
                    "original_name": "Super+title.txt",
                    "owner": {
                        "avatar": "/static/img/mug.png",
                        "company": None,
                        "date_joined": mock.ANY,
                        "document_upload_count": 1,
                        "email": self.DUMMY_EMAIL,
                        "first_name": None,
                        "had_trial": False,
                        "id": mock.ANY,
                        "is_paid": False,
                        "is_super": False,
                        "job_title": None,
                        "last_login": mock.ANY,
                        "last_name": None,
                        "pending": False,
                        "phone": None,
                        "tags": [],
                        "keywords": [],
                        "settings": mock.ANY,
                        "username": self.DUMMY_USERNAME
                    },
                    "report_url": "/report/%s" % document.uuid,
                    "title": 'Super title',
                    "url": "/api/v1/document/%s" % document.uuid,
                    "is_initsample": False,
                    "agreement_type": mock.ANY,
                    "agreement_type_confidence": mock.ANY,
                    "uuid": document.uuid,
                    'document_id': document.id,
                    'document_id': document.id,
                    "status": 0,
                    'failed': False,
                    'processing_begin_timestamp': mock.ANY,
                    'processing_end_timestamp': mock.ANY,
                })

    def test_post_text(self):
        data = {'text': 'This is an awesome text. It is pretty much about anything. Running out of inspiration here.'
                        'What more is it to say? How can I lengthen this even more? Good question! Marvelous question.'
                        'In fact, I need this to be just over 100 chars. Can we make this happen people?'}

        self.assertEqual(len(Document.objects.all()), 0)

        with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
            mock_save.return_value = 'RETURN_VALUE_FILE_PATH'

            response = self.client.post(self.API_URL + '?from=%s' % self.DUMMY_EMAIL, data=json.dumps(data), content_type='application/json',
                                        REMOTE_ADDR='127.0.0.1')

            self.assertEqual(len(Document.objects.all()), 1)
            document = Document.objects.all()[0]
            data = json.loads(response.content)

            EXPECTED_ORIGINAL_NAME = 'This+is+an+awesome+text.+It+is+pretty+much+about+a.txt'

            self.assertEqual(data, {
                "collaborators": [],
                "created": mock.ANY,
                "original_name": EXPECTED_ORIGINAL_NAME,
                "owner": {
                    "avatar": "/static/img/mug.png",
                    "company": None,
                    "date_joined": mock.ANY,
                    "document_upload_count": 1,
                    "email": self.DUMMY_EMAIL,
                    "first_name": None,
                    "had_trial": False,
                    "id": mock.ANY,
                    "is_paid": False,
                    "is_super": False,
                    "job_title": None,
                    "last_login": mock.ANY,
                    "last_name": None,
                    "pending": False,
                    "phone": None,
                    "tags": [],
                    "keywords": [],
                    "settings": mock.ANY,
                    "username": self.DUMMY_USERNAME
                },
                "report_url": "/report/%s" % document.uuid,
                "title": 'This is an awesome text. It is pretty much about a',
                "url": "/api/v1/document/%s" % document.uuid,
                "is_initsample": False,
                "agreement_type": mock.ANY,
                "agreement_type_confidence": mock.ANY,
                "uuid": document.uuid,
                'document_id': document.id,
                "status": 0,
                "failed": False,
                "processing_begin_timestamp": mock.ANY,
                "processing_end_timestamp": mock.ANY,
            })

    def test_post_text_and_title(self):
        data = {'text': 'This is an awesome text. It is pretty much about anything. Running out of inspiration here.'
                        'What more is it to say? How can I lengthen this even more? Good question! Marvelous question.'
                        'In fact, I need this to be just over 100 chars. Can we make this happen people?',
                'title': 'The Stuff'}

        self.assertEqual(len(Document.objects.all()), 0)

        with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
            mock_save.return_value = 'RETURN_VALUE_FILE_PATH'

            response = self.client.post(self.API_URL + '?from=%s' % self.DUMMY_EMAIL, data=json.dumps(data), content_type='application/json',
                                        REMOTE_ADDR='127.0.0.1')

            self.assertEqual(len(Document.objects.all()), 1)
            document = Document.objects.all()[0]
            data = json.loads(response.content)

            self.assertEqual(data, {
                "collaborators": [],
                "created": mock.ANY,
                "original_name": 'The+Stuff.txt',
                "owner": {
                    "avatar": "/static/img/mug.png",
                    "company": None,
                    "date_joined": mock.ANY,
                    "document_upload_count": 1,
                    "email": self.DUMMY_EMAIL,
                    "first_name": None,
                    "had_trial": False,
                    "id": mock.ANY,
                    "is_paid": False,
                    "is_super": False,
                    "job_title": None,
                    "last_login": mock.ANY,
                    "last_name": None,
                    "pending": False,
                    "phone": None,
                    "tags": [],
                    "keywords": [],
                    "settings": mock.ANY,
                    "username": self.DUMMY_USERNAME
                },
                "report_url": "/report/%s" % document.uuid,
                "title": 'The Stuff',
                "url": "/api/v1/document/%s" % document.uuid,
                "is_initsample": False,
                "agreement_type": mock.ANY,
                "agreement_type_confidence": mock.ANY,
                "uuid": document.uuid,
                'document_id': document.id,
                "status": 0,
                "failed": False,
                "processing_begin_timestamp": mock.ANY,
                "processing_end_timestamp": mock.ANY,
            })

    # TODO Rewrite test using new functionality
    def test_workflow_params_for_url(self):
        pass

    # TODO Rewrite test using new functionality
    def test_workflow_params_for_text(self):
        pass

    # TODO: mock broken
    def test_process_document_conversion_params_for_url(self):
        data = {'url': 'http://example.com'}

        ARTICLE_TEXT = "This is a huge responsibility. Treat it as such!"
        ARTICLE_TITLE = "This is the title"

        with mock.patch('api_v1.document.endpoints.Article') as MockArticle:
            with mock.patch('core.tasks.process_document_conversion.delay') as mock_conversion:
                with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                    mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                    type(MockArticle.return_value).text = mock.PropertyMock(return_value=ARTICLE_TEXT)
                    type(MockArticle.return_value).title = mock.PropertyMock(return_value=ARTICLE_TITLE)
                    self.client.post(self.API_URL + '?from=%s' % self.DUMMY_EMAIL, data=json.dumps(data), content_type='application/json',
                                         REMOTE_ADDR='127.0.0.1')

                    mock_conversion.assert_called_once_with(mock.ANY, 'media/RETURN_VALUE_FILE_PATH', True)

    def test_process_document_conversion_params_for_text(self):
        data = {'text': 'This is an awesome text. It is pretty much about anything. Running out of inspiration here.'
                        'What more is it to say? How can I lengthen this even more? Good question! Marvelous question.'
                        'In fact, I need this to be just over 100 chars. Can we make this happen people?'}

        with mock.patch('core.tasks.process_document_conversion.delay') as mock_conversion:
            with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                self.client.post(self.API_URL + '?from=%s' % self.DUMMY_EMAIL, data=json.dumps(data), content_type='application/json',
                                     REMOTE_ADDR='127.0.0.1')

                mock_conversion.assert_called_once_with(mock.ANY, 'media/RETURN_VALUE_FILE_PATH', True)

    # TODO: Github page has changed
    def test_url_containing_unicode(self):
        data = {'url': 'https://github.com/contact'}

        PAGE_HTML = """
            <!DOCTYPE html>
            <html lang="en">
                <head><title>Contact GitHub · GitHub</title></head>
                <body>
                    <p>
                        You’ve come to the right place!
                        The form below sends an email to a real human being on our support staff.
                    </p>
                </body>
            </html>
        """

        self.assertEqual(len(Document.objects.all()), 0)

        with mock.patch('newspaper.article.network.get_html') as mock_get_html:
            mock_get_html.return_value = PAGE_HTML
            with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                response = self.client.post(self.API_URL + '?from=%s' % self.DUMMY_EMAIL, data=json.dumps(data), content_type='application/json',
                                            REMOTE_ADDR='127.0.0.1')

                self.assertEqual(len(Document.objects.all()), 1)
                document = Document.objects.all()[0]
                data = json.loads(response.content)

                self.assertEqual(data, {
                    "agreement_type": mock.ANY,
                    "agreement_type_confidence": mock.ANY,
                    "collaborators": [],
                    "created": mock.ANY,
                    "original_name": "Contact+GitHub+%C2%B7+GitHub.txt",
                    "owner": {
                        "avatar": "/static/img/mug.png",
                        "company": None,
                        "date_joined": mock.ANY,
                        "document_upload_count": 1,
                        "email": self.DUMMY_EMAIL,
                        "first_name": None,
                        "had_trial": False,
                        "id": mock.ANY,
                        "is_paid": False,
                        "is_super": False,
                        "job_title": None,
                        "last_login": mock.ANY,
                        "last_name": None,
                        "pending": False,
                        "phone": None,
                        "tags": [],
                        "keywords": [],
                        "settings": mock.ANY,
                        "username": self.DUMMY_USERNAME
                    },
                    "report_url": "/report/%s" % document.uuid,
                    "title": u'Contact GitHub * GitHub',
                    "url": "/api/v1/document/%s" % document.uuid,
                    "is_initsample": False,
                    "uuid": document.uuid,
                    'document_id': document.id,
                    'document_id': document.id,
                    "status": 0,
                    'failed': False,
                    'processing_begin_timestamp': mock.ANY,
                    'processing_end_timestamp': mock.ANY,
                })

    def test_upload_file(self):
        file_handler = tempfile.TemporaryFile()
        file_handler.write("Hello World!".encode('utf-8'))
        file_handler.seek(0)

        with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
            mock_save.return_value = 'RETURN_VALUE_FILE_PATH'

            response = self.client.post(self.API_URL + '?from=%s' % self.DUMMY_EMAIL,
                                        {'file': self.get_temporary_text_file('document.txt', 'Some awesome stuff')},
                                        format='multipart', REMOTE_ADDR='127.0.0.1')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(Document.objects.all()), 1)

            data = json.loads(response.content)
            self.assertEqual(data, {
                'agreement_type': mock.ANY,
                'agreement_type_confidence': mock.ANY,
                'collaborators': [],
                'created': mock.ANY,
                'is_initsample': False,
                'original_name': 'file',
                'owner': {'avatar': mock.ANY,
                          'company': None,
                          'date_joined': mock.ANY,
                          'document_upload_count': 1,
                          'email': self.DUMMY_EMAIL,
                          'first_name': None,
                          'had_trial': False,
                          'id': mock.ANY,
                          'is_paid': False,
                          'is_super': False,
                          'job_title': None,
                          'last_login': mock.ANY,
                          'last_name': None,
                          'pending': False,
                          'phone': None,
                          'tags': [],
                          'keywords': [],
                          'settings': mock.ANY,
                          'username': self.DUMMY_USERNAME},
                'report_url': mock.ANY,
                'title': 'file',
                'url': mock.ANY,
                'uuid': mock.ANY,
                'document_id': mock.ANY,
                'status': 0,
                'failed': False,
                'processing_begin_timestamp': mock.ANY,
                'processing_end_timestamp': mock.ANY})

    def test_upload_file_with_a_more_complex_name(self):
        file_handler = tempfile.TemporaryFile()
        file_handler.write("Hello World!".encode('utf-8'))
        file_handler.seek(0)

        with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
            mock_save.return_value = 'RETURN_VALUE_FILE_PATH'

            response = self.client.post(self.API_URL + '?from=%s' % self.DUMMY_EMAIL,
                                        {'this_matters.docx': self.get_temporary_text_file('THIS DOESNT MATTER', 'Some awesome stuff')},
                                        format='multipart', REMOTE_ADDR='127.0.0.1')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(Document.objects.all()), 1)

            data = json.loads(response.content)
            self.assertEqual(data, {
                'agreement_type': mock.ANY,
                'agreement_type_confidence': mock.ANY,
                'collaborators': [],
                'created': mock.ANY,
                'is_initsample': False,
                'original_name': 'this_matters.docx',
                'owner': {'avatar': mock.ANY,
                          'company': None,
                          'date_joined': mock.ANY,
                          'document_upload_count': 1,
                          'email': self.DUMMY_EMAIL,
                          'first_name': None,
                          'had_trial': False,
                          'id': mock.ANY,
                          'is_paid': False,
                          'is_super': False,
                          'job_title': None,
                          'last_login': mock.ANY,
                          'last_name': None,
                          'pending': False,
                          'phone': None,
                          'tags': [],
                          'keywords': [],
                          'settings': mock.ANY,
                          'username': self.DUMMY_USERNAME},
                'report_url': mock.ANY,
                'title': 'this matters',
                'url': mock.ANY,
                'uuid': mock.ANY,
                'document_id': mock.ANY,
                'status': 0,
                'failed': False,
                'processing_begin_timestamp': mock.ANY,
                'processing_end_timestamp': mock.ANY})


class InternalAddSubscriptionActionViewTestCase(BeagleWebTest):

    def test_to_dict(self):
        """
        Check that InternalAddSubscriptionActionView.to_dict does nothing :)
        """
        from dogbone.app_settings.marketing_settings import AllAccessTrial
        ps = PurchasedSubscription.purchase_subscription(self.user, AllAccessTrial)

        from api_v1.internal.endpoints import InternalAddSubscriptionActionView
        self.assertEqual(InternalAddSubscriptionActionView.to_dict(ps.to_dict()), ps.to_dict())

    def test_valid_subscription(self):
        from dogbone.app_settings.marketing_settings import AllAccessTrial
        url = reverse('internal_add_subscription_action_view', kwargs={'identifier': self.DUMMY_EMAIL,
                                                                       'subscription_id': AllAccessTrial.uid})
        active_subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)
        self.assertEqual(len(active_subscriptions), 0)

        response = self.client.post(url, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 200)

        active_subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)
        self.assertEqual(len(active_subscriptions), 1)
        self.assertEqual(active_subscriptions[0].get_subscription(), AllAccessTrial)

        data = json.loads(response.content)
        self.assertEqual(data, {
            "buyer": {
                "email": self.DUMMY_EMAIL,
                "first_name": mock.ANY,
                "id": mock.ANY,
                "last_name": mock.ANY,
                "username": self.DUMMY_USERNAME
            },
            "coupon": None,
            "days_remaining": 6,
            "display_days_remaining": 7,
            "end": mock.ANY,
            "end_tz": mock.ANY,
            "expire_info_emailed": None,
            "expire_warning_emailed": None,
            "id": mock.ANY,
            "start": mock.ANY,
            "start_tz": mock.ANY,
            "subscription": {
                "description": AllAccessTrial.description,
                "name": AllAccessTrial.name,
                "price": None,
                "uid": AllAccessTrial.uid
            }
        })

    def test_invalid_subscription(self):
        url = reverse('internal_add_subscription_action_view', kwargs={'identifier': self.DUMMY_EMAIL,
                                                                       'subscription_id': 'NO_SUCH_THING'})
        active_subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)
        self.assertEqual(len(active_subscriptions), 0)

        response = self.client.post(url, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 400)

        active_subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)
        self.assertEqual(len(active_subscriptions), 0)

    def test_invalid_user(self):
        from dogbone.app_settings.marketing_settings import AllAccessTrial
        url = reverse('internal_add_subscription_action_view', kwargs={'identifier': 'whatever@beagle.ai',
                                                                       'subscription_id': AllAccessTrial.uid})
        response = self.client.post(url, REMOTE_ADDR='127.0.0.1')
        self.assertEqual(response.status_code, 404)

    def test_invalid_internal_ip(self):
        from dogbone.app_settings.marketing_settings import AllAccessTrial
        url = reverse('internal_add_subscription_action_view', kwargs={'identifier': self.DUMMY_EMAIL,
                                                                       'subscription_id': AllAccessTrial.uid})

        active_subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)
        self.assertEqual(len(active_subscriptions), 0)

        response = self.client.post(url, REMOTE_ADDR='166.3.4.1')
        self.assertEqual(response.status_code, 403)

        active_subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)
        self.assertEqual(len(active_subscriptions), 0)


class InternalNotifyUserViewTestCase(BeagleWebTest):

    def test_200_unsupported_file_type(self):
        url = reverse('internal_user_notify_action_view', kwargs={'identifier': self.DUMMY_EMAIL,
                                                                  'notification_type': 'unsupported_file_type'})

        active_subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)
        self.assertEqual(len(active_subscriptions), 0)
        with mock.patch('api_v1.internal.endpoints.send_unsupported_file_type_notification.delay') as mock_send:
            response = self.client.post(url, REMOTE_ADDR='127.0.0.1',
                                        content_type='application/json', data=json.dumps({'title': 'strange.doc'}))
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            self.assertEqual(data, {'success': True})
            mock_send.assert_called_with(self.user.pk, 'strange.doc')

    def test_400_unsupported_file_type_no_title(self):
        url = reverse('internal_user_notify_action_view', kwargs={'identifier': self.DUMMY_EMAIL,
                                                                  'notification_type': 'unsupported_file_type'})
        active_subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)
        self.assertEqual(len(active_subscriptions), 0)
        with mock.patch('api_v1.internal.endpoints.send_unsupported_file_type_notification.delay') as mock_send:
            response = self.client.post(url, REMOTE_ADDR='127.0.0.1',
                                        content_type='application/json')
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data, {'message': 'Could not decode the document title from the sent payload',
                                    'code': None,
                                    'type': 'error',
                                    'http_status': 400})

    def test_200_unknown_notification(self):
        url = reverse('internal_user_notify_action_view', kwargs={'identifier': self.DUMMY_EMAIL,
                                                                  'notification_type': 'wut'})
        active_subscriptions = PurchasedSubscription.get_current_subscriptions(self.user)
        self.assertEqual(len(active_subscriptions), 0)
        response = self.client.post(url, REMOTE_ADDR='127.0.0.1',
                                    content_type='application/json', data=json.dumps({'title': 'strange.doc'}))
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Invalid notification type',
                                'code': None,
                                'type': 'error',
                                'http_status': 400})
