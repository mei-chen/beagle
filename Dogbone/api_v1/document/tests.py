# -*- coding: utf-8 -*-

import json
import mock
import tempfile
from core.models import (
    CollaborationInvite, Document, ExternalInvite, UserLastViewDate
)

from portal.models import WrongAnalysisFlag
from dogbone.testing.base import BeagleWebTest
from beagle_realtime.notifications import NotificationManager
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.utils import override_settings
from django.utils.timezone import get_current_timezone


class DocumentListTest(BeagleWebTest):
    def test_200(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'objects': [], 'meta': mock.ANY})

    def test_one_document(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        batch = self.create_batch('Title', self.user)
        self.create_document('Title', self.user, pending=False, batch=batch)

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['objects'][0]['owner']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['batch_name'], 'Title')

    def test_more_documents(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')
        batch1 = self.create_batch('Title', self.user)
        self.create_document('Title', self.user, pending=False, batch=batch1)
        batch2 = self.create_batch('Title2', self.user)
        self.create_document('Title2', self.user, pending=False, batch=batch2)
        batch3 = self.create_batch('Title3', self.user)
        self.create_document('Title3', self.user, pending=False, batch=batch3)

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 3)
        self.assertEqual(data['objects'][2]['owner']['email'], self.user.email)
        self.assertEqual(data['objects'][2]['batch_name'], 'Title')

        self.assertEqual(data['objects'][1]['owner']['email'], self.user.email)
        self.assertEqual(data['objects'][1]['batch_name'], 'Title2')

        self.assertEqual(data['objects'][0]['owner']['email'], self.user.email)
        self.assertEqual(data['objects'][0]['batch_name'], 'Title3')

    def test_not_authenticated(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})

    def test_pagination(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        batch1 = self.create_batch('Title', self.user)
        self.create_document('Title', self.user, pending=False, batch=batch1)
        batch2 = self.create_batch('Title2', self.user)
        self.create_document('Title2', self.user, pending=False, batch=batch2)
        batch3 = self.create_batch('Title3', self.user)
        self.create_document('Title3', self.user, pending=False, batch=batch3)
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 3)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('document_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 0,
                          'page_count': 1,
                          'object_count': 3,
                          'page_url': reverse('document_list_view') + '?page=0&rpp=5',
                          'prev_page': None,
                          'prev_page_url': None,
                          'rpp': 5})

    def test_pagination_multiple_pages(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        batch1 = self.create_batch('Title', self.user)
        self.create_document('Title', self.user, pending=False, batch=batch1)
        batch2 = self.create_batch('Title2', self.user)
        self.create_document('Title2', self.user, pending=False, batch=batch2)
        batch3 = self.create_batch('Title3', self.user)
        self.create_document('Title3', self.user, pending=False, batch=batch3)
        batch4 = self.create_batch('Title4', self.user)
        self.create_document('Title4', self.user, pending=False, batch=batch4)
        batch5 = self.create_batch('Title5', self.user)
        self.create_document('Title5', self.user, pending=False, batch=batch5)
        batch6 = self.create_batch('Title6', self.user)
        self.create_document('Title6', self.user, pending=False, batch=batch6)

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 5)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('document_list_view'),
                          'next_page': 1,
                          'next_page_url': reverse('document_list_view') + '?page=1&rpp=5',
                          'page': 0,
                          'page_count': 2,
                          'object_count': 6,
                          'page_url': reverse('document_list_view') + '?page=0&rpp=5',
                          'prev_page': None,
                          'prev_page_url': None,
                          'rpp': 5})

        response = self.client.get(data['meta']['pagination']['next_page_url'])
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('document_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 1,
                          'page_count': 2,
                          'object_count': 6,
                          'page_url': reverse('document_list_view') + '?page=1&rpp=5',
                          'prev_page': 0,
                          'prev_page_url': reverse('document_list_view') + '?page=0&rpp=5',
                          'rpp': 5})

    def test_pagination_custom_rpp(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        batch1 = self.create_batch('Title', self.user)
        self.create_document('Title', self.user, pending=False, batch=batch1)
        batch2 = self.create_batch('Title2', self.user)
        self.create_document('Title2', self.user, pending=False, batch=batch2)
        batch3 = self.create_batch('Title3', self.user)
        self.create_document('Title3', self.user, pending=False, batch=batch3)
        batch4 = self.create_batch('Title4', self.user)
        self.create_document('Title4', self.user, pending=False, batch=batch4)
        batch5 = self.create_batch('Title5', self.user)
        self.create_document('Title5', self.user, pending=False, batch=batch5)
        batch6 = self.create_batch('Title6', self.user)
        self.create_document('Title6', self.user, pending=False, batch=batch6)

        self.login()

        response = self.client.get(api_url + '?rpp=10')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 6)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('document_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 0,
                          'page_count': 1,
                          'object_count': 6,
                          'page_url': reverse('document_list_view') + '?page=0&rpp=10',
                          'prev_page': None,
                          'prev_page_url': None,
                          'rpp': 10})

    def test_pagination_zero_documents(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 0)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('document_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 0,
                          'page_count': 0,
                          'object_count': 0,
                          'page_url': reverse('document_list_view') + '?page=0&rpp=5',
                          'prev_page': None,
                          'prev_page_url': None,
                          'rpp': 5})

    def test_pagination_outside_page(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        batch1 = self.create_batch('Title', self.user)
        self.create_document('Title', self.user, pending=False, batch=batch1)
        batch2 = self.create_batch('Title2', self.user)
        self.create_document('Title2', self.user, pending=False, batch=batch2)
        batch3 = self.create_batch('Title3', self.user)
        self.create_document('Title3', self.user, pending=False, batch=batch3)

        self.login()

        response = self.client.get(api_url + '?page=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['objects']), 0)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('document_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 1,
                          'page_count': 1,
                          'object_count': 3,
                          'page_url': reverse('document_list_view') + '?page=1&rpp=5',
                          'prev_page': 0,
                          'prev_page_url': reverse('document_list_view') + '?page=0&rpp=5',
                          'rpp': 5})

        response = self.client.get(api_url + '?page=2')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 0)
        self.assertEqual(data['meta']['pagination'],
                         {'base_url': reverse('document_list_view'),
                          'next_page': None,
                          'next_page_url': None,
                          'page': 2,
                          'page_count': 1,
                          'object_count': 3,
                          'page_url': reverse('document_list_view') + '?page=2&rpp=5',
                          'prev_page': 1,
                          'prev_page_url': reverse('document_list_view') + '?page=1&rpp=5',
                          'rpp': 5})

    def test_search(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        batch1 = self.create_batch('apples', self.user)
        self.create_document('apples', self.user, pending=False, batch=batch1)
        batch2 = self.create_batch('oranges and apples', self.user)
        self.create_document('oranges and apples', self.user, pending=False, batch=batch2)
        batch3 = self.create_batch('Apples and coconuts', self.user)
        self.create_document('Apples and coconuts', self.user, pending=False, batch=batch3)
        batch4 = self.create_batch('coconuts and almonds', self.user)
        self.create_document('coconuts and almonds', self.user, pending=False, batch=batch4)
        batch5 = self.create_batch('butter and some milk', self.user)
        self.create_document('butter and some milk', self.user, pending=False, batch=batch5)
        batch6 = self.create_batch('Apple and butter', self.user)
        self.create_document('Apple and butter', self.user, pending=False, batch=batch6)

        self.login()
        response = self.client.get(api_url + '?q=apple')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 4)
        self.assertEqual(data['meta']['pagination']['object_count'], 4)

        titles = [d['batch_name'] for d in data['objects']]
        self.assertEqual(len(titles), 4)
        self.assertEqual(set(titles), set(['Apple and butter', 'Apples and coconuts', 'oranges and apples', 'apples']))
        self.assertEqual(data['meta']['search']['query'], 'apple')

        response = self.client.get(api_url + '?q=butter')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)
        self.assertEqual(data['meta']['pagination']['object_count'], 2)
        titles = [d['batch_name'] for d in data['objects']]
        self.assertEqual(len(titles), 2)
        self.assertEqual(set(titles), set(['Apple and butter', 'butter and some milk']))

        self.assertEqual(data['meta']['search']['query'], 'butter')

    def test_search_case_insensitive(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        batch_1 = self.create_batch('apples', self.user)
        self.create_document('apples', self.user, pending=False, batch=batch_1)
        batch_2 = self.create_batch('oranges and apples', self.user)
        self.create_document('oranges and apples', self.user, pending=False, batch=batch_2)
        batch_3 = self.create_batch('Apples and coconuts', self.user)
        self.create_document('Apples and coconuts', self.user, pending=False, batch=batch_3)
        batch_4 = self.create_batch('coconuts and almonds', self.user)
        self.create_document('coconuts and almonds', self.user, pending=False, batch=batch_4)
        batch_5 = self.create_batch('butter and some milk', self.user)
        self.create_document('butter and some milk', self.user, pending=False, batch=batch_5)
        batch_6 = self.create_batch('Apple and butter', self.user)
        self.create_document('Apple and butter', self.user, pending=False, batch=batch_6)

        self.login()

        response = self.client.get(api_url + '?q=Apple')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 4)
        self.assertEqual(data['meta']['search']['query'], 'Apple')
        self.assertEqual(data['meta']['pagination']['object_count'], 4)

        titles = [d['batch_name'] for d in data['objects']]
        self.assertEqual(len(titles), 4)
        self.assertEqual(set(titles), set(['Apple and butter', 'Apples and coconuts', 'oranges and apples', 'apples']))

    def test_nothing_found(self):
        self.make_paid(self.user)
        api_url = reverse('document_list_view')

        self.create_document('apples', self.user, pending=False)
        self.create_document('oranges and apples', self.user, pending=False)
        self.create_document('Apples and coconuts', self.user, pending=False)
        self.create_document('coconuts and almonds', self.user, pending=False)
        self.create_document('butter and some milk', self.user, pending=False)
        self.create_document('Apple and butter', self.user, pending=False)

        self.login()

        response = self.client.get(api_url + '?q=banana')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 0)
        self.assertEqual(data['meta']['pagination']['object_count'], 0)


class DocumentDetailTest(BeagleWebTest):

    def setUp(self):
        super(DocumentDetailTest, self).setUp()

        self.instance = self.create_document('Some title', self.user, pending=False)

    def test_get_200(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('document_detail_view', kwargs={'uuid': self.instance.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_fields(self):
        self.make_paid(self.user)
        url = reverse('document_detail_view', kwargs={'uuid': self.instance.uuid})
        self.login()

        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertIn('analysis', data)
        self.assertIn('collaborators', data)
        self.assertIn('created', data)
        self.assertIn('original_name', data)
        self.assertIn('owner', data)
        self.assertIn('report_url', data)
        self.assertIn('url', data)
        self.assertIn('title', data)
        self.assertIn('status', data)
        self.assertIn('uuid', data)
        self.assertNotIn('trash', data)

        self.assertIn('parties', data['analysis'])
        self.assertIn('sentences', data['analysis'])
        self.assertIn('them', data['analysis']['parties'])
        self.assertIn('you', data['analysis']['parties'])

        self.assertEqual(data['collaborators'], [])
        self.assertEqual(data['original_name'], self.instance.original_name)
        self.assertEqual(data['title'], self.instance.title)
        self.assertEqual(data['uuid'], self.instance.uuid)
        self.assertEqual(data['status'], 1)

    def test_trash(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('document_detail_view', kwargs={'uuid': self.instance.uuid})

        self.instance.trash = True
        self.instance.save()

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        expected_data = {'message': 'Document matching query does not exist.',
                         'code': None,
                         'type': 'error',
                         'http_status': 404}
        data = json.loads(response.content)
        self.assertEqual(expected_data, data)

    def test_get_404(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('document_detail_view', kwargs={'uuid': self.instance.uuid + 'aaa'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_403(self):
        self.make_paid(self.user)
        url = reverse('document_detail_view', kwargs={'uuid': self.instance.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    @mock.patch('api_v1.document.endpoints.NotificationManager.create_document_message')
    def test_delete(self, mock_message):
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_detail_view', kwargs={'uuid': document.uuid})
        document = Document.objects.get(pk=document.pk)
        response = self.client.delete(api_url)
        self.assertEqual(response.status_code, 200)
        mock_message.assert_called_once_with(document, 'message', {
            'notif': NotificationManager.ServerNotifications.DOCUMENT_DELETED_NOTIFICATION,
            'document': document.to_dict(include_raw=False, include_analysis=False)
        })


class DocumentSortedListViewTest(BeagleWebTest):

    def setUp(self):
        super(DocumentSortedListViewTest, self).setUp()

        self.document1 = self.create_document(
            'Most recent document', self.user, pending=False
        )
        self.document2 = self.create_document(
            'Document viewed some time ago', self.user, pending=False
        )
        self.document3 = self.create_document(
            'Unviewed document', self.user, pending=False
        )

        self.make_paid(self.user)
        self.login()

        self.client.get(
            reverse('document_detail_view',
                    kwargs={'uuid': self.document2.uuid})
        )

        self.client.get(
            reverse('document_detail_view',
                    kwargs={'uuid': self.document1.uuid})
        )

    def test_get(self):
        url = reverse('document_sorted_list_view')

        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['meta']['pagination']['object_count'], 3)
        self.assertEqual(
            [obj['title'] for obj in data['objects']],
            ['Most recent document',
             'Document viewed some time ago',
             'Unviewed document']
        )

    def test_get_reversed(self):
        url = reverse('document_sorted_list_view') + '?order=dsc'

        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['meta']['pagination']['object_count'], 3)
        self.assertEqual(
            [obj['title'] for obj in data['objects']],
            ['Unviewed document',
             'Document viewed some time ago',
             'Most recent document']
        )


class DocumentViewedByTest(BeagleWebTest):

    def test_get(self):
        document = self.create_document('Some title', self.user, pending=False)

        self.make_paid(self.user)
        self.login()

        url = reverse('document_viewed_by_view',
                      kwargs={'uuid': document.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{}')

        doc_view = reverse('document_detail_view',
                           kwargs={'uuid': document.uuid})
        self.client.get(doc_view)
        viewdate = UserLastViewDate.objects.get(document=document,
                                                user=self.user)
        time = viewdate.date.astimezone(
            get_current_timezone()).strftime("%Y-%m-%d %H:%M")

        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {'dummy_user': time})


class AggregatedDocumentListTestCase(BeagleWebTest):
    def test_200(self):
        self.make_paid(self.user)
        api_url = reverse('document_aggregated_list_view')
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'objects': []})

    def test_document_owner(self):
        self.make_paid(self.user)
        api_url = reverse('document_aggregated_list_view')

        document = self.create_document('Title', self.user, pending=False)

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)

        data_document = data['objects'][0]
        self.assertEqual(data_document['status'], 1)
        self.assertEqual(data_document['uuid'], document.uuid)
        self.assertEqual(data_document['title'], 'Title')
        self.assertEqual(data_document['owner']['username'], self.DUMMY_USERNAME)
        self.assertEqual(data_document['owner']['email'], self.DUMMY_EMAIL)
        self.assertEqual(data_document['owner']['pending'], False)

    def test_more_invites_received(self):
        self.make_paid(self.user)
        api_url = reverse('document_aggregated_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', other_user, pending=False)
        CollaborationInvite(document=document, invitee=self.user, inviter=other_user).save()

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 1)

        data_document = data['objects'][0]
        self.assertEqual(data_document['status'], 1)
        self.assertEqual(data_document['uuid'], document.uuid)
        self.assertEqual(data_document['title'], 'Title')
        self.assertEqual(data_document['owner']['username'], 'someusername')
        self.assertEqual(data_document['owner']['email'], 'some@email.com')
        self.assertEqual(data_document['owner']['pending'], False)

    def test_owner_and_invited(self):
        self.make_paid(self.user)
        api_url = reverse('document_aggregated_list_view')

        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', other_user, pending=False)
        CollaborationInvite(document=document, invitee=self.user, inviter=other_user).save()

        self.create_document('Title', self.user, pending=False)

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(len(data['objects']), 2)

        emails = set([e['owner']['email'] for e in data['objects']])
        self.assertEqual(emails, set(['some@email.com', self.DUMMY_EMAIL]))

    def test_not_authenticated(self):
        self.make_paid(self.user)
        api_url = reverse('document_aggregated_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})


class FlagDocumentActionTestCase(BeagleWebTest):
    def test_get(self):
        self.make_paid(self.user)
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_flag_action_view', kwargs={'uuid': document.uuid})
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)
        flags = WrongAnalysisFlag.objects.all()
        self.assertEqual(len(flags), 0)

    def test_404(self):
        self.make_paid(self.user)
        self.login()
        api_url = reverse('document_flag_action_view', kwargs={'uuid': 'something'})
        data = json.dumps({'comments': 'U suck!'})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 404)
        flags = WrongAnalysisFlag.objects.all()
        self.assertEqual(len(flags), 0)

    def test_empty_comments(self):
        self.make_paid(self.user)
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_flag_action_view', kwargs={'uuid': document.uuid})
        data = json.dumps({})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'status': 0, 'message': 'Please provide a comment'})
        flags = WrongAnalysisFlag.objects.all()
        self.assertEqual(len(flags), 0)

    def test_successful(self):
        self.make_paid(self.user)
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_flag_action_view', kwargs={'uuid': document.uuid})
        data = json.dumps({'comments': "U don't suck!"})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'status': 1, 'message': 'OK'})
        flags = WrongAnalysisFlag.objects.all()
        self.assertEqual(len(flags), 1)
        flag = flags[0]
        self.assertEqual(flag.user, self.user)
        self.assertEqual(flag.doc, document)
        self.assertEqual(flag.comments, "U don't suck!")

    def test_403(self):
        self.make_paid(self.user)
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_flag_action_view', kwargs={'uuid': document.uuid})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

        data = json.loads(response.content)
        self.assertEqual(data, {'message': 'Please authenticate', 'code': None, 'type': 'error', 'http_status': 403})
        flags = WrongAnalysisFlag.objects.all()
        self.assertEqual(len(flags), 0)


class DocumentPrepareExportTestCase(BeagleWebTest):
    @mock.patch('core.tasks.prepare_docx_export.delay')
    def test_get(self, mocked_task):
        self.make_paid(self.user)
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_prepare_export_view', kwargs={'uuid': document.uuid})
        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 200)

        s3_path = settings.S3_EXPORT_PATH % document.uuid
        mocked_task.assert_called_once_with(
            document.pk,
            s3_path,
            included_annotations=None,
            include_track_changes=False,
            user_id=self.user.id,
            include_comments=False
        )

    def test_404(self):
        self.make_paid(self.user)
        self.login()
        api_url = reverse('document_prepare_export_view', kwargs={'uuid': 'something'})
        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 404)

    def test_403(self):
        self.make_paid(self.user)
        # Create another user
        other_user = self.create_user('other@email.com', 'other_username', 'P@$$')
        self.make_paid(other_user)

        document = self.create_document('Title', other_user, pending=False)
        api_url = reverse('document_prepare_export_view', kwargs={'uuid': document.uuid})

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 403)


class IssueSentenceInvitesActionViewTestCase(BeagleWebTest):
    @mock.patch('api_v1.document.endpoints.store_activity_notification.delay')
    def test_collaboration_invite(self, mocked_store_activity_notification):
        self.make_paid(self.user)
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        # Create another user
        other_user = self.create_user('other@email.com', 'other_username', 'P@$$')
        self.make_paid(other_user)

        # Create a collaboration invite
        CollaborationInvite(inviter=self.user, invitee=other_user, document=document).save()

        api_url = reverse('document_sentence_assign_action_view', kwargs={'uuid': document.uuid})
        data = {'email': 'other@email.com', 'sentences': [0, 3, 4]}

        response = self.client.post(api_url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        mocked_store_activity_notification.assert_has_calls([mock.call(target=other_user,
                                                                       transient=False,
                                                                       actor=self.user,
                                                                       verb='assigned',
                                                                       action_object=document.get_sentence_by_index(0),
                                                                       recipient=other_user,
                                                                       render_string='(actor) assigned (target) to a clause on (action_object)'),
                                                             mock.call(target=other_user,
                                                                       transient=False,
                                                                       actor=self.user,
                                                                       verb='assigned',
                                                                       action_object=document.get_sentence_by_index(3),
                                                                       recipient=other_user,
                                                                       render_string='(actor) assigned (target) to a clause on (action_object)'),
                                                             mock.call(target=other_user,
                                                                       transient=False,
                                                                       actor=self.user,
                                                                       verb='assigned',
                                                                       action_object=document.get_sentence_by_index(4),
                                                                       recipient=other_user,
                                                                       render_string='(actor) assigned (target) to a clause on (action_object)')
                                                             ])

    def test_no_collaboration_invite(self):
        self.make_paid(self.user)
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        # Create another user
        other_user = self.create_user('other@email.com', 'other_username', 'P@$$')
        self.make_paid(other_user)

        api_url = reverse('document_sentence_assign_action_view', kwargs={'uuid': document.uuid})
        data = {'email': 'other@email.com', 'sentences': [0, 3, 4]}

        response = self.client.post(api_url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_external_invite(self):
        self.make_paid(self.user)
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        # Create a collaboration invite
        ExternalInvite(inviter=self.user, email='other@email.com', document=document).save()

        api_url = reverse('document_sentence_assign_action_view', kwargs={'uuid': document.uuid})
        data = {'email': 'other@email.com', 'sentences': [0, 3, 4]}

        response = self.client.post(api_url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        from core.models import DelayedNotification
        delayed_notifications = DelayedNotification.objects.all().order_by('created')
        for sidx, dnotif in zip([0, 3, 4], delayed_notifications):
            self.assertEqual(document.get_sentence_by_index(sidx), dnotif.notification.action_object)
            self.assertEqual(self.user, dnotif.notification.actor)
            self.assertEqual('assigned', dnotif.notification.verb)
            self.assertEqual("(actor) assigned (target) to a clause on (action_object)",
                             dnotif.notification.data['render_string'])
            self.assertEqual('other@email.com', dnotif.email)
            self.assertEqual(False, dnotif.transient)
            self.assertEqual(dnotif.delayed_fields, ['recipient', 'target'])

    def test_no_external_invite(self):
        self.make_paid(self.user)
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        api_url = reverse('document_sentence_assign_action_view', kwargs={'uuid': document.uuid})
        data = {'email': 'other@email.com', 'sentences': [0, 3, 4]}

        response = self.client.post(api_url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

        from core.models import DelayedNotification
        delayed_notifications = DelayedNotification.objects.all().order_by('created')

        self.assertEqual(len(delayed_notifications), 0)


class ChangeOwnerActionViewTestCase(BeagleWebTest):
    ENDPOINT_NAME = 'document_change_owner_action_view'

    def test_document_not_found(self):
        """
        Try to change the owner of a non-existing document
        """
        self.login()
        other_user = self.create_user('other@email.com', 'other_username', 'P@$$')

        api_url = reverse(self.ENDPOINT_NAME, kwargs={'uuid': 'does-not-exist'})
        data = json.dumps({'owner': other_user.pk})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_key_not_found(self):
        """
        Post a non compliant json to the endpoint
        """
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse(self.ENDPOINT_NAME, kwargs={'uuid': document.uuid})
        data = json.dumps({'smth': 'dne@dne.com'})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {
            'code': None,
            'http_status': 400,
            'message': "Please provide the new 'owner'",
            'type': 'error'})

        # Check the owner didn't change
        document = Document.objects.get(pk=document.pk)
        self.assertEqual(document.owner, self.user)

    def test_new_owner_to_found(self):
        """
        Try to change the owner to a non-existing user
        """
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse(self.ENDPOINT_NAME, kwargs={'uuid': document.uuid})
        data = json.dumps({'owner': 'dne@dne.com'})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {
            'code': None,
            'http_status': 400,
            'message': "The new owner can't be found",
            'type': 'error'})

        # Check the owner didn't change
        document = Document.objects.get(pk=document.pk)
        self.assertEqual(document.owner, self.user)

    def test_new_user_no_access(self):
        """
        Try to change the owner to a non-participating user
        """
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse(self.ENDPOINT_NAME, kwargs={'uuid': document.uuid})
        other_user = self.create_user('other@email.com', 'other_username', 'P@$$')
        data = json.dumps({'owner': other_user.pk})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {
            'code': None,
            'http_status': 400,
            'message': "The new owner doesn't have access to the document",
            'type': 'error'})

        # Check the owner didn't change
        document = Document.objects.get(pk=document.pk)
        self.assertEqual(document.owner, self.user)

    def test_change_to_old_owner(self):
        """
        Try to change the owner to a non-participating user
        """
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse(self.ENDPOINT_NAME, kwargs={'uuid': document.uuid})
        data = json.dumps({'owner': self.user.pk})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {
            'code': None,
            'http_status': 400,
            'message': "The new owner is the same as the old one",
            'type': 'error'})

        # Check the owner didn't change
        document = Document.objects.get(pk=document.pk)
        self.assertEqual(document.owner, self.user)

    def test_changer_no_access(self):
        """
        A user tries to change the owner of a document he doesn't have access to
        """
        self.login()

        other_user = self.create_user('other@email.com', 'other_username', 'P@$$')
        another_user = self.create_user('another@email.com', 'another_username', 'P@$$')
        document = self.create_document('Title', other_user, pending=False)
        api_url = reverse(self.ENDPOINT_NAME, kwargs={'uuid': document.uuid})
        CollaborationInvite.objects.create(inviter=self.user, invitee=other_user, document=document)
        data = json.dumps({'owner': another_user.pk})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content), {
            'code': None,
            'http_status': 403,
            'message': "You don't have access to this resource",
            'type': 'error'})

        # Check the owner didn't change
        document = Document.objects.get(pk=document.pk)
        self.assertEqual(document.owner, other_user)

    @mock.patch('api_v1.document.endpoints.NotificationManager.create_document_message')
    def test_success(self, mock_message):
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse(self.ENDPOINT_NAME, kwargs={'uuid': document.uuid})
        other_user = self.create_user('other@email.com', 'other_username', 'P@$$')
        CollaborationInvite.objects.create(inviter=self.user, invitee=other_user, document=document)
        data = json.dumps({'owner': other_user.pk})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'message': "OK",
            'status': 1})

        # Check the owner DID change
        document = Document.objects.get(pk=document.pk)
        self.assertEqual(document.owner, other_user)

        # Check that the old user has been automatically invited to the document
        self.assertEqual(len(CollaborationInvite.objects.filter(
            inviter=other_user, invitee=self.user, document=document)), 1)

        # Check that there isn't any invitation for the new owner
        self.assertEqual(len(CollaborationInvite.objects.filter(
            inviter=self.user, invitee=other_user, document=document)), 0)

        # Send the notification to refresh the document
        mock_message.assert_called_once_with(document, 'message', {
            'notif': NotificationManager.ServerNotifications.DOCUMENT_OWNER_CHANGED_NOTIFICATION,
            'document': document.to_dict(include_raw=False, include_analysis=False)
        })

    @mock.patch('api_v1.document.endpoints.NotificationManager.create_document_message')
    def test_success_complex(self, mock_message):
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse(self.ENDPOINT_NAME, kwargs={'uuid': document.uuid})

        other_user = self.create_user('other@email.com', 'other_username', 'P@$$')
        another_user = self.create_user('another@email.com', 'another_username', 'P@$$')

        CollaborationInvite.objects.create(inviter=self.user, invitee=other_user, document=document)
        CollaborationInvite.objects.create(inviter=self.user, invitee=another_user, document=document)

        self.login()  # Log in as the first user `self.user`
        data = json.dumps({'owner': other_user.pk})  # make `other_user` the owner
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'message': "OK",
            'status': 1})
        self.logout()

        self.client.login(username='other_username', password='P@$$')  # Log in as `other_user`
        data = json.dumps({'owner': another_user.pk})  # make `another_user` the owner
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'message': "OK",
            'status': 1})
        self.client.logout()

        # Check the owner DID change
        document = Document.objects.get(pk=document.pk)
        self.assertEqual(document.owner, another_user)

        # Check that the old user has been automatically invited to the document
        self.assertEqual(len(CollaborationInvite.objects.filter(
            inviter=another_user, invitee=other_user, document=document)), 1)

        # Check that there isn't any invitation for the new owner
        self.assertEqual(len(CollaborationInvite.objects.filter(
            invitee=another_user, document=document)), 0)

        self.assertEqual(mock_message.call_count, 2)

        # Send the notification to refresh the document
        mock_message.assert_has_calls([
            mock.call(document, 'message', {
                'notif': NotificationManager.ServerNotifications.DOCUMENT_OWNER_CHANGED_NOTIFICATION,
                'document': mock.ANY
            }),

            mock.call().send(),

            mock.call(document, 'message', {
                'notif': NotificationManager.ServerNotifications.DOCUMENT_OWNER_CHANGED_NOTIFICATION,
                'document': mock.ANY
            }),

            mock.call().send()
        ])


class ChangePartiesActionViewTestCase(BeagleWebTest):
    def test_404(self):
        self.make_paid(self.user)
        self.login()
        api_url = reverse('document_change_parties_action_view', kwargs={'uuid': 'something'})
        data = json.dumps({'parties': ['P1', 'P2']})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_no_parties(self):
        self.make_paid(self.user)
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_change_parties_action_view', kwargs={'uuid': document.uuid})
        data = json.dumps({})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'status': 0, 'message': 'Please provide parties'})

    def test_empty_parties(self):
        self.make_paid(self.user)
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_change_parties_action_view', kwargs={'uuid': document.uuid})
        data = json.dumps({'parties': []})
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'status': 0, 'message': '2 parties should be provided'})

    @override_settings(DEBUG=False)
    def test_successful_prod(self):
        self.make_paid(self.user)
        with mock.patch('api_v1.document.endpoints.send_slack_message') as mock_send_slackbot_message:
            self.login()
            document = self.create_document('Title', self.user, pending=False)
            api_url = reverse('document_change_parties_action_view', kwargs={'uuid': document.uuid})
            data = json.dumps({'parties': ['P1', 'P2']})
            response = self.client.post(api_url, data=data, content_type='application/json')

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            # Test the Beagle Slackbot message is sent to us
            mock_send_slackbot_message.assert_called_once_with(
                '* * ({0}) updated parties:\n*Original Parties*\nParty A: ** _confidence: 0%_\nParty B: ** _confidence: 0%_\n*New Parties*\nParty A: *P2*\nParty B: *P1*\nOn report _Title_'.format(
                    self.user.email), '#intercom')

            self.assertEqual(data, {'status': 1, 'message': 'OK'})

    @override_settings(DEBUG=True)
    def test_successful_dev(self):
        self.make_paid(self.user)
        with mock.patch('core.tasks.send_slack_message') as mock_send_slackbot_message:
            self.login()
            document = self.create_document('Title', self.user, pending=False)
            api_url = reverse('document_change_parties_action_view', kwargs={'uuid': document.uuid})
            data = json.dumps({'parties': ['P1', 'P2']})
            response = self.client.post(api_url, data=data, content_type='application/json')

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            # Test the Beagle slackbot message is NOT sent to us (because we're on a dev environment)
            self.assertFalse(mock_send_slackbot_message.called)
            self.assertEqual(data, {'status': 1, 'message': 'OK'})


class ReanalysisActionViewTestCase(BeagleWebTest):
    def test_404(self):
        self.make_paid(self.user)
        self.login()
        api_url = reverse('document_reanalysis_action_view', kwargs={'uuid': 'something'})
        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated(self):
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_reanalysis_action_view', kwargs={'uuid': document.uuid})
        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 403)

    def test_not_owner(self):
        self.login()
        other_user = self.create_user('other@email.com', 'other_username', 'P@$$')

        # -- When user is invited to the document --
        document1 = self.create_document('Title', other_user, pending=False)
        CollaborationInvite.objects.create(inviter=other_user, invitee=self.user, document=document1)
        api_url = reverse('document_reanalysis_action_view', kwargs={'uuid': document1.uuid})

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 200)

        # -- When user is NOT invited to the document --
        document2 = self.create_document('Title 2', other_user, pending=False)
        api_url = reverse('document_reanalysis_action_view', kwargs={'uuid': document2.uuid})

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=True)
    def test_successful(self):
        self.make_paid(self.user)
        with mock.patch('core.tasks.process_document_task') as mock_process_document_task:
            self.login()
            document = self.create_document('Title', self.user, pending=False)
            api_url = reverse('document_reanalysis_action_view', kwargs={'uuid': document.uuid})
            response = self.client.post(api_url)

            mock_process_document_task.assert_called_once()
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {'status': 1, 'message': 'OK'})


class UploadRawTextComputeView(BeagleWebTest):
    def test_missing_text(self):
        self.make_paid(self.user)
        self.login()
        api_url = reverse('document_upload_text_compute_view')
        data = json.dumps({
            'username': self.DUMMY_USERNAME,
            'url': 'http://some-url.com',
        })
        response = self.client.post(api_url, data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['message'], "'text' not present")

    def test_missing_url(self):
        self.make_paid(self.user)
        self.login()
        api_url = reverse('document_upload_text_compute_view')
        data = json.dumps({
            'username': self.DUMMY_USERNAME,
            'text': 'This is a veeeeeeeery long text.',
        })
        response = self.client.post(api_url, data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['message'], "'url' not present")

    def test_missing_username(self):
        self.make_paid(self.user)
        self.login()
        api_url = reverse('document_upload_text_compute_view')
        data = json.dumps({
            'text': 'This is a veeeeeeeery long text.',
            'url': 'http://some-url.com',
        })
        response = self.client.post(api_url, data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['message'], "'username' not present")

    def test_unauthenticated(self):
        api_url = reverse('document_upload_text_compute_view')
        data = json.dumps({
            'username': self.DUMMY_USERNAME,
            'text': 'This is a veeeeeeeery long text.',
            'url': 'http://some-url.com',
        })
        response = self.client.post(api_url, data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_successful(self):
        self.make_paid(self.user)
        self.login()
        api_url = reverse('document_upload_text_compute_view')
        data = json.dumps({
            'username': self.DUMMY_USERNAME,
            'text': 'This is a veeeeeeeery long text.',
            'url': 'http://some-url.com',
        })
        response = self.client.post(api_url, data=data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)

        documents = Document.objects.all()
        self.assertEqual(len(documents), 1)

        document = documents[0]
        self.assertEqual(document.title, 'http://some-url.com')
        self.assertEqual(document.owner, self.user)


class DocumentUploadComputeViewTestCase(BeagleWebTest):
    API_URL = reverse('document_upload_compute_view')

    def test_get(self):
        self.make_paid(self.user)
        self.login()
        self.assertEqual(self.client.get(self.API_URL).status_code, 403)

    def test_post_url(self):
        self.make_paid(self.user)
        self.login()
        data = {'url': 'http://example.com'}

        ARTICLE_TEXT = "This is a huge responsibility. Treat it as such!"
        ARTICLE_TITLE = "This is the title"
        FILE_NAME = "This+is+the+title.txt"

        self.assertEqual(len(Document.objects.all()), 0)

        with mock.patch('api_v1.document.endpoints.DocumentUploadComputeView.handle_url') as mock_handle_url:
          with mock.patch('api_v1.document.endpoints.Article') as MockArticle:
              with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                  mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                  type(MockArticle.return_value).text = mock.PropertyMock(return_value=ARTICLE_TEXT)
                  type(MockArticle.return_value).title = mock.PropertyMock(return_value=ARTICLE_TITLE)
                  mock_handle_url.return_value = (ARTICLE_TITLE, FILE_NAME, ARTICLE_TEXT)

                  response = self.client.post(self.API_URL, data=json.dumps(data), content_type='application/json')

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
                          "is_paid": True,
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

    def test_post_url_upload_via_email(self):
        self.make_paid(self.user)
        self.login()
        data = {'url': 'http://example.com'}

        ARTICLE_TEXT = "This is a huge responsibility. Treat it as such!"
        ARTICLE_TITLE = "This is the title"
        FILE_NAME = "This+is+the+title.txt"

        self.assertEqual(len(Document.objects.all()), 0)
        with mock.patch('api_v1.document.endpoints.DocumentUploadComputeView.handle_url') as mock_handle_url:
          with mock.patch('api_v1.document.endpoints.Article') as MockArticle:
              with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                  mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                  mock_handle_url.return_value = (ARTICLE_TITLE, FILE_NAME, ARTICLE_TEXT)

                  type(MockArticle.return_value).text = mock.PropertyMock(return_value=ARTICLE_TEXT)
                  type(MockArticle.return_value).title = mock.PropertyMock(return_value=ARTICLE_TITLE)
                  self.client.post(self.API_URL + '?send_upload_via_email=true', data=json.dumps(data),
                                       content_type='application/json')

                  self.assertEqual(len(Document.objects.all()), 1)
                  document = Document.objects.all()[0]
                  self.assertEqual(document.upload_source, 'email')

    def test_post_url_and_title(self):
        self.make_paid(self.user)
        self.login()
        data = {'url': 'http://example.com', 'title': 'Super title'}

        ARTICLE_TITLE = "This is the title"
        FILE_NAME = "Super+title.txt"
        ARTICLE_TEXT = "This is a huge responsibility. Treat it as such!"

        self.assertEqual(len(Document.objects.all()), 0)

        with mock.patch('api_v1.document.endpoints.DocumentUploadComputeView.handle_url') as mock_handle_url:
          with mock.patch('api_v1.document.endpoints.Article') as MockArticle:
              with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                  mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                  type(MockArticle.return_value).text = mock.PropertyMock(return_value=ARTICLE_TEXT)
                  mock_handle_url.return_value = (ARTICLE_TITLE, FILE_NAME, ARTICLE_TEXT)

                  response = self.client.post(self.API_URL, data=json.dumps(data), content_type='application/json')

                  self.assertEqual(len(Document.objects.all()), 1)
                  document = Document.objects.all()[0]
                  data = json.loads(response.content)

                  self.assertEqual(data, {
                      "collaborators": [],
                      "created": mock.ANY,
                      "original_name": FILE_NAME,
                      "owner": {
                          "avatar": "/static/img/mug.png",
                          "company": None,
                          "date_joined": mock.ANY,
                          "document_upload_count": 1,
                          "email": self.DUMMY_EMAIL,
                          "first_name": None,
                          "had_trial": False,
                          "id": mock.ANY,
                          "is_paid": True,
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
                      "document_id": document.id,
                      "status": 0,
                      "failed": False,
                      "processing_begin_timestamp": mock.ANY,
                      "processing_end_timestamp": mock.ANY,
                  })

    def test_post_text(self):
        self.make_paid(self.user)
        self.login()
        data = {'text': 'This is an awesome text. It is pretty much about anything. Running out of inspiration here.'
                        'What more is it to say? How can I lengthen this even more? Good question! Marvelous question.'
                        'In fact, I need this to be just over 100 chars. Can we make this happen people?'}

        self.assertEqual(len(Document.objects.all()), 0)

        with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
            mock_save.return_value = 'RETURN_VALUE_FILE_PATH'

            response = self.client.post(self.API_URL, data=json.dumps(data), content_type='application/json')

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
                    "is_paid": True,
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
        self.make_paid(self.user)
        self.login()
        data = {'text': 'This is an awesome text. It is pretty much about anything. Running out of inspiration here.'
                        'What more is it to say? How can I lengthen this even more? Good question! Marvelous question.'
                        'In fact, I need this to be just over 100 chars. Can we make this happen people?',
                'title': 'The Stuff'}

        self.assertEqual(len(Document.objects.all()), 0)

        with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
            mock_save.return_value = 'RETURN_VALUE_FILE_PATH'

            response = self.client.post(self.API_URL, data=json.dumps(data), content_type='application/json')

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
                    "is_paid": True,
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
        # Test out of date
        pass

    # TODO Rewrite test using new functionality
    def test_workflow_params_for_text(self):
        # Test out of date
        pass

    def test_process_document_conversion_params_for_url(self):
        self.make_paid(self.user)
        self.login()
        data = {'url': 'http://example.com'}

        ARTICLE_TEXT = "This is a huge responsibility. Treat it as such!"
        ARTICLE_TITLE = "This is the title"

        with mock.patch('api_v1.document.endpoints.Article') as MockArticle:
            with mock.patch('core.tasks.process_document_conversion.delay') as mock_conversion:
                with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                    mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                    type(MockArticle.return_value).text = mock.PropertyMock(return_value=ARTICLE_TEXT)
                    type(MockArticle.return_value).title = mock.PropertyMock(return_value=ARTICLE_TITLE)
                    self.client.post(self.API_URL, data=json.dumps(data), content_type='application/json')

                    mock_conversion.assert_called_once_with(mock.ANY, 'media/RETURN_VALUE_FILE_PATH', True)

    def test_process_document_conversion_params_for_text(self):
        self.make_paid(self.user)
        self.login()
        data = {'text': 'This is an awesome text. It is pretty much about anything. Running out of inspiration here.'
                        'What more is it to say? How can I lengthen this even more? Good question! Marvelous question.'
                        'In fact, I need this to be just over 100 chars. Can we make this happen people?'}

        with mock.patch('core.tasks.process_document_conversion.delay') as mock_conversion:
            with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
                mock_save.return_value = 'RETURN_VALUE_FILE_PATH'
                self.client.post(self.API_URL, data=json.dumps(data), content_type='application/json')

                mock_conversion.assert_called_once_with(mock.ANY, 'media/RETURN_VALUE_FILE_PATH', True)

    def test_url_containing_unicode(self):
        self.make_paid(self.user)
        self.login()
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
                response = self.client.post(self.API_URL, data=json.dumps(data), content_type='application/json')

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
                        "is_paid": True,
                        "is_super": False,
                        "job_title": None,
                        "last_login": mock.ANY,
                        "last_name": None,
                        "pending": False,
                        "phone": None,
                        "tags": [],
                        "keywords": mock.ANY,
                        "settings": mock.ANY,
                        "username": self.DUMMY_USERNAME
                    },
                    "report_url": "/report/%s" % document.uuid,
                    "title": u'Contact GitHub * GitHub',
                    "url": "/api/v1/document/%s" % document.uuid,
                    "is_initsample": False,
                    "uuid": document.uuid,
                    "document_id": document.id,
                    "status": 0,
                    "failed": False,
                    "processing_begin_timestamp": mock.ANY,
                    "processing_end_timestamp": mock.ANY,
                })

    def test_upload_file_via_email(self):
        self.make_paid(self.user)
        self.login()

        file_handler = tempfile.TemporaryFile()
        file_handler.write("Hello World!")
        file_handler.seek(0)

        with mock.patch('api_v1.document.endpoints.default_storage.save') as mock_save:
            mock_save.return_value = 'RETURN_VALUE_FILE_PATH'

            response = self.client.post(self.API_URL + '?send_upload_via_email=true',
                                        {'afile.txt': self.get_temporary_text_file('doesntmatter.txt',
                                                                                   'Some awesome stuff')},
                                        format='multipart')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(Document.objects.all()), 1)

            document = Document.objects.all()[0]

            self.assertEqual(document.upload_source, 'email')

            # TODO Rewrite test using new functionality
            def test_download_docx(self):
                # Test out of date
                pass

            # TODO Rewrite test using new functionality
            def test_download_pdf(self):
                # Test out of date
                pass
