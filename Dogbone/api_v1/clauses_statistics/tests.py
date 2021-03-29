import json

from django.urls import reverse

from clauses_statistics.models import ClausesStatistic
from dogbone.testing.base import BeagleWebTest


class ClausesStatisticDetailViewTestCase(BeagleWebTest):

    def setUp(self):
        super(ClausesStatisticDetailViewTestCase, self).setUp()
        ClausesStatistic.objects.create(tag='taggy', avg_word_count=99)

    def test_200(self):
        api_url = reverse('clauses_statistic_detail_view', kwargs={'tag': 'taggy'})

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data,
                         {u'tag': u'taggy',
                          u'avg_word_count': 99})

    def test_not_authenticated(self):
        api_url = reverse('clauses_statistic_detail_view', kwargs={'tag': 'taggy'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

    def test404(self):
        api_url = reverse('clauses_statistic_detail_view', kwargs={'tag': 'taggy_nonexistent'})

        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)
