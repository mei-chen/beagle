import mock
import json
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.http import HttpResponse
from dogbone.testing.base import BeagleWebTest
from core.models import CollaborationInvite, Document
from api_v1.decorators import is_internal, internal_or_403
from authentication.models import AuthToken


class AllowedActionsTestCase(BeagleWebTest):
    def test_url_send_for_extension_user(self):
        """
        Check if a chrome extension user can upload a document via API
        """
        ARTICLE_TEXT = "This is a huge responsibility. Treat it as such!"
        ARTICLE_TITLE = "This is the title"

        self.make_extension_user(self.user)
        auth_url = reverse('user_auth_compute_view')
        upload_url = reverse('document_upload_compute_view')

        response = self.client.post(auth_url, data=json.dumps({'username': self.DUMMY_USERNAME,
                                                              'password': self.DUMMY_PASSWORD}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        token = AuthToken.objects.get(user=self.user).token
        data = {'url': 'http://example.com'}

        with mock.patch('api_v1.document.endpoints.Article') as MockArticle:
            with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                type(MockArticle.return_value).text = mock.PropertyMock(return_value=ARTICLE_TEXT)
                type(MockArticle.return_value).title = mock.PropertyMock(return_value=ARTICLE_TITLE)
                response = self.client.post(upload_url + '?token=' + token,
                                            data=json.dumps(data),
                                            content_type='application/json')

                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(Document.objects.all()), 1)

    def test_url_send_for_non_extension_user(self):
        """
        Check if a chrome extension user cannot upload a document via API
        """
        ARTICLE_TEXT = "This is a huge responsibility. Treat it as such!"
        ARTICLE_TITLE = "This is the title"

        auth_url = reverse('user_auth_compute_view')
        upload_url = reverse('document_upload_compute_view')

        response = self.client.post(auth_url, data=json.dumps({'username': self.DUMMY_USERNAME,
                                                              'password': self.DUMMY_PASSWORD}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        token = self.user.auth_token.token
        data = {'url': 'http://example.com'}

        with mock.patch('api_v1.document.endpoints.Article') as MockArticle:
            with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                type(MockArticle.return_value).text = mock.PropertyMock(return_value=ARTICLE_TEXT)
                type(MockArticle.return_value).title = mock.PropertyMock(return_value=ARTICLE_TITLE)
                response = self.client.post(upload_url + '?token=' + token,
                                            data=json.dumps(data),
                                            content_type='application/json')

                self.assertEqual(response.status_code, 403)
                self.assertEqual(len(Document.objects.all()), 0)

    def test_invite_collaborator_check_actions(self):
        """
        Check if an invited user without any subscription can
        1. post a comment on a document
        2. like a sentence
        3. dislike a sentence
        4. add tag
        5. remove tag
        """
        # Create a paid user
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        self.make_paid(other_user)

        # Login the user
        self.login()

        # Create the document
        document = self.create_document('Title', self.user, pending=False)

        CollaborationInvite(inviter=other_user, document=document, invitee=self.user).save()

        # 1. post a comment on a document
        url = reverse('sentence_comments_list_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        data = {'message': 'Awesome!'}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # 2. like a sentence
        like_url = reverse('sentence_like_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(like_url)
        self.assertEqual(response.status_code, 200)

        # 3. dislike a sentence
        dislike_url = reverse('sentence_dislike_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(dislike_url)
        self.assertEqual(response.status_code, 200)

        # 4. add tag
        tag_url = reverse('sentence_tags_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        data = json.dumps({'tag': 'tag1'})
        response = self.client.post(tag_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # 5. remove tag
        tag_url = reverse('sentence_tags_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        data = json.dumps({'tag': 'tag1'})
        response = self.client.delete(tag_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)


class TestInternalRequest(BeagleWebTest):
    def test_internal_ips(self):
        self.factory = RequestFactory()
        request = self.factory.get('/addr', REMOTE_ADDR="127.0.0.1")

        with self.settings(INTERNAL_IPS=('127.0.0.1', )):
            self.assertTrue(is_internal(request))

    def test_decorator_internal(self):
        self.factory = RequestFactory()
        request = self.factory.get('/addr', REMOTE_ADDR="127.0.0.1")

        def viewf(_):
            return HttpResponse("Super")

        decorated = internal_or_403(viewf)

        with self.settings(INTERNAL_IPS=('127.0.0.1', )):
            response = decorated(request)
            self.assertEqual(response.status_code, 200)

    def test_decorator_external(self):
        self.factory = RequestFactory()
        request = self.factory.get('/addr', REMOTE_ADDR="122.12.12.3")

        def viewf(_):
            return HttpResponse("Super")

        decorated = internal_or_403(viewf)

        with self.settings(INTERNAL_IPS=('127.0.0.1', )):
            response = decorated(request)
            self.assertEqual(response.status_code, 403)
