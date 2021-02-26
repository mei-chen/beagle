import json
import mock
from django.core.urlresolvers import reverse
from dogbone.testing.base import BeagleWebTest
from core.models import CollaborationInvite, ExternalInvite, Sentence
from notifications.models import Notification


class ReceivedInvitationsListTestCase(BeagleWebTest):
    def test_200(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'objects': [], 'meta': mock.ANY})

    def test_one_invite_received(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        batch = self.create_batch('Title', other_user)
        document = self.create_document('Title', other_user, pending=False, batch=batch)
        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['invitee']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['inviter']['email'], other_user.email)
        self.assertEqual(data['objects'][0]['document']['title'], 'Title')

    def test_more_invites_received(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')
        batch1 = self.create_batch('Title', other_user)
        document = self.create_document('Title', other_user, pending=False, batch=batch1)
        batch2 = self.create_batch('Title', other_user2)
        document2 = self.create_document('Title2', other_user2, pending=False, batch=batch2)
        batch3 = self.create_batch('Title', other_user3)
        document3 = self.create_document('Title3', other_user3, pending=False, batch=batch3)
        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        CollaborationInvite(document=document2, inviter=other_user2, invitee=self.user).save()
        CollaborationInvite(document=document3, inviter=other_user3, invitee=self.user).save()

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 3)
        self.assertEqual(data['objects'][0]['invitee']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['inviter']['email'], other_user3.email)
        self.assertEqual(data['objects'][0]['document']['title'], 'Title3')

        self.assertEqual(data['objects'][1]['invitee']['email'], self.user.email)
        self.assertEqual(data['objects'][1]['inviter']['email'], other_user2.email)
        self.assertEqual(data['objects'][1]['document']['title'], 'Title2')

        self.assertEqual(data['objects'][2]['invitee']['email'], self.user.email)
        self.assertEqual(data['objects'][2]['inviter']['email'], other_user.email)
        self.assertEqual(data['objects'][2]['document']['title'], 'Title')

    def test_not_authenticated(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_pagination(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')
        document = self.create_document('Title', other_user, pending=False)
        document2 = self.create_document('Title2', other_user2, pending=False)
        document3 = self.create_document('Title3', other_user3, pending=False)
        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        CollaborationInvite(document=document2, inviter=other_user2, invitee=self.user).save()
        CollaborationInvite(document=document3, inviter=other_user3, invitee=self.user).save()

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 3)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('me_received_invitations_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 0,
                          'page_count': 1,
                          'object_count': 3,
                          'page_url': reverse('me_received_invitations_list_view') + '?page=0&rpp=4',
                          'prev_page': None,
                          'prev_page_url': None,
                          'rpp': 4})

    def test_pagination_multiple_pages(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')

        document = self.create_document('Title', other_user, pending=False)
        document2 = self.create_document('Title2', other_user2, pending=False)
        document3 = self.create_document('Title3', other_user3, pending=False)
        document4 = self.create_document('Title4', other_user3, pending=False)
        document5 = self.create_document('Title5', other_user3, pending=False)
        document6 = self.create_document('Title6', other_user3, pending=False)

        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        CollaborationInvite(document=document2, inviter=other_user2, invitee=self.user).save()
        CollaborationInvite(document=document3, inviter=other_user3, invitee=self.user).save()
        CollaborationInvite(document=document4, inviter=other_user3, invitee=self.user).save()
        CollaborationInvite(document=document5, inviter=other_user3, invitee=self.user).save()
        CollaborationInvite(document=document6, inviter=other_user3, invitee=self.user).save()

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 4)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('me_received_invitations_list_view'),
                          'next_page': 1,
                          'next_page_url': reverse('me_received_invitations_list_view') + '?page=1&rpp=4',
                          'page': 0,
                          'page_count': 2,
                          'object_count': 6,
                          'page_url': reverse('me_received_invitations_list_view') + '?page=0&rpp=4',
                          'prev_page': None,
                          'prev_page_url': None,
                          'rpp': 4})

        response = self.client.get(data['meta']['pagination']['next_page_url'])
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('me_received_invitations_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 1,
                          'page_count': 2,
                          'object_count': 6,
                          'page_url': reverse('me_received_invitations_list_view') + '?page=1&rpp=4',
                          'prev_page': 0,
                          'prev_page_url': reverse('me_received_invitations_list_view') + '?page=0&rpp=4',
                          'rpp': 4})

    def test_pagination_custom_rpp(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')

        document = self.create_document('Title', other_user, pending=False)
        document2 = self.create_document('Title2', other_user2, pending=False)
        document3 = self.create_document('Title3', other_user3, pending=False)
        document4 = self.create_document('Title4', other_user3, pending=False)
        document5 = self.create_document('Title5', other_user3, pending=False)
        document6 = self.create_document('Title6', other_user3, pending=False)

        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        CollaborationInvite(document=document2, inviter=other_user2, invitee=self.user).save()
        CollaborationInvite(document=document3, inviter=other_user3, invitee=self.user).save()
        CollaborationInvite(document=document4, inviter=other_user3, invitee=self.user).save()
        CollaborationInvite(document=document5, inviter=other_user3, invitee=self.user).save()
        CollaborationInvite(document=document6, inviter=other_user3, invitee=self.user).save()

        self.login()

        response = self.client.get(api_url + '?rpp=10')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 6)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('me_received_invitations_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 0,
                          'page_count': 1,
                          'object_count': 6,
                          'page_url': reverse('me_received_invitations_list_view') + '?page=0&rpp=10',
                          'prev_page': None,
                          'prev_page_url': None,
                          'rpp': 10})

    def test_pagination_zero_invites(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 0)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('me_received_invitations_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 0,
                          'page_count': 0,
                          'object_count': 0,
                          'page_url': reverse('me_received_invitations_list_view') + '?page=0&rpp=4',
                          'prev_page': None,
                          'prev_page_url': None,
                          'rpp': 4})

    def test_pagination_outside_page(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')
        document = self.create_document('Title', other_user, pending=False)
        document2 = self.create_document('Title2', other_user2, pending=False)
        document3 = self.create_document('Title3', other_user3, pending=False)
        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        CollaborationInvite(document=document2, inviter=other_user2, invitee=self.user).save()
        CollaborationInvite(document=document3, inviter=other_user3, invitee=self.user).save()

        self.login()

        response = self.client.get(api_url + '?page=1')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 0)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('me_received_invitations_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 1,
                          'page_count': 1,
                          'object_count': 3,
                          'page_url': reverse('me_received_invitations_list_view') + '?page=1&rpp=4',
                          'prev_page': 0,
                          'prev_page_url': reverse('me_received_invitations_list_view') + '?page=0&rpp=4',
                          'rpp': 4})

        response = self.client.get(api_url + '?page=2')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 0)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('me_received_invitations_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 2,
                          'page_count': 1,
                          'object_count': 3,
                          'page_url': reverse('me_received_invitations_list_view') + '?page=2&rpp=4',
                          'prev_page': 1,
                          'prev_page_url': reverse('me_received_invitations_list_view') + '?page=1&rpp=4',
                          'rpp': 4})

    def test_search(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')
        document = self.create_document('Apple', other_user, pending=False)
        document2 = self.create_document('Apple and Pear', other_user2, pending=False)
        document3 = self.create_document('Banana', other_user3, pending=False)
        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        CollaborationInvite(document=document2, inviter=other_user2, invitee=self.user).save()
        CollaborationInvite(document=document3, inviter=other_user3, invitee=self.user).save()

        self.login()

        response = self.client.get(api_url + '?q=')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['object_count'], 3)
        self.assertEqual(data['meta']['search']['query'], '')

        response = self.client.get(api_url + '?q=appl')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['object_count'], 2)
        self.assertEqual(data['meta']['search']['query'], 'appl')

    def test_search_spaces(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')
        document = self.create_document('Apple', other_user, pending=False)
        document2 = self.create_document('Apple and Pear', other_user2, pending=False)
        document3 = self.create_document('Banana', other_user3, pending=False)
        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        CollaborationInvite(document=document2, inviter=other_user2, invitee=self.user).save()
        CollaborationInvite(document=document3, inviter=other_user3, invitee=self.user).save()

        self.login()

        response = self.client.get(api_url + '?q=apple and p')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['meta']['pagination']['object_count'], 1)
        self.assertEqual(data['meta']['search']['query'], 'apple and p')


class ReceivedInvitationsDetailTestCase(BeagleWebTest):
    def test_200(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'objects': [], 'meta': mock.ANY})

    def test_not_authenticated(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_invite_delete(self):
        self.make_paid(self.user)
        other_user = self.create_user(
            'some1@email.com',
            'someusername1',
            'somepass1'
        )

        document = self.create_document(
            'Title',
            other_user,
            pending=False
        )

        # Trigger lazy analysis explicitly (otherwise it might be triggered
        # implicitly during serialization, i.e. inside some to_dict call)
        document.analysis_result

        self.assertFalse(Notification.objects.exists())

        CollaborationInvite(
            invitee=self.user,
            inviter=other_user,
            document=document
        ).save()

        collab = CollaborationInvite.objects.filter(
            invitee=self.user,
            inviter=other_user,
            document=document
        ).first()

        self.assertIsNotNone(collab)

        api_url = reverse(
            'document_received_invitations_list_view',
            kwargs={'uuid': document.uuid}
        )

        self.login()

        with mock.patch('django.conf.settings.CELERY_ALWAYS_EAGER', True, create=True):
            response = self.client.delete(api_url, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            actual_data = json.loads(response.content)

            collab.delete()
            expected_data = {'objects': [collab.to_dict()]}

            self.assertEqual(expected_data, actual_data)

            collab = CollaborationInvite.objects.filter(
                inviter=self.user,
                invitee=other_user,
                document=document
            ).first()

            self.assertIsNone(collab)

            self.assertEqual(Notification.objects.count(), 1)

            notif = Notification.objects.first()

            self.assertEqual(notif.actor, self.user)
            self.assertEqual(notif.recipient, other_user)
            self.assertEqual(notif.target, other_user)
            self.assertEqual(notif.verb, 'rejected')
            self.assertEqual(notif.data['render_string'], '(actor) rejected invite from (target) to collaborate on (action_object)')


class IssuedInvitationsListTestCase(BeagleWebTest):

    def test_200(self):
        self.make_paid(self.user)
        api_url = reverse('me_issued_invitations_list_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'objects': []})

    def test_one_invite_issued(self):
        self.make_paid(self.user)
        api_url = reverse('me_issued_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)
        CollaborationInvite(document=document, invitee=other_user, inviter=self.user).save()

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['inviter']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['invitee']['email'], other_user.email)
        self.assertEqual(data['objects'][0]['document']['title'], 'Title')

    def test_more_invites_received(self):
        self.make_paid(self.user)
        api_url = reverse('me_issued_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')
        batch1 = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch1)
        batch2 = self.create_batch('Title2', self.user)
        document2 = self.create_document('Title2', self.user, pending=False, batch=batch2)
        batch3 = self.create_batch('Title', self.user)
        document3 = self.create_document('Title3', self.user, pending=False, batch=batch3)
        CollaborationInvite(document=document, invitee=other_user, inviter=self.user).save()
        CollaborationInvite(document=document2, invitee=other_user2, inviter=self.user).save()
        CollaborationInvite(document=document3, invitee=other_user3, inviter=self.user).save()

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 3)
        self.assertEqual(data['objects'][0]['inviter']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['invitee']['email'], other_user.email)
        self.assertEqual(data['objects'][0]['document']['title'], 'Title')

        self.assertEqual(data['objects'][1]['inviter']['email'], self.user.email)
        self.assertEqual(data['objects'][1]['invitee']['email'], other_user2.email)
        self.assertEqual(data['objects'][1]['document']['title'], 'Title2')

        self.assertEqual(data['objects'][2]['inviter']['email'], self.user.email)
        self.assertEqual(data['objects'][2]['invitee']['email'], other_user3.email)
        self.assertEqual(data['objects'][2]['document']['title'], 'Title3')

    def test_not_authenticated(self):
        self.make_paid(self.user)
        api_url = reverse('me_issued_invitations_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_post(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = {'invitee': 'some@email.com'}
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['objects'][0]['document']['owner']['email'], self.DUMMY_EMAIL)
        self.assertEqual(data['objects'][0]['document']['collaborators'][0]['email'], 'some@email.com')
        self.assertEqual(data['objects'][0]['external'], False)
        self.assertEqual(data['objects'][0]['invitee']['email'], 'some@email.com')
        self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)

        invites = CollaborationInvite.objects.all()
        self.assertEqual(len(invites), 1)
        invite = invites[0]
        self.assertEqual(invite.inviter, self.user)
        self.assertEqual(invite.invitee, other_user)
        self.assertEqual(invite.document, document)

    def test_not_owner(self):
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        third_user = self.create_user('third@email.com', 'third', 'somepass')
        self.make_paid(self.user)
        self.make_paid(other_user)

        document = self.create_document('Title', other_user, pending=False)

        # Invite the user to the document
        CollaborationInvite.objects.create(inviter=other_user, invitee=self.user, document=document)

        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = {'invitee': 'third@email.com'}
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {
            'code': None,
            'http_status': 403,
            'message': 'You are not allowed to invite people to this document',
            'type': 'error'
        })

    def test_post_list(self):
        self.make_paid(self.user)
        other_user1 = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass2')
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = [{'invitee': 'some1@email.com', 'document': document.uuid},
                {'invitee': 'some2@email.com', 'document': document.uuid}]
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['objects'][0]['document']['owner']['email'], self.DUMMY_EMAIL)
        self.assertEqual(data['objects'][0]['external'], False)
        self.assertEqual(data['objects'][0]['invitee']['email'], 'some1@email.com')
        self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)

        self.assertEqual(data['objects'][1]['document']['owner']['email'], self.DUMMY_EMAIL)
        self.assertEqual(data['objects'][1]['external'], False)
        self.assertEqual(data['objects'][1]['invitee']['email'], 'some2@email.com')
        self.assertEqual(data['objects'][1]['inviter']['email'], self.DUMMY_EMAIL)

        invites = CollaborationInvite.objects.all()
        self.assertEqual(len(invites), 2)

    def test_post_no_access(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', other_user, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = {'invitee': self.DUMMY_EMAIL, 'document': document.uuid}
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['objects'], [])

        invites = CollaborationInvite.objects.all()
        self.assertEqual(len(invites), 0)

    def test_post_list_no_access(self):
        self.make_paid(self.user)
        other_user1 = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        self.create_user('some2@email.com', 'someusername2', 'somepass2')
        document = self.create_document('Title', other_user1, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = [{'invitee': 'some1@email.com', 'document': document.uuid},
                {'invitee': 'some2@email.com', 'document': document.uuid}]
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data['objects']), 0)

        invites = CollaborationInvite.objects.all()
        self.assertEqual(len(invites), 0)

    def test_post_sentence_external(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        batch = self.create_batch('My beautiful document', self.user)
        document = self.create_analysed_document('My beautiful document', sentences, self.user, batch=batch)

        api_url = reverse('document_issued_invitations_list_view', kwargs={'uuid': document.uuid}) + '?external=True'
        data = {'invitee': 'some@email.com', 'sentenceIdx': 0}
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['objects']), 1)
        invite = data['objects'][0]
        self.assertEqual(invite['document']['uuid'], document.uuid)
        self.assertEqual(invite['invitee']['email'], 'some@email.com')

        invites = ExternalInvite.objects.all()
        self.assertEqual(len(invites), 1)
        invite = invites[0]

        self.assertIsNotNone(invite.sentence)

        self.assertEqual(invite.sentence.doc.uuid, document.uuid)
        self.assertEqual(document.sentences_pks.index(invite.sentence.pk), 0)

    def test_post_sentence_external_out_of_range(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        batch = self.create_batch('My beautiful document', self.user)
        document = self.create_analysed_document('My beautiful document', sentences, self.user, batch=batch)

        api_url = reverse('document_issued_invitations_list_view', kwargs={'uuid': document.uuid}) + '?external=True'
        data = {'invitee': 'some@email.com', 'sentenceIdx': 2}
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 404)

        invites = ExternalInvite.objects.all()
        self.assertEqual(len(invites), 0)

    def test_post_sentence_external_invalid_index(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        batch = self.create_batch('My beautiful document', self.user)
        document = self.create_analysed_document('My beautiful document', sentences, self.user, batch=batch)

        api_url = reverse('document_issued_invitations_list_view', kwargs={'uuid': document.uuid}) + '?external=True'
        data = {'invitee': 'some@email.com', 'sentenceIdx': 'abc'}
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        invites = ExternalInvite.objects.all()
        self.assertEqual(len(invites), 0)


class DocumentReceivedInvitationsListTestCase(BeagleWebTest):

    def test_200(self):
        self.make_paid(self.user)
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_received_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'objects': []})

    def test_no_access(self):
        self.make_paid(self.user)
        other_user1 = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass2')

        document = self.create_document('Title', other_user1, pending=False)
        CollaborationInvite(document=document, inviter=other_user1, invitee=other_user2).save()

        api_url = reverse('document_received_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)

    def test_one_invite_received(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        batch = self.create_batch('Title', other_user)
        document = self.create_document('Title', other_user, pending=False, batch=batch)
        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        api_url = reverse('document_received_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['invitee']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['inviter']['email'], other_user.email)
        self.assertEqual(data['objects'][0]['document']['title'], 'Title')

    def test_more_invites_received(self):
        self.make_paid(self.user)
        api_url = reverse('me_received_invitations_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', other_user, pending=False, batch=batch)
        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        CollaborationInvite(document=document, inviter=other_user2, invitee=self.user).save()
        CollaborationInvite(document=document, inviter=other_user3, invitee=self.user).save()

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 3)
        self.assertEqual(data['objects'][0]['invitee']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['inviter']['email'], other_user3.email)
        self.assertEqual(data['objects'][0]['document']['title'], 'Title')

        self.assertEqual(data['objects'][1]['invitee']['email'], self.user.email)
        self.assertEqual(data['objects'][1]['inviter']['email'], other_user2.email)
        self.assertEqual(data['objects'][1]['document']['title'], 'Title')

        self.assertEqual(data['objects'][2]['invitee']['email'], self.user.email)
        self.assertEqual(data['objects'][2]['inviter']['email'], other_user.email)
        self.assertEqual(data['objects'][2]['document']['title'], 'Title')

    def test_not_authenticated(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', other_user, pending=False)
        CollaborationInvite(document=document, inviter=other_user, invitee=self.user).save()
        api_url = reverse('document_received_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})


class DocumentIssuedInvitationsListTestCase(BeagleWebTest):

    def test_200(self):
        self.make_paid(self.user)
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'objects': []})

    def test_no_access(self):
        self.make_paid(self.user)
        other_user1 = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass2')

        document = self.create_document('Title', other_user1, pending=False)
        CollaborationInvite(document=document, inviter=other_user1, invitee=other_user2).save()

        api_url = reverse('document_received_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)

    def test_one_invite_issued(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)
        CollaborationInvite(document=document, inviter=self.user, invitee=other_user).save()
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['inviter']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['invitee']['email'], other_user.email)
        self.assertEqual(data['objects'][0]['document']['title'], 'Title')

    def test_more_invites_received(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass')
        other_user3 = self.create_user('some3@email.com', 'someusername3', 'somepass')
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)
        CollaborationInvite(document=document, invitee=other_user, inviter=self.user).save()
        CollaborationInvite(document=document, invitee=other_user2, inviter=self.user).save()
        CollaborationInvite(document=document, invitee=other_user3, inviter=self.user).save()

        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 3)
        self.assertEqual(data['objects'][0]['inviter']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['invitee']['email'], other_user.email)
        self.assertEqual(data['objects'][0]['document']['title'], 'Title')

        self.assertEqual(data['objects'][1]['inviter']['email'], self.user.email)
        self.assertEqual(data['objects'][1]['invitee']['email'], other_user2.email)
        self.assertEqual(data['objects'][1]['document']['title'], 'Title')

        self.assertEqual(data['objects'][2]['inviter']['email'], self.user.email)
        self.assertEqual(data['objects'][2]['invitee']['email'], other_user3.email)
        self.assertEqual(data['objects'][2]['document']['title'], 'Title')

    def test_external_invite(self):
        self.make_paid(self.user)
        document = self.create_document('Title', self.user, pending=False)
        ExternalInvite(inviter=self.user, email='some@email.com', document=document, pending=True).save()
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid}) + '?external=True'

        self.login()
        response = self.client.get(api_url)

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(data['objects']), 1)

        self.assertEqual(data['objects'][0]['document']['owner']['email'], self.DUMMY_EMAIL)
        self.assertEqual(data['objects'][0]['document']['collaborators'][0]['email'], 'some@email.com')
        self.assertEqual(data['objects'][0]['external'], True)
        self.assertEqual(data['objects'][0]['invitee']['email'], 'some@email.com')
        self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)

    def test_mixed_invites(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)
        ExternalInvite(inviter=self.user, email='doesnot@exist.com', document=document, pending=True).save()
        CollaborationInvite(document=document, invitee=other_user, inviter=self.user).save()
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid}) + '?external=True'
        self.login()
        response = self.client.get(api_url)

        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['objects'][0]['document']['owner']['email'], self.DUMMY_EMAIL)
        self.assertEqual(data['objects'][0]['external'], False)
        self.assertEqual(data['objects'][0]['invitee']['email'], other_user.email)
        self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)

        self.assertEqual(data['objects'][1]['document']['owner']['email'], self.DUMMY_EMAIL)
        self.assertEqual(data['objects'][1]['external'], True)
        self.assertEqual(data['objects'][1]['invitee']['email'], 'doesnot@exist.com')
        self.assertEqual(data['objects'][1]['inviter']['email'], self.DUMMY_EMAIL)

    def test_not_authenticated(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', other_user, pending=False)
        CollaborationInvite(document=document, inviter=self.user, invitee=other_user).save()
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_post(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')

        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)

        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = {'invitee': 'some@email.com'}

        with mock.patch('api_v1.invites.endpoints.send_collaboration_invite.delay') as mock_task, \
                mock.patch('authentication.models.OneTimeLoginHash.get_hash') as mock_hash:
            mock_hash.return_value = 'aB1cD2eF3'

            response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
            data = json.loads(response.content)
            self.assertEqual(response.status_code, 200)

            self.assertEqual(data['objects'][0]['document']['owner']['email'], self.DUMMY_EMAIL)
            self.assertEqual(data['objects'][0]['document']['collaborators'][0]['email'], 'some@email.com')
            self.assertEqual(data['objects'][0]['external'], False)
            self.assertEqual(data['objects'][0]['invitee']['email'], 'some@email.com')
            self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)

            invites = CollaborationInvite.objects.all()
            self.assertEqual(len(invites), 1)
            invite = invites[0]
            self.assertEqual(invite.inviter, self.user)
            self.assertEqual(invite.invitee, other_user)
            self.assertEqual(invite.document, document)

            mock_task.assert_called_once_with(invite.pk, mock.ANY)

            from core.tools import login_resource_url
            follow_url = login_resource_url(other_user, document.get_report_url())
            self.assertTrue(mock_task.call_args[0][1].endswith(follow_url))

    def test_post_with_sentence(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')

        sentences = ['I like flowers.', 'I don\'t like butter.']
        batch = self.create_batch('My beautiful document', self.user)
        document = self.create_analysed_document('My beautiful document', sentences, self.user, batch=batch)

        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = {'invitee': 'some@email.com', 'sentenceIdx': 0}
        sentence = Sentence.objects.get(pk=document.sentences_pks[0])

        with mock.patch('api_v1.invites.endpoints.send_collaboration_invite.delay') as mock_task, \
                mock.patch('authentication.models.OneTimeLoginHash.get_hash') as mock_hash:
            mock_hash.return_value = 'aB1cD2eF3'

            response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
            data = json.loads(response.content)
            self.assertEqual(response.status_code, 200)

            self.assertEqual(data['objects'][0]['document']['owner']['email'], self.DUMMY_EMAIL)
            self.assertEqual(data['objects'][0]['document']['collaborators'][0]['email'], 'some@email.com')
            self.assertEqual(data['objects'][0]['external'], False)
            self.assertEqual(data['objects'][0]['invitee']['email'], 'some@email.com')
            self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)

            invites = CollaborationInvite.objects.all()
            self.assertEqual(len(invites), 1)
            invite = invites[0]
            self.assertEqual(invite.inviter, self.user)
            self.assertEqual(invite.invitee, other_user)
            self.assertEqual(invite.document, document)
            self.assertEqual(invite.sentence, sentence)

            mock_task.assert_called_once_with(invite.pk, mock.ANY)

            from core.tools import login_resource_url
            follow_url = login_resource_url(other_user, sentence.get_report_url(0))
            self.assertTrue(mock_task.call_args[0][1].endswith(follow_url))

    def test_invite_yourself(self):
        self.make_paid(self.user)
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.login()
        data = {'invitee': self.DUMMY_EMAIL}

        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(CollaborationInvite.objects.all()), 0)

    def test_double_invite(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.login()
        data = {'invitee': other_user.email}
        with mock.patch('api_v1.invites.endpoints.send_collaboration_invite.delay') as _:
            response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(CollaborationInvite.objects.all()), 1)

            response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
            self.assertEqual(response.status_code, 403)
            self.assertEqual(len(CollaborationInvite.objects.all()), 1)

    def test_post_external(self):
        self.make_paid(self.user)
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid}) + '?external=True'
        self.login()
        data = {'invitee': 'some@email.com'}
        with mock.patch('api_v1.invites.endpoints.send_external_invite.delay') as mock_task:
            response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
            data = json.loads(response.content)
            self.assertEqual(response.status_code, 200)

            self.assertEqual(data['objects'][0]['document']['uuid'], document.uuid)
            self.assertEqual(data['objects'][0]['document']['collaborators'][0]['email'], 'some@email.com')
            self.assertEqual(data['objects'][0]['document']['collaborators'][0]['pending'], True)
            self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)
            self.assertEqual(data['objects'][0]['external'], True)
            self.assertEqual(data['objects'][0]['invitee']['email'], 'some@email.com')
            self.assertEqual(data['objects'][0]['invitee']['pending'], True)
            external_invite = ExternalInvite.objects.all()[0]
            mock_task.assert_called_once_with(external_invite.pk, mock.ANY)

    def test_post_list(self):
        self.make_paid(self.user)
        self.create_user('some1@email.com', 'someusername1', 'somepass1')
        self.create_user('some2@email.com', 'someusername2', 'somepass2')
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = [{'invitee': 'some1@email.com'},
                {'invitee': 'some2@email.com'}]

        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        with mock.patch('api_v1.invites.endpoints.send_collaboration_invite.delay') as mock_task:
            self.assertEqual(data['objects'][0]['document']['owner']['email'], self.DUMMY_EMAIL)
            self.assertEqual(data['objects'][0]['external'], False)
            self.assertEqual(data['objects'][0]['invitee']['email'], 'some1@email.com')
            self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)

            self.assertEqual(data['objects'][1]['document']['owner']['email'], self.DUMMY_EMAIL)
            self.assertEqual(data['objects'][1]['external'], False)
            self.assertEqual(data['objects'][1]['invitee']['email'], 'some2@email.com')
            self.assertEqual(data['objects'][1]['inviter']['email'], self.DUMMY_EMAIL)

            invites = CollaborationInvite.objects.all()
            self.assertEqual(len(invites), 2)

    def test_post_no_access(self):
        self.make_paid(self.user)
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', other_user, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = {'invitee': self.DUMMY_EMAIL}
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['objects'], [])

        invites = CollaborationInvite.objects.all()
        self.assertEqual(len(invites), 0)

    def test_post_list_no_access(self):
        self.make_paid(self.user)
        other_user1 = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        self.create_user('some2@email.com', 'someusername2', 'somepass2')
        document = self.create_document('Title', other_user1, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})
        self.login()
        data = [{'invitee': 'some1@email.com'},
                {'invitee': 'some2@email.com'}]
        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data['objects']), 0)

        invites = CollaborationInvite.objects.all()
        self.assertEqual(len(invites), 0)

    def test_invite_delete(self):
        self.make_paid(self.user)
        other_user = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.assertFalse(Notification.objects.exists())

        CollaborationInvite(inviter=self.user, invitee=other_user, document=document).save()
        collab = CollaborationInvite.objects.filter(inviter=self.user, invitee=other_user, document=document).first()
        self.assertIsNotNone(collab)

        self.login()
        data = {'email': 'some1@email.com'}
        with mock.patch('django.conf.settings.CELERY_ALWAYS_EAGER', True, create=True):
            response = self.client.delete(api_url, data=json.dumps(data), content_type='application/json')
            data = json.loads(response.content)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data['objects'][0]['document']['uuid'], document.uuid)
            self.assertEqual(data['objects'][0]['document']['analysis'], None)
            self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)
            self.assertEqual(data['objects'][0]['invitee']['email'], other_user.email)
            self.assertEqual(data['objects'][0]['external'], False)
            self.assertEqual(len(data['objects']), 1)

            collab = CollaborationInvite.objects.filter(inviter=self.user, invitee=other_user, document=document).first()
            self.assertIsNone(collab)

            self.assertEqual(Notification.objects.count(), 1)

            notif = Notification.objects.first()

            self.assertEqual(notif.actor, self.user)
            self.assertEqual(notif.recipient, other_user)
            self.assertEqual(notif.target, other_user)
            self.assertEqual(notif.verb, 'revoked')
            self.assertEqual(notif.data['render_string'], '(actor) revoked access from (target) to collaborate on (action_object)')

    def test_invite_delete_external(self):
        self.make_paid(self.user)
        batch = self.create_batch('Title', self.user)
        document = self.create_document('Title', self.user, pending=False, batch=batch)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid}) + '?external=True'

        ExternalInvite(inviter=self.user, email='some1@email.com', document=document, pending=True).save()
        self.login()
        data = {'email': 'some1@email.com'}
        response = self.client.delete(api_url, data=json.dumps(data), content_type='application/json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['objects'][0]['document']['uuid'], document.uuid)
        self.assertEqual(data['objects'][0]['document']['analysis'], None)
        self.assertEqual(data['objects'][0]['inviter']['email'], self.DUMMY_EMAIL)
        self.assertEqual(data['objects'][0]['invitee']['email'], 'some1@email.com')
        self.assertEqual(data['objects'][0]['external'], True)
        self.assertEqual(len(data['objects']), 1)

        try:
            ExternalInvite.objects.get(inviter=self.user, email='some1@email.com', document=document, pending=True)
            self.assertTrue(False)
        except ExternalInvite.DoesNotExist:
            pass

    def test_invite_delete_external_404(self):
        self.make_paid(self.user)
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid}) + '?external=True'
        self.login()
        data = {'email': 'some1@email.com'}
        response = self.client.delete(api_url, data=json.dumps(data), content_type='application/json')
        json.loads(response.content)
        self.assertEqual(response.status_code, 404)

    def test_invite_delete_404(self):
        self.make_paid(self.user)
        self.create_user('some1@email.com', 'someusername1', 'somepass1')
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.login()
        data = {'email': 'some1@email.com'}
        response = self.client.delete(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_invite_delete_no_access(self):
        self.make_paid(self.user)
        other_user1 = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass2')
        document = self.create_document('Title', other_user1, pending=False)
        CollaborationInvite(inviter=other_user1, invitee=other_user2, document=document).save()
        CollaborationInvite(inviter=other_user1, invitee=self.user, document=document).save()

        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid})

        self.login()
        data = {'email': 'some2@email.com'}
        response = self.client.delete(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_invite_delete_external_no_access(self):
        self.make_paid(self.user)
        other_user1 = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        document = self.create_document('Title', other_user1, pending=False)
        ExternalInvite(inviter=other_user1, email='tralala@lala.com', document=document, pending=True).save()

        api_url = reverse('document_issued_invitations_list_view',
                          kwargs={'uuid': document.uuid}) + '?external=True'

        self.login()
        data = {'email': 'tralala@lala.com'}
        response = self.client.delete(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 404)
