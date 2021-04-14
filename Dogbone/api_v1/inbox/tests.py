import json
import mock
from core.models import Sentence
from core.tasks import store_activity_notification
from dogbone.testing.base import BeagleWebTest
from django.urls import reverse
from notifications.models import Notification


class InboxDetailEndpointViewTest(BeagleWebTest):

    def test_200(self):
        self.make_paid(self.user)
        document = self.create_document('Some Title', self.user, pending=False)
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.action_object = document
        notif.save()

        api_url = reverse('inbox_detail_view', kwargs={'id': notif.pk})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        document_upload_count = self.user.details.document_upload_count

        self.assertEqual(data,
                {'action_object': {'created': mock.ANY,
                                   'original_name': 'Some Title.pdf',
                                   'owner': {'avatar': '/static/img/mug.png',
                                             'email': self.DUMMY_EMAIL,
                                             'first_name': None,
                                             'id': mock.ANY,
                                             'last_name': None,
                                             'pending': False,
                                             'job_title': None,
                                             'company': None,
                                             'username': self.DUMMY_USERNAME,
                                             'last_login': mock.ANY,
                                             'date_joined': mock.ANY,
                                             'tags': mock.ANY,
                                             'keywords': mock.ANY,
                                             'settings': mock.ANY,
                                             'is_paid': True,
                                             'had_trial': mock.ANY,
                                             'is_super': False,
                                             'document_upload_count': document_upload_count,
                                             'phone': None},
                 'title': 'Some Title',
                 'uuid': mock.ANY},
                 'action_object_type': 'document',
                 'actor': {'avatar': '/static/img/mug.png',
                           'email': self.DUMMY_EMAIL,
                           'first_name': None,
                           'id': mock.ANY,
                           'last_name': None,
                           'pending': False,
                           'job_title': None,
                           'company': None,
                           'username': self.DUMMY_USERNAME,
                           'tags': mock.ANY,
                           'keywords': mock.ANY,
                           'settings': mock.ANY,
                           'last_login': mock.ANY,
                           'date_joined': mock.ANY,
                           'is_paid': True,
                           'had_trial': mock.ANY,
                           'is_super': False,
                           'document_upload_count': document_upload_count,
                           'phone': None},
                 'actor_type': 'user',
                 'data': None,
                 'description': None,
                 'id': mock.ANY,
                 'level': 'info',
                 'read': False,
                 'render_string': None,
                 'suggested_display': None,
                 'target': {'avatar': '/static/img/mug.png',
                            'email': 'myemail@hhh.com',
                            'first_name': None,
                            'id': mock.ANY,
                            'last_name': None,
                            'pending': False,
                            'job_title': None,
                            'company': None,
                            'username': 'new_username',
                            'is_paid': False,
                            'had_trial': mock.ANY,
                            'is_super': False,
                            'tags': mock.ANY,
                            'keywords': mock.ANY,
                            'settings': mock.ANY,
                            'date_joined': mock.ANY,
                            'last_login': mock.ANY,
                            'document_upload_count': 0,
                            'phone': None},
                 'target_type': 'user',
                 'timestamp': mock.ANY,
                 'verb': 'has invited'})

        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['meta']['unread_count'], 1)

    def test_put1(self):
        """
        Mark it as read
        """
        self.make_paid(self.user)
        document = self.create_document('Some Title', self.user, pending=False)
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.action_object = document
        notif.save()

        api_url = reverse('inbox_detail_view', kwargs={'id': notif.pk})
        self.login()
        response = self.client.put(api_url, data=json.dumps({'read': True}), content_type='application/json')

        data = json.loads(response.content)

        document_upload_count = self.user.details.document_upload_count

        self.assertEqual(data,
                {'action_object': {'created': mock.ANY,
                                   'original_name': 'Some Title.pdf',
                                   'owner': {'avatar': '/static/img/mug.png',
                                             'email': self.DUMMY_EMAIL,
                                             'first_name': None,
                                             'id': mock.ANY,
                                             'last_name': None,
                                             'pending': False,
                                             'job_title': None,
                                             'company': None,
                                             'tags': mock.ANY,
                                             'keywords': mock.ANY,
                                             'settings': mock.ANY,
                                             'username': self.DUMMY_USERNAME,
                                             'last_login': mock.ANY,
                                             'date_joined': mock.ANY,
                                             'is_paid': True,
                                             'had_trial': mock.ANY,
                                             'is_super': False,
                                             'document_upload_count': document_upload_count,
                                             'phone': None},
                 'title': 'Some Title',
                 'uuid': mock.ANY},
                 'action_object_type': 'document',
                 'actor': {'avatar': '/static/img/mug.png',
                           'email': self.DUMMY_EMAIL,
                           'first_name': None,
                           'id': mock.ANY,
                           'last_name': None,
                           'pending': False,
                           'job_title': None,
                           'company': None,
                           'tags': mock.ANY,
                           'keywords': mock.ANY,
                           'settings': mock.ANY,
                           'username': self.DUMMY_USERNAME,
                           'last_login': mock.ANY,
                           'date_joined': mock.ANY,
                           'is_paid': True,
                           'had_trial': mock.ANY,
                           'is_super': False,
                           'document_upload_count': document_upload_count,
                           'phone': None},
                 'actor_type': 'user',
                 'data': None,
                 'description': None,
                 'id': mock.ANY,
                 'level': 'info',
                 'read': True,
                 'render_string': None,
                 'suggested_display': None,
                 'target': {'avatar': '/static/img/mug.png',
                            'email': 'myemail@hhh.com',
                            'first_name': None,
                            'id': mock.ANY,
                            'last_name': None,
                            'pending': False,
                            'job_title': None,
                            'company': None,
                            'tags': mock.ANY,
                            'keywords': mock.ANY,
                            'settings': mock.ANY,
                            'username': 'new_username',
                            'last_login': mock.ANY,
                            'date_joined': mock.ANY,
                            'is_paid': False,
                            'had_trial': mock.ANY,
                            'is_super': False,
                            'document_upload_count': 0,
                            'phone': None},
                 'target_type': 'user',
                 'timestamp': mock.ANY,
                 'verb': 'has invited'})

        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['meta']['unread_count'], 0)

    def test_put2(self):
        """
        Mark it as read
        """
        self.make_paid(self.user)
        document = self.create_document('Some Title', self.user, pending=False)
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.action_object = document
        notif.save()

        api_url = reverse('inbox_detail_view', kwargs={'id': notif.pk})
        self.login()
        response = self.client.put(api_url, data=json.dumps({'unread': False}), content_type='application/json')

        data = json.loads(response.content)

        document_upload_count = self.user.details.document_upload_count

        self.assertEqual(data,
                {'action_object': {'created': mock.ANY,
                                   'original_name': 'Some Title.pdf',
                                   'owner': {'avatar': '/static/img/mug.png',
                                             'email': self.DUMMY_EMAIL,
                                             'first_name': None,
                                             'id': mock.ANY,
                                             'last_name': None,
                                             'pending': False,
                                             'job_title': None,
                                             'company': None,
                                             'tags': mock.ANY,
                                             'keywords': mock.ANY,
                                             'settings': mock.ANY,
                                             'username': self.DUMMY_USERNAME,
                                             'last_login': mock.ANY,
                                             'date_joined': mock.ANY,
                                             'is_paid': True,
                                             'had_trial': mock.ANY,
                                             'is_super': False,
                                             'document_upload_count': document_upload_count,
                                             'phone': None},
                 'title': 'Some Title',
                 'uuid': mock.ANY},
                 'action_object_type': 'document',
                 'actor': {'avatar': '/static/img/mug.png',
                           'email': self.DUMMY_EMAIL,
                           'first_name': None,
                           'id': mock.ANY,
                           'last_name': None,
                           'pending': False,
                           'job_title': None,
                           'company': None,
                           'tags': mock.ANY,
                           'keywords': mock.ANY,
                           'settings': mock.ANY,
                           'username': self.DUMMY_USERNAME,
                           'last_login': mock.ANY,
                           'date_joined': mock.ANY,
                           'is_paid': True,
                           'had_trial': mock.ANY,
                           'is_super': False,
                           'document_upload_count': document_upload_count,
                           'phone': None},
                 'actor_type': 'user',
                 'data': None,
                 'description': None,
                 'id': mock.ANY,
                 'level': 'info',
                 'read': True,
                 'render_string': None,
                 'suggested_display': None,
                 'target': {'avatar': '/static/img/mug.png',
                            'email': 'myemail@hhh.com',
                            'first_name': None,
                            'id': mock.ANY,
                            'last_name': None,
                            'pending': False,
                            'job_title': None,
                            'company': None,
                            'tags': mock.ANY,
                            'keywords': mock.ANY,
                            'settings': mock.ANY,
                            'username': 'new_username',
                            'last_login': mock.ANY,
                            'date_joined': mock.ANY,
                            'is_paid': False,
                            'had_trial': mock.ANY,
                            'is_super': False,
                            'document_upload_count': 0,
                            'phone': None},
                 'target_type': 'user',
                 'timestamp': mock.ANY,
                 'verb': 'has invited'})

        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['meta']['unread_count'], 0)

    def test_put3(self):
        """
        Mark it as read and then mark it as unread
        """
        self.make_paid(self.user)
        document = self.create_document('Some Title', self.user, pending=False)
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.action_object = document
        notif.save()

        api_url = reverse('inbox_detail_view', kwargs={'id': notif.pk})
        self.login()
        response = self.client.put(api_url, data=json.dumps({'read': True}), content_type='application/json')
        response = self.client.put(api_url, data=json.dumps({'read': False}), content_type='application/json')

        data = json.loads(response.content)

        document_upload_count = self.user.details.document_upload_count

        self.assertEqual(data,
                {'action_object': {'created': mock.ANY,
                                   'original_name': 'Some Title.pdf',
                                   'owner': {'avatar': '/static/img/mug.png',
                                             'email': self.DUMMY_EMAIL,
                                             'first_name': None,
                                             'id': mock.ANY,
                                             'last_name': None,
                                             'pending': False,
                                             'job_title': None,
                                             'company': None,
                                             'tags': mock.ANY,
                                             'keywords': mock.ANY,
                                             'settings': mock.ANY,
                                             'username': self.DUMMY_USERNAME,
                                             'is_paid': True,
                                             'had_trial': mock.ANY,
                                             'is_super': False,
                                             'date_joined': mock.ANY,
                                             'last_login': mock.ANY,
                                             'document_upload_count': document_upload_count,
                                             'phone': None},
                 'title': 'Some Title',
                 'uuid': mock.ANY},
                 'action_object_type': 'document',
                 'actor': {'avatar': '/static/img/mug.png',
                           'email': self.DUMMY_EMAIL,
                           'first_name': None,
                           'id': mock.ANY,
                           'last_name': None,
                           'pending': False,
                           'job_title': None,
                           'company': None,
                           'tags': mock.ANY,
                           'keywords': mock.ANY,
                           'settings': mock.ANY,
                           'username': self.DUMMY_USERNAME,
                           'is_paid': True,
                           'had_trial': mock.ANY,
                           'is_super': False,
                           'date_joined': mock.ANY,
                           'last_login': mock.ANY,
                           'document_upload_count': document_upload_count,
                           'phone': None},
                 'actor_type': 'user',
                 'data': None,
                 'description': None,
                 'id': mock.ANY,
                 'level': 'info',
                 'read': False,
                 'render_string': None,
                 'suggested_display': None,
                 'target': {'avatar': '/static/img/mug.png',
                            'email': 'myemail@hhh.com',
                            'first_name': None,
                            'id': mock.ANY,
                            'last_name': None,
                            'pending': False,
                            'is_paid': False,
                            'had_trial': mock.ANY,
                            'is_super': False,
                            'company': None,
                            'tags': mock.ANY,
                            'keywords': mock.ANY,
                            'settings': mock.ANY,
                            'job_title': None,
                            'date_joined': mock.ANY,
                            'last_login': mock.ANY,
                            'username': 'new_username',
                            'document_upload_count': 0,
                            'phone': None},
                 'target_type': 'user',
                 'timestamp': mock.ANY,
                 'verb': 'has invited'})

        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['meta']['unread_count'], 1)


class InboxEndpointListViewTest(BeagleWebTest):

    def test_200(self):
        self.make_paid(self.user)
        api_url = reverse('inbox_list_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'objects': [], 'meta': mock.ANY})

    def test_one_notification(self):
        self.make_paid(self.user)
        document = self.create_document('Some Title', self.user, pending=False)
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.action_object = document
        notif.save()

        api_url = reverse('inbox_list_view')

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0],
            {'action_object': {'created': mock.ANY,
                               'original_name': 'Some Title.pdf',
                               'owner': {'avatar': mock.ANY,
                                         'email': self.DUMMY_EMAIL,
                                         'first_name': None,
                                         'id': mock.ANY,
                                         'last_name': None,
                                         'pending': False,
                                         'job_title': None,
                                         'company': None,
                                         'tags': mock.ANY,
                                         'keywords': mock.ANY,
                                         'settings': mock.ANY,
                                         'date_joined': mock.ANY,
                                         'last_login': mock.ANY,
                                         'is_super': False,
                                         'is_paid': True,
                                         'had_trial': mock.ANY,
                                         'username': self.DUMMY_USERNAME,
                                         'document_upload_count': 1,
                                         'phone': None},
                               'title': 'Some Title',
                               'uuid': document.uuid},
               'action_object_type': 'document',
               'actor': {'avatar': mock.ANY,
                         'email': self.DUMMY_EMAIL,
                         'first_name': None,
                         'id': mock.ANY,
                         'last_name': None,
                         'pending': False,
                         'job_title': None,
                         'company': None,
                         'tags': mock.ANY,
                         'keywords': mock.ANY,
                         'settings': mock.ANY,
                         'date_joined': mock.ANY,
                         'last_login': mock.ANY,
                         'is_super': False,
                         'is_paid': True,
                         'had_trial': mock.ANY,
                         'username': self.DUMMY_USERNAME,
                         'document_upload_count': 1,
                         'phone': None},
               'actor_type': 'user',
               'data': None,
               'description': None,
               'id': mock.ANY,
               'level': 'info',
               'read': False,
               'render_string': None,
               'suggested_display': None,
               'target': {'avatar': mock.ANY,
                          'email': other_user.email,
                          'first_name': None,
                          'id': mock.ANY,
                          'last_name': None,
                          'pending': False,
                          'job_title': None,
                          'username': other_user.username,
                          'last_login': mock.ANY,
                          'date_joined': mock.ANY,
                          'company': None,
                          'tags': mock.ANY,
                          'keywords': mock.ANY,
                          'settings': mock.ANY,
                          'is_paid': False,
                          'had_trial': mock.ANY,
                          'is_super': False,
                          'document_upload_count': 0,
                          'phone': None},
               'target_type': 'user',
               'timestamp': mock.ANY,
               'url': reverse('report', kwargs={'uuid': document.uuid}),
               'verb': 'has invited'})

        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('inbox_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'object_count': 1,
                          'page': 0,
                          'page_count': 1,
                          'page_url': reverse('inbox_list_view') + '?page=0&rpp=20',
                          'prev_page': None,
                          'prev_page_url': None,
                          'rpp': 20})

        self.assertEqual(data['meta']['unread_count'], 1)

    def test_sentence_revision_changed(self):
        """
        Check that the notification updates its sentence, if the sentence is not up to date
        """
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document',
                                                 sentences, self.user)

        sentence = Sentence.objects.get(pk=document.sentences_pks[0])
        sentence.like(self.user)

        # Store the corresponding notification for the like action
        store_activity_notification(
            actor_id=self.user.id,
            recipient_id=self.user.id,
            verb='liked',
            target_id=sentence.id,
            target_type="Sentence",
            action_object_id=document.id,
            action_object_type="Document",
            render_string="(actor) liked a clause on (action_object)",
            transient=False)

        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['url'], '/report/%s#/context-view?idx=0' % document.uuid)

        sentence.edit(self.user, 'Whole new s$%t!', [])

        # Store the corresponding notification for the edit action
        store_activity_notification(
            actor_id=self.user.id,
            recipient_id=self.user.id,
            verb='edited',
            target_id=sentence.id,
            target_type="Sentence",
            action_object_id=document.id,
            action_object_type="Document",
            render_string="(actor) edited a clause on (action_object)",
            transient=False)

        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['objects'][0]['url'], '/report/%s#/context-view?idx=0' % document.uuid)
        self.assertEqual(data['objects'][1]['url'], '/report/%s#/context-view?idx=0' % document.uuid)


class InboxMarkAllViewTest(BeagleWebTest):

    def setUpTest(self):
        """
        A secondary set up method (not to override the setUp in the
        BeagleWebTest base class)
        """
        self.make_paid(self.user)
        document = self.create_document('Some Title', self.user, pending=False)
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.action_object = document
        notif.save()

        notif2 = Notification()
        notif2.actor = self.user
        notif2.recipient = self.user
        notif2.verb = 'has uninvited'
        notif2.target = other_user
        notif2.action_object = document
        notif2.save()
        self.login()

    def test_mark_all_read(self):
        self.setUpTest()
        self.make_paid(self.user)
        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['meta']['pagination']['object_count'], 2)
        self.assertEqual(data['meta']['unread_count'], 2)

        api_url = reverse('inbox_mark_all_view')
        response = self.client.post(
            api_url, data=json.dumps({'read': True}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['meta']['pagination']['object_count'], 2)
        self.assertEqual(data['meta']['unread_count'], 0) # the real test

    def test_mark_all_unread(self):
        self.setUpTest()
        self.make_paid(self.user)
        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['meta']['pagination']['object_count'], 2)
        self.assertEqual(data['meta']['unread_count'], 2)

        api_url = reverse('inbox_mark_all_view')

        # mark them all read
        response = self.client.post(api_url, data=json.dumps({'read': True}), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        # mark all unread again
        response = self.client.post(api_url, data=json.dumps({'unread': True }), content_type="application/json")
        self.assertEqual(response.status_code, 200)

        api_url = reverse('inbox_list_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['meta']['pagination']['object_count'], 2)
        self.assertEqual(data['meta']['unread_count'], 2)
