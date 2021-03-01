import json
import mock

from django.core.urlresolvers import reverse
from django.db import transaction

from dogbone.testing.base import BeagleWebTest
from keywords.models import SearchKeyword


class SearchKeywordListViewTestCase(BeagleWebTest):
    def test_200(self):
        kw1 = SearchKeyword.add(self.user, 'slim')
        kw2 = SearchKeyword.add(self.user, 'shady')
        kw3 = SearchKeyword.add(self.user, 'snoopy')

        kw2.deactivate()
        api_url = reverse('keyword_list_view')

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            "objects": [
                {
                    "active": True,
                    "created": mock.ANY,
                    "keyword": "snoopy",
                    "exact_match": False
                },
                {
                    "active": False,
                    "created": mock.ANY,
                    "keyword": "shady",
                    "exact_match": False
                },
                {
                    "active": True,
                    "created": mock.ANY,
                    "keyword": "slim",
                    "exact_match": False
                },
            ]
        })

    def test_200_other_peoples_keywords(self):
        another_user = self.create_user('some@user.com', 'someusername', '1234')
        kw1 = SearchKeyword.add(self.user, 'slim')
        kw2 = SearchKeyword.add(self.user, 'shady')
        okw1 = SearchKeyword.add(another_user, 'one')
        kw3 = SearchKeyword.add(self.user, 'snoopy')
        okw2 = SearchKeyword.add(another_user, 'two')

        kw2.deactivate()
        api_url = reverse('keyword_list_view')

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            "objects": [
                {
                    "active": True,
                    "created": mock.ANY,
                    "keyword": "snoopy",
                    "exact_match": False
                },
                {
                    "active": False,
                    "created": mock.ANY,
                    "keyword": "shady",
                    "exact_match": False
                },
                {
                    "active": True,
                    "created": mock.ANY,
                    "keyword": "slim",
                    "exact_match": False
                },
            ]
        })

    def test_200_lots_of_keywords(self):
        for idx in range(22):
            SearchKeyword.add(self.user, 'a'* idx)

        api_url = reverse('keyword_list_view')

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['objects']), 22)

    def test_post(self):
        api_url = reverse('keyword_list_view')
        self.login()

        data = {'keyword': 'Shady'}

        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {
            'objects': [
                {
                    'active': True,
                    'created': mock.ANY,
                    'keyword': 'shady',
                    'exact_match': False
                }
            ]
        })

        self.assertEqual(len(SearchKeyword.objects.filter(keyword='shady', owner=self.user)), 1)

    def test_post_multiple(self):
        api_url = reverse('keyword_list_view')
        self.login()

        data = [
            {
                'keyword': 'Slim',
                'active': False,
            },
            {
                'keyword': 'Shady'
            },
            {
                'keyword': 'eminem',
                'exact_match': True,
            }
        ]

        response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertEqual(data, {
            'objects': [
                {
                    'active': False,
                    'created': mock.ANY,
                    'keyword': 'slim',
                    'exact_match': False
                },
                {
                    'active': True,
                    'created': mock.ANY,
                    'keyword': 'shady',
                    'exact_match': False
                },
                {
                    'active': True,
                    'created': mock.ANY,
                    'keyword': 'eminem',
                    'exact_match': True
                }
            ]
        })

        self.assertEqual(len(SearchKeyword.objects.filter(keyword='shady', owner=self.user)), 1)

    def test_post_duplicate(self):
        api_url = reverse('keyword_list_view')
        self.login()

        data = {'keyword': 'Shady'}

        self.client.post(api_url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(len(SearchKeyword.objects.filter(keyword='shady', owner=self.user)), 1)

        with transaction.atomic():
            response = self.client.post(api_url, data=json.dumps(data), content_type='application/json')
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.content)
            self.assertEqual(data, {
                'code': None,
                'http_status': 400,
                'message': 'The keyword is already associated with the user',
                'type': 'error'
            })

        self.assertEqual(len(SearchKeyword.objects.filter(keyword='shady', owner=self.user)), 1)


class SearchKeywordDetailViewTestCase(BeagleWebTest):

    def test_200(self):
        SearchKeyword.add(self.user, 'shady')
        api_url = reverse('keyword_detail_view', kwargs={'keyword': 'shady'})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            'active': True,
            'keyword': 'shady',
            'created': mock.ANY,
            'exact_match': False
        })

    def test_404(self):
        api_url = reverse('keyword_detail_view', kwargs={'keyword': 'non-existent'})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.content)
        self.assertEqual(data, {
            'code': None,
            'http_status': 404,
            'message': 'SearchKeyword matching query does not exist.',
            'type': 'error'})

    def test_delete(self):
        SearchKeyword.add(self.user, 'awesome')
        api_url = reverse('keyword_detail_view', kwargs={'keyword': 'awesome'})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.delete(api_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)

        self.assertRaises(SearchKeyword.DoesNotExist, SearchKeyword.objects.get, owner=self.user, keyword='awesome')

    def test_put_change_match(self):
        SearchKeyword.add(self.user, 'awesome')
        api_url = reverse('keyword_detail_view', kwargs={'keyword': 'awesome'})
        self.login()

        data = {'exact_match': True}
        response = self.client.put(api_url, data=json.dumps(data), content_type='application/json')

        data = json.loads(response.content)
        self.assertEqual(data, {
            'active': True,
            'keyword': 'awesome',
            'created': mock.ANY,
            'exact_match': True
        })

    def test_put_change_keyword(self):
        SearchKeyword.add(self.user, 'awesome')
        api_url = reverse('keyword_detail_view', kwargs={'keyword': 'awesome'})
        self.login()

        data = {'keyword': 'different'}
        response = self.client.put(api_url, data=json.dumps(data), content_type='application/json')

        data = json.loads(response.content)
        self.assertEqual(data, {
            'active': True,
            'keyword': 'different',
            'created': mock.ANY,
            'exact_match': False
        })

    def test_not_authenticated(self):
        SearchKeyword.add(self.user, 'awesome')
        api_url = reverse('keyword_detail_view', kwargs={'keyword': 'awesome'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)


class SearchKeywordActivateActionViewTestCase(BeagleWebTest):

    def test_200(self):
        kw = SearchKeyword.add(self.user, 'shady')
        kw.deactivate()
        api_url = reverse('keyword_activate_action_view', kwargs={'keyword': 'shady'})
        self.login()

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            'active': True,
            'keyword': 'shady',
            'created': mock.ANY,
            'exact_match': False
        })

    def test_200_already_active(self):
        SearchKeyword.add(self.user, 'shady')
        api_url = reverse('keyword_activate_action_view', kwargs={'keyword': 'shady'})
        self.login()

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            'active': True,
            'keyword': 'shady',
            'created': mock.ANY,
            'exact_match': False
        })

    def test_404(self):
        api_url = reverse('keyword_activate_action_view', kwargs={'keyword': 'non-existent'})
        self.login()

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.content)
        self.assertEqual(data, {
            'code': None,
            'http_status': 404,
            'message': 'SearchKeyword matching query does not exist.',
            'type': 'error'})


class SearchKeywordDeactivateActionViewTestCase(BeagleWebTest):

    def test_200(self):
        SearchKeyword.add(self.user, 'shady')
        api_url = reverse('keyword_deactivate_action_view', kwargs={'keyword': 'shady'})
        self.login()

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            'active': False,
            'keyword': 'shady',
            'created': mock.ANY,
            'exact_match': False
        })

    def test_200_already_inactive(self):
        kw = SearchKeyword.add(self.user, 'shady')
        kw.deactivate()
        api_url = reverse('keyword_deactivate_action_view', kwargs={'keyword': 'shady'})
        self.login()

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {
            'active': False,
            'keyword': 'shady',
            'created': mock.ANY,
            'exact_match': False,
        })

    def test_404(self):
        api_url = reverse('keyword_deactivate_action_view', kwargs={'keyword': 'non-existent'})
        self.login()

        response = self.client.post(api_url)
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.content)

        self.assertEqual(data, {
            'code': None,
            'http_status': 404,
            'message': 'SearchKeyword matching query does not exist.',
            'type': 'error'
        })



