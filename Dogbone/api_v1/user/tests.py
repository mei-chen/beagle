import json
import mock
import datetime
import base64
import uuid
from freezegun import freeze_time

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone

from dogbone.testing.base import BeagleWebTest
from core.models import CollaborationInvite, CollaboratorList
from authentication.models import AuthToken
from marketing.models import PurchasedSubscription
from marketing.subscriptions import Subscription


class SomeTrialSubscription(Subscription):
    __abstract__ = False
    uid = "Trial30"
    name = "This Subscription"
    description = "This description"
    duration = datetime.timedelta(days=30)


class CurrentUserTestCase(BeagleWebTest):

    def test_200(self):
        self.make_paid(self.user)
        api_url = reverse('me_detail_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            "id": mock.ANY,
            "avatar": "/static/img/mug.png",
            "date_joined": mock.ANY,
            "email": self.DUMMY_EMAIL,
            "first_name": None,
            "is_paid": True,
            "had_trial": mock.ANY,
            "is_super": False,
            "job_title": None,
            "company": None,
            "tags": mock.ANY,
            "keywords": mock.ANY,
            "settings": mock.ANY,
            "last_login": mock.ANY,
            "last_name": None,
            "username": self.DUMMY_USERNAME,
            "pending": False,
            "document_upload_count": 0,
            "phone": None,
            'token': mock.ANY,
            'token_expire': mock.ANY,
        })

    def test_not_authenticated(self):
        api_url = reverse('me_detail_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_put(self):
        self.make_paid(self.user)
        with mock.patch('portal.tasks.hubspot_update_contact_properties.delay') as mock_hs_update:
            self.login()
            data = {
                'first_name': 'Some FN',
                'last_name': 'Some LN',
                'job_title': 'Professional hand model',
                'company': 'Hand Modelling Inc.',
                "phone": '555-555-5555',
                'password': self.DUMMY_PASSWORD,
                'new_password': '1234',
                'confirm_password': '1234',
            }

            api_url = reverse('me_detail_view')
            response = self.client.put(api_url, data=json.dumps(data), content_type='application/json')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.content)
            self.assertEqual(data, {"id": mock.ANY,
                                    "pending": False,
                                    "username": self.DUMMY_USERNAME,
                                    "first_name": u'Some FN',
                                    "last_name": u'Some LN',
                                    "is_super": False,
                                    "is_paid": True,
                                    "had_trial": mock.ANY,
                                    "company": u'Hand Modelling Inc.',
                                    "tags": [],
                                    "keywords": mock.ANY,
                                    "settings": mock.ANY,
                                    "last_login": mock.ANY,
                                    "avatar": u'/static/img/mug.png',
                                    "job_title": u'Professional hand model',
                                    "email": self.DUMMY_EMAIL,
                                    "date_joined": mock.ANY,
                                    "document_upload_count": 0,
                                    "phone": u'555-555-5555',
                                    "token": mock.ANY,
                                    "token_expire": mock.ANY})

            user = User.objects.get(username=self.DUMMY_USERNAME)
            self.assertTrue(user.check_password('1234'))

            self.assertEqual(user.last_name, 'Some LN')
            self.assertEqual(user.first_name, 'Some FN')
            self.assertEqual(user.details.phone, '555-555-5555')
            self.assertEqual(user.details.company, 'Hand Modelling Inc.')
            self.assertEqual(user.details.job_title, 'Professional hand model')

            # Check for HS update calls
            self.assertTrue(mock_hs_update.called)

    @freeze_time("2014-11-5")
    @mock.patch('integrations.s3.S3FileManager.save_string')
    @mock.patch('integrations.s3.S3Connection')
    def test_update_profile_picture_s3(self, _, mock_save_string):
        self.login()
        data = {
            'avatar': 'abcabc,%s' % base64.b64encode('abcabc123123'),
        }
        api_url = reverse('me_detail_view')

        with mock.patch('api_v1.user.endpoints.uuid.uuid4') as mock_uuid4:
            generated_uuid = uuid.UUID(bytes='1234432112344321')
            mock_uuid4.return_value = generated_uuid
            response = self.client.put(api_url, data=json.dumps(data), content_type='application/json')
            self.assertEqual(response.status_code, 200)

            mock_save_string.assert_called_with('profile_photo/2014/11/5/%s.png' % str(generated_uuid),
                                                'abcabc123123', acl='public-read')

    def test_wrong_old_password(self):
        self.login()
        data = {
            'first_name': 'Some FN',
            'last_name': 'Some LN',
            'job_title': 'Professional hand model',
            'company': 'Hand Modelling Inc.',
            'password': 'ThatsCuteButItsWrong!!!',
            'new_password': '1234',
            'confirm_password': '1234',
        }

        api_url = reverse('me_detail_view')
        response = self.client.put(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        user = User.objects.get(username=self.DUMMY_USERNAME)
        self.assertTrue(user.check_password(self.DUMMY_PASSWORD))

        self.assertNotEqual(user.last_name, 'Some LN')
        self.assertNotEqual(user.first_name, 'Some FN')
        self.assertNotEqual(user.details.company, 'Hand Modelling Inc.')
        self.assertNotEqual(user.details.job_title, 'Professional hand model')

    def test_wrong_not_matching_passwords(self):
        self.login()
        data = {
            'first_name': 'Some FN',
            'last_name': 'Some LN',
            'job_title': 'Professional hand model',
            'company': 'Hand Modelling Inc.',
            'password': self.DUMMY_PASSWORD,
            'new_password': '12345',
            'confirm_password': '54321',
        }

        api_url = reverse('me_detail_view')
        response = self.client.put(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        user = User.objects.get(username=self.DUMMY_USERNAME)
        self.assertTrue(user.check_password(self.DUMMY_PASSWORD))

        self.assertNotEqual(user.last_name, 'Some LN')
        self.assertNotEqual(user.first_name, 'Some FN')
        self.assertNotEqual(user.details.company, 'Hand Modelling Inc.')
        self.assertNotEqual(user.details.job_title, 'Professional hand model')

    def test_active_subscription(self):
        user = self.create_user('eeee@mail.com', 'Funkey', 'p@$$')
        purchased = PurchasedSubscription(buyer=user,
                                          subscription=SomeTrialSubscription.uid)

        purchased.save()
        client = self.client_class()
        client.login(username=user.username, password='p@$$')

        api_url = reverse('me_detail_view')
        response = client.get(api_url)
        data = json.loads(response.content)

        self.assertTrue(data['is_paid'])

    def test_expired_subscription(self):
        user = self.create_user('eeee@mail.com', 'Funkey', 'p@$$')
        purchased = PurchasedSubscription(buyer=user,
                                          subscription=SomeTrialSubscription.uid)

        purchased.save()
        over31days = timezone.now() + datetime.timedelta(days=31)
        with freeze_time(over31days):
            client = self.client_class()
            client.login(username=user.username, password='p@$$')
            api_url = reverse('me_detail_view')
            response = client.get(api_url)
            data = json.loads(response.content)

            self.assertFalse(data['is_paid'])

    def test_no_active_subscription(self):
        user = self.create_user('eeee@mail.com', 'Funkey', 'p@$$')
        client = self.client_class()
        client.login(username=user.username, password='p@$$')

        api_url = reverse('me_detail_view')
        response = client.get(api_url)
        data = json.loads(response.content)

        self.assertFalse(data['is_paid'])


class UserUnviewedDocsTest(BeagleWebTest):

    def test_get(self):
        document = self.create_document('Some title', self.user, pending=False)

        self.make_paid(self.user)
        self.login()

        url = reverse('user_unviewed_docs_view',
                      kwargs={'identifier': self.user.username})
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, [document.uuid])

        doc_view = reverse('document_detail_view',
                           kwargs={'uuid': document.uuid})
        self.client.get(doc_view)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[]')


class UserDetailViewTestCase(BeagleWebTest):

    def test_200_username(self):
        user = self.create_user('myemail@yahoo.com', 'gigi-tarnac0p_A', 'p@ss')
        api_url = reverse('user_detail_view', kwargs={'identifier': user.username})
        self.login()

        response = self.client.get(api_url)
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

    def test_200_email(self):
        user = self.create_user('myemail@yahoo.com', 'gigi-tarnac0p_A', 'p@ss')
        api_url = reverse('user_detail_view', kwargs={'identifier': user.email})
        self.login()

        response = self.client.get(api_url)
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

    def test_200_email_case_insensitive(self):
        user = self.create_user('myemail@yahoo.com', 'gigi-tarnac0p_A', 'p@ss')
        api_url = reverse('user_detail_view', kwargs={'identifier': 'MYEMAIL@YAHOO.COM'})
        self.login()

        response = self.client.get(api_url)
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
        api_url = reverse('user_detail_view', kwargs={'identifier': user.pk})
        self.login()

        response = self.client.get(api_url)
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

    def test_not_authenticated(self):
        api_url = reverse('user_detail_view', kwargs={'identifier': self.DUMMY_USERNAME})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate',
                                'code': None,
                                'type': 'error',
                                'http_status': 403})

    def test404(self):
        self.login()
        api_url = reverse('user_detail_view', kwargs={'identifier': 'Not_Found'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'This username does not exist',
                                'code': None,
                                'type': 'error',
                                'http_status': 404})


class UserAuthenticationViewTestCase(BeagleWebTest):
    def test_get(self):
        api_url = reverse('user_auth_compute_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

    def test_empty_post(self):
        api_url = reverse('user_auth_compute_view')

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {
            "code": None,
            "http_status": 400,
            "message": "No JSON object could be decoded",
            "type": "error"
        })

    def test_no_username_no_email(self):
        api_url = reverse('user_auth_compute_view')

        response = self.client.post(api_url, data=json.dumps({'password': '1234'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {
            "code": None,
            "http_status": 400,
            "message": "email/username not present",
            "type": "error"
        })

    def test_no_password(self):
        api_url = reverse('user_auth_compute_view')

        response = self.client.post(api_url, data=json.dumps({'username': 'user1234'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {
            "code": None,
            "http_status": 400,
            "message": "password not present",
            "type": "error"
        })

    def test_not_matching_credentials(self):
        api_url = reverse('user_auth_compute_view')

        response = self.client.post(api_url, data=json.dumps({'username': 'user1234', 'password': 'p@$$'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content), {
            "code": None,
            "http_status": 403,
            "message": "incorrect credentials",
            "type": "error"
        })

    def test_not_matching_password(self):
        api_url = reverse('user_auth_compute_view')

        response = self.client.post(api_url, data=json.dumps({'username': self.DUMMY_USERNAME, 'password': 'p@$$w0rD'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content), {
            "code": None,
            "http_status": 403,
            "message": "incorrect credentials",
            "type": "error"
        })

    def test_not_matching_username(self):
        api_url = reverse('user_auth_compute_view')

        response = self.client.post(api_url, data=json.dumps({'username': self.DUMMY_USERNAME + '123',
                                                              'password': self.DUMMY_PASSWORD}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content), {
            "code": None,
            "http_status": 403,
            "message": "incorrect credentials",
            "type": "error"
        })

    def test_not_matching_email(self):
        api_url = reverse('user_auth_compute_view')

        response = self.client.post(api_url, data=json.dumps({'email': 'aaa' + self.DUMMY_EMAIL,
                                                              'password': self.DUMMY_PASSWORD}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content), {
            "code": None,
            "http_status": 403,
            "message": "incorrect credentials",
            "type": "error"
        })

    def test_correct_credentials1(self):
        self.make_paid(self.user)
        api_url = reverse('user_auth_compute_view')

        response = self.client.post(api_url,
                                    data=json.dumps({'email': self.DUMMY_EMAIL, 'password': self.DUMMY_PASSWORD}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        token = AuthToken.objects.get(user=self.user).token

        self.assertEqual(json.loads(response.content), {
            'avatar': '/static/img/mug.png',
            'company': None,
            "date_joined": mock.ANY,
            'document_upload_count': 0,
            'email': self.DUMMY_EMAIL,
            'first_name': None,
            'had_trial': False,
            'id': mock.ANY,
            'is_paid': True,
            'is_super': False,
            'job_title': None,
            'last_login': mock.ANY,
            'last_name': None,
            'pending': False,
            "phone": None,
            "tags": [],
            "keywords": mock.ANY,
            "settings": mock.ANY,
            'username': self.DUMMY_USERNAME})

    def test_correct_credentials2(self):
        self.make_paid(self.user)

        api_url = reverse('user_auth_compute_view')

        response = self.client.post(api_url, data=json.dumps({'username': self.DUMMY_USERNAME,
                                                              'password': self.DUMMY_PASSWORD}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        token = AuthToken.objects.get(user=self.user).token

        self.assertEqual(json.loads(response.content), {
            'avatar': '/static/img/mug.png',
            'company': None,
            "date_joined": mock.ANY,
            'document_upload_count': 0,
            'email': self.DUMMY_EMAIL,
            'first_name': None,
            'had_trial': False,
            'id': mock.ANY,
            'is_paid': True,
            'is_super': False,
            'job_title': None,
            'last_login': mock.ANY,
            'last_name': None,
            'pending': False,
            "phone": None,
            "tags": [],
            "keywords": mock.ANY,
            "settings": mock.ANY,
            'username': self.DUMMY_USERNAME})

    def test_endpoints_working_with_token(self):
        AuthToken.create_token_model(self.user)
        token = self.user.auth_token.token

        api_url = reverse('me_profile_detail_view')
        response = self.client.get(api_url + '?token=%s' % token)
        self.assertEqual(response.status_code, 200)

        api_url = reverse('me_detail_view')
        response = self.client.get(api_url + '?token=%s' % token)
        self.assertEqual(response.status_code, 200)

        api_url = reverse('me_subscription_detail_view')
        response = self.client.get(api_url + '?token=%s' % token)
        self.assertEqual(response.status_code, 200)


class CurrentUserProfileTestCase(BeagleWebTest):

    def test_200(self):
        api_url = reverse('me_profile_detail_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'company': '',
                                'avatar': '/static/img/mug.png',
                                'job_title': '',
                                "tags": [],
                                "keywords": [],
                                "settings": mock.ANY,
                                'document_upload_count': 0,
                                "phone": ''})

    def test_not_authenticated(self):
        api_url = reverse('me_detail_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})


class UserSettingsTestCase(BeagleWebTest):

    def test_200(self):
        self.make_paid(self.user)
        api_url = reverse('me_settings_detail_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {})

    def test_not_authenticated(self):
        api_url = reverse('me_settings_detail_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_put(self):
        self.make_paid(self.user)
        self.login()
        data = {'a': True, 'b': False, 'c': False, 'd': True}

        api_url = reverse('me_settings_detail_view')
        response = self.client.put(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        resp_data = json.loads(response.content)
        self.assertEqual(resp_data, data)

        user = User.objects.get(username=self.DUMMY_USERNAME)
        self.assertEqual(user.details.settings, data)


class CurrentUserCollaboratorsTestCase(BeagleWebTest):

    def test_200(self):
        """
        Test that user without collaborators gets an empty list
        """
        api_url = reverse('me_collaborators_list_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'objects': []})

    def test_403(self):
        """
        Check an unauthenticated user gets a 403
        """
        api_url = reverse('me_collaborators_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_inviter(self):
        """
        Check that a user with one collaborator on a document gets a list with one collaborator
        """
        self.login()
        api_url = reverse('me_collaborators_list_view')
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', self.user, pending=False)
        CollaborationInvite(inviter=self.user, invitee=other_user, document=document).save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['objects']), 1)

        self.assertEqual(data['objects'][0]['email'], 'some@email.com')

    def test_invitee(self):
        """
        Check that a user that has been invited to one document gets a list with one collaborator, the inviter
        """
        self.login()
        api_url = reverse('me_collaborators_list_view')
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', other_user, pending=False)
        CollaborationInvite(invitee=self.user, inviter=other_user, document=document).save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['objects']), 1)

        self.assertEqual(data['objects'][0]['email'], 'some@email.com')

    def test_invite_then_uninvite(self):
        """
        Check that once a collaborator always a collaborator
        - Invite a user to collaborate on a document
        - The invited user should be in the collaborators list
        - Uninvite the user from the document
        - That user should still be in the suggested collaborators list
        """
        self.login()
        api_url = reverse('me_collaborators_list_view')
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', self.user, pending=False)
        invite = CollaborationInvite(inviter=self.user, invitee=other_user, document=document)
        invite.save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['email'], 'some@email.com')

        invite.delete()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['objects']), 1)

        self.assertEqual(data, {'objects': [
            {'username': 'someusername',
             'first_name': None,
             'last_name': None,
             'is_super': False,
             'is_paid': False,
             'had_trial': mock.ANY,
             'company': None,
             'email': 'some@email.com',
             'last_login': mock.ANY,
             'avatar': '/static/img/mug.png',
             'job_title': None,
             'id': mock.ANY,
             "tags": [],
             "keywords": [],
             "settings": mock.ANY,
             'pending': False,
             "date_joined": mock.ANY,
             "document_upload_count": 0,
             "phone": None}]})

    def test_invite_then_uninvite_and_invite_another(self):
        self.login()
        api_url = reverse('me_collaborators_list_view')
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', self.user, pending=False)
        invite = CollaborationInvite(inviter=self.user, invitee=other_user, document=document)
        invite.save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['email'], 'some@email.com')
        invite.delete()

        other_user = self.create_user('new@email.com', 'newusername', 'somepass')
        invite = CollaborationInvite(inviter=self.user, invitee=other_user, document=document)
        invite.save()
        CollaboratorList.objects.get(user=self.user).add_collaborator(email='new@email.com')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)

        self.assertEqual(sorted(data['objects'], key=lambda item: item['email']), sorted([
            {'username': 'someusername',
             'first_name': None,
             'last_name': None,
             'is_super': False,
             'is_paid': False,
             'had_trial': mock.ANY,
             'company': None,
             'email': 'some@email.com',
             'last_login': mock.ANY,
             'avatar': '/static/img/mug.png',
             'job_title': None,
             'id': mock.ANY,
             'pending': False,
             "tags": [],
             "keywords": [],
             "settings": mock.ANY,
             "date_joined": mock.ANY,
             "document_upload_count": 0,
             "phone": None},
            {'username': 'newusername',
             'first_name': None,
             'last_name': None,
             'is_super': False,
             'is_paid': False,
             'had_trial': mock.ANY,
             'company': None,
             'email': 'new@email.com',
             'last_login': mock.ANY,
             'avatar': '/static/img/mug.png',
             'job_title': None,
             'id': mock.ANY,
             'pending': False,
             "tags": [],
             "keywords": [],
             "settings": mock.ANY,
             "date_joined": mock.ANY,
             "document_upload_count": 0,
             "phone": None}], key=lambda item: item['email']))

    def test_invite_then_uninvite_and_invite_another_via_api(self):
        self.make_paid(self.user)
        self.login()
        api_url = reverse('me_collaborators_list_view')
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', self.user, pending=False)

        invite_api_url = reverse('document_issued_invitations_list_view',
                                 kwargs={'uuid': document.uuid})
        data = {'invitee': other_user.email}
        response = self.client.post(invite_api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['email'], 'some@email.com')

        other_user = self.create_user('new@email.com', 'newusername', 'somepass')
        data = {'invitee': other_user.email}
        response = self.client.post(invite_api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)

        self.assertEqual(sorted(data['objects'], key=lambda item: item['email']), sorted([
            {'username': 'someusername',
             'first_name': None,
             'last_name': None,
             'is_super': False,
             'is_paid': False,
             'had_trial': mock.ANY,
             'company': None,
             'email': 'some@email.com',
             'last_login': mock.ANY,
             'avatar': '/static/img/mug.png',
             'job_title': None,
             'id': mock.ANY,
             'pending': False,
             "tags": [],
             "keywords": [],
             "settings": mock.ANY,
             "date_joined": mock.ANY,
             "document_upload_count": 0,
             "phone": None},
            {'username': 'newusername',
             'first_name': None,
             'last_name': None,
             'is_super': False,
             'is_paid': False,
             'had_trial': mock.ANY,
             'company': None,
             'email': 'new@email.com',
             'last_login': mock.ANY,
             'avatar': '/static/img/mug.png',
             'job_title': None,
             'id': mock.ANY,
             'pending': False,
             "tags": [],
             "keywords": [],
             "settings": mock.ANY,
             "date_joined": mock.ANY,
             "document_upload_count": 0,
             "phone": None}], key=lambda item: item['email']))

    def test_invite_internal_and_external(self):
        self.make_paid(self.user)
        self.login()

        document = self.create_document('Title', self.user, pending=False)
        self.create_user('some@email.com', 'someusername', 'somepass')

        api_url = reverse('document_issued_invitations_list_view', kwargs={'uuid': document.uuid}) + '?external=True'
        data = {'invitee': 'some@email.com'}
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = {'invitee': 'external@email.com'}
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        suggestion_api_url = reverse('me_collaborators_list_view')

        response = self.client.get(suggestion_api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)

        self.assertEqual(data, {'objects': [
            {'username': 'someusername',
             'first_name': None,
             'last_name': None,
             'is_super': False,
             'is_paid': False,
             'had_trial': mock.ANY,
             'company': None,
             'email': 'some@email.com',
             'last_login': mock.ANY,
             'avatar': '/static/img/mug.png',
             'job_title': None,
             'id': mock.ANY,
             'pending': False,
             "tags": [],
             "keywords": [],
             "settings": mock.ANY,
             "date_joined": mock.ANY,
             'document_upload_count': 0,
             "phone": None},
            {'username': 'external@email.com',
             'first_name': None,
             'last_name': None,
             'is_super': False,
             'is_paid': False,
             'had_trial': mock.ANY,
             'company': None,
             'email': 'external@email.com',
             'last_login': None,
             'avatar': '/static/img/mugpending.png',
             'job_title': None,
             'id': None,
             'pending': True,
             "tags": [],
             "keywords": [],
             "settings": mock.ANY,
             "date_joined": None}]})

    def test_more_collaborations(self):
        """
        Complex scenario with many inviters and documents
        """
        self.login()
        api_url = reverse('me_collaborators_list_view')
        user1 = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        user2 = self.create_user('some2@email.com', 'someusername2', 'somepass2')
        user3 = self.create_user('some3@email.com', 'someusername3', 'somepass3')

        document1 = self.create_document('Title1', self.user, pending=False)
        document2 = self.create_document('Title2', user1, pending=False)
        document3 = self.create_document('Title3', user2, pending=False)
        document4 = self.create_document('Title4', user3, pending=False)
        document5 = self.create_document('Title5', user3, pending=False)

        CollaborationInvite(invitee=user1, inviter=self.user, document=document1).save()
        CollaborationInvite(invitee=self.user, inviter=user1, document=document2).save()
        CollaborationInvite(invitee=self.user, inviter=user3, document=document4).save()
        CollaborationInvite(invitee=self.user, inviter=user3, document=document5).save()
        CollaborationInvite(invitee=user3, inviter=user2, document=document3).save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)

        self.assertEqual(sorted(data['objects'], key=lambda item: item['email']), sorted([
            {'username': 'someusername1',
             'first_name': None,
             'last_name': None,
             'is_super': False,
             'is_paid': False,
             'had_trial': mock.ANY,
             'company': None,
             'email': 'some1@email.com',
             'last_login': mock.ANY,
             'avatar': '/static/img/mug.png',
             'job_title': None,
             'id': mock.ANY,
             'pending': False,
             "tags": [],
             "keywords": [],
             "settings": mock.ANY,
             "date_joined": mock.ANY,
             'document_upload_count': 1,
             "phone": None},
            {'username': 'someusername3',
             'first_name': None,
             'last_name': None,
             'is_super': False,
             'is_paid': False,
             'had_trial': mock.ANY,
             'company': None,
             'email': 'some3@email.com',
             'last_login': mock.ANY,
             'avatar': '/static/img/mug.png',
             'job_title': None,
             'id': mock.ANY,
             'pending': False,
             "tags": [],
             "keywords": [],
             "settings": mock.ANY,
             "date_joined": mock.ANY,
             'document_upload_count': 2,
             "phone": None}], key=lambda item: item['email']))


class CurrentUserActiveSubscriptionDetailViewTestCase(BeagleWebTest):
    def test_no_subscription(self):
        """
        Test the return for a user with no active subscription
        """
        self.login()
        api_url = reverse('me_subscription_detail_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'current_subscription': None})

    def test_403(self):
        """
        Check an unauthenticated user gets a 403
        """
        api_url = reverse('me_subscription_detail_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_active_subscription(self):
        """
        Test the return for a user with an active subscription
        """
        self.login()
        api_url = reverse('me_subscription_detail_view')
        purchased = PurchasedSubscription(buyer=self.user,
                                          subscription=SomeTrialSubscription.uid)

        purchased.save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'current_subscription': {
                'buyer': {
                    'username': self.DUMMY_USERNAME,
                    'first_name': mock.ANY,
                    'last_name': mock.ANY,
                    'email': self.DUMMY_EMAIL,
                    'id': mock.ANY
                },
                'id': mock.ANY,
                'is_trial': False,
                'coupon': None,
                'subscription': {
                    'uid': 'Trial30',
                    'price': 0.0,
                    'description': 'This description',
                    'name': 'This Subscription'
                },
                'days_remaining': 29,
                'display_days_remaining': 30,
                'expire_info_emailed': None,
                'expire_warning_emailed': None,
                'end': mock.ANY,
                'start': mock.ANY,
                'start_tz': 'UTC',
                'end_tz': 'UTC'}})

    def test_is_trial(self):
        """
        Test if the is_trial flag is working properly
        """
        from dogbone.app_settings.marketing_settings import StandardTrial

        self.login()

        api_url = reverse('me_subscription_detail_view')
        purchased = PurchasedSubscription(buyer=self.user,
                                          subscription=StandardTrial.uid)
        purchased.save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'current_subscription': {
                'buyer': {
                    'username': self.DUMMY_USERNAME,
                    'first_name': mock.ANY,
                    'last_name': mock.ANY,
                    'email': self.DUMMY_EMAIL,
                    'id': mock.ANY
                },
                'id': mock.ANY,
                'is_trial': True,
                'coupon': None,
                'subscription': {
                    'uid': StandardTrial.uid,
                    'price': None,
                    'description': StandardTrial.description,
                    'name': StandardTrial.name
                },
                'days_remaining': 29,
                'display_days_remaining': 30,
                'expire_info_emailed': None,
                'expire_warning_emailed': None,
                'end': mock.ANY,
                'start': mock.ANY,
                'start_tz': 'UTC',
                'end_tz': 'UTC'}})


class CurrentUserSubscriptionsListViewTestCase(BeagleWebTest):
    def test_no_subscription(self):
        """
        Test the return for a user with no active subscription
        """
        self.login()
        api_url = reverse('me_subscriptions_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'objects': []})

    def test_403(self):
        """
        Check an unauthenticated user gets a 403
        """
        api_url = reverse('me_subscriptions_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_active_subscriptions(self):
        """
        Test the return for a user with an active subscription
        """
        self.login()
        api_url = reverse('me_subscriptions_list_view')
        purchased = PurchasedSubscription(buyer=self.user,
                                          subscription=SomeTrialSubscription.uid)

        purchased.save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(data, {
            'objects': [{
                'buyer': {
                    'username': self.DUMMY_USERNAME,
                    'first_name': mock.ANY,
                    'last_name': mock.ANY,
                    'email': self.DUMMY_EMAIL,
                    'id': mock.ANY
                },
                'id': mock.ANY,
                'is_trial': False,
                'coupon': None,
                'subscription': {
                    'uid': 'Trial30',
                    'price': 0.0,
                    'description': 'This description',
                    'name': 'This Subscription'
                },
                'days_remaining': 29,
                'display_days_remaining': 30,
                'expire_info_emailed': None,
                'expire_warning_emailed': None,
                'end': mock.ANY,
                'start': mock.ANY,
                'start_tz': 'UTC',
                'end_tz': 'UTC'}
            ]
        })

    def test_is_trial(self):
        """
        Test if the is_trial flag is working properly
        """
        from dogbone.app_settings.marketing_settings import StandardTrial

        self.login()

        api_url = reverse('me_subscriptions_list_view')
        purchased = PurchasedSubscription(buyer=self.user,
                                          subscription=StandardTrial.uid)
        purchased.save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'objects': [
                {
                    'buyer': {
                        'username': self.DUMMY_USERNAME,
                        'first_name': mock.ANY,
                        'last_name': mock.ANY,
                        'email': self.DUMMY_EMAIL,
                        'id': mock.ANY
                    },
                    'id': mock.ANY,
                    'is_trial': True,
                    'coupon': None,
                    'subscription': {
                        'uid': StandardTrial.uid,
                        'price': None,
                        'description': StandardTrial.description,
                        'name': StandardTrial.name
                    },
                    'days_remaining': 29,
                    'display_days_remaining': 30,
                    'expire_info_emailed': None,
                    'expire_warning_emailed': None,
                    'end': mock.ANY,
                    'start': mock.ANY,
                    'start_tz': 'UTC',
                    'end_tz': 'UTC'}
            ]
        })

    def test_multiple_active_subscription(self):
        """
        Test if multiple subscriptions are properly exposed through the API
        """
        from dogbone.app_settings.marketing_settings import (StandardTrial, UnlimitedBrowserExtensionSubscription,
                                                YearlyPaidSubscription)

        self.login()

        PurchasedSubscription(buyer=self.user, subscription=StandardTrial.uid,
                              start=timezone.now()).save()
        PurchasedSubscription(buyer=self.user, subscription=UnlimitedBrowserExtensionSubscription.uid,
                              start=timezone.now()).save()
        PurchasedSubscription(buyer=self.user, subscription=YearlyPaidSubscription.uid,
                              start=timezone.now()).save()

        api_url = reverse('me_subscriptions_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        data['objects'] = sorted(data['objects'], key=lambda item: -item['id'])
        self.assertEqual(data, {'objects': [{'buyer': {'email': self.DUMMY_EMAIL,
                                                       'first_name': '',
                                                       'id': mock.ANY,
                                                       'last_name': '',
                                                       'username': self.DUMMY_USERNAME},
                                             'id': mock.ANY,
                                             'coupon': None,
                                             'days_remaining': 364,
                                             'display_days_remaining': 365,
                                             'end': mock.ANY,
                                             'end_tz': 'UTC',
                                             'expire_info_emailed': None,
                                             'expire_warning_emailed': None,
                                             'is_trial': False,
                                             'start': mock.ANY,
                                             'start_tz': 'UTC',
                                             'subscription': {'description': YearlyPaidSubscription.description,
                                                              'name': YearlyPaidSubscription.name,
                                                              'price': 4000.0,
                                                              'uid': YearlyPaidSubscription.uid}},
                                            {'buyer': {'email': self.DUMMY_EMAIL,
                                                       'first_name': '',
                                                       'id': mock.ANY,
                                                       'last_name': '',
                                                       'username': self.DUMMY_USERNAME},
                                             'id': mock.ANY,
                                             'coupon': None,
                                             'days_remaining': None,
                                             'display_days_remaining': None,
                                             'end': None,
                                             'end_tz': None,
                                             'expire_info_emailed': None,
                                             'expire_warning_emailed': None,
                                             'is_trial': False,
                                             'start': mock.ANY,
                                             'start_tz': 'UTC',
                                             'subscription': {'description': UnlimitedBrowserExtensionSubscription.description,
                                                              'name': UnlimitedBrowserExtensionSubscription.name,
                                                              'price': 0.0,
                                                              'uid': UnlimitedBrowserExtensionSubscription.uid}},
                                            {'buyer': {'email': self.DUMMY_EMAIL,
                                                       'first_name': '',
                                                       'id': mock.ANY,
                                                       'last_name': '',
                                                       'username': self.DUMMY_USERNAME},
                                             'id': mock.ANY,
                                             'coupon': None,
                                             'days_remaining': 29,
                                             'display_days_remaining': 30,
                                             'end': mock.ANY,
                                             'end_tz': 'UTC',
                                             'expire_info_emailed': None,
                                             'expire_warning_emailed': None,
                                             'is_trial': True,
                                             'start': mock.ANY,
                                             'start_tz': 'UTC',
                                             'subscription': {'description': StandardTrial.description,
                                                              'name': StandardTrial.name,
                                                              'price': None,
                                                              'uid': StandardTrial.uid}}]})


class UserSubscriptionInfoOnDetailViewTestCase(BeagleWebTest):
    def test_user_had_trial(self):
        """
        Test if the is_trial flag is working properly
        """
        from dogbone.app_settings.marketing_settings import StandardTrial

        self.login()

        api_url = reverse('me_subscription_detail_view')

        purchased = PurchasedSubscription(buyer=self.user,
                                          subscription=StandardTrial.uid,
                                          start=timezone.now() - datetime.timedelta(days=50))
        purchased.save()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'current_subscription': None})

        me_api_url = reverse('me_detail_view')

        response = self.client.get(me_api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(data, {
            "id": mock.ANY,
            "avatar": "/static/img/mug.png",
            "date_joined": mock.ANY,
            "email": self.DUMMY_EMAIL,
            "first_name": None,
            "is_paid": False,
            "had_trial": True,
            "is_super": False,
            "job_title": None,
            "company": None,
            "tags": mock.ANY,
            "keywords": mock.ANY,
            "settings": mock.ANY,
            "last_login": mock.ANY,
            "last_name": None,
            "username": self.DUMMY_USERNAME,
            "pending": False,
            "document_upload_count": 0,
            "phone": None,
            "token": mock.ANY,
            "token_expire": mock.ANY
        })

    def test_user_had_no_trial(self):
        """
        Test if the is_trial flag is working properly
        """
        self.login()

        api_url = reverse('me_subscription_detail_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'current_subscription': None})

        me_api_url = reverse('me_detail_view')

        response = self.client.get(me_api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(data, {
            "id": mock.ANY,
            "avatar": "/static/img/mug.png",
            "date_joined": mock.ANY,
            "email": self.DUMMY_EMAIL,
            "first_name": None,
            "is_paid": False,
            "had_trial": False,
            "is_super": False,
            "job_title": None,
            "company": None,
            "tags": mock.ANY,
            "keywords": mock.ANY,
            "settings": mock.ANY,
            "last_login": mock.ANY,
            "last_name": None,
            "username": self.DUMMY_USERNAME,
            "pending": False,
            "document_upload_count": 0,
            "phone": None,
            'token': mock.ANY,
            'token_expire': mock.ANY
        })
