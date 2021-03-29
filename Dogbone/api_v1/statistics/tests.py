import json

from django.urls import reverse
import mock

from dogbone.testing.base import BeagleWebTest


class StatisticsComputeViewTestCase(BeagleWebTest):

    def setUp(self):
        super(StatisticsComputeViewTestCase, self).setUp()
        self.api_url = reverse('statistics_compute_view')

    @mock.patch('api_v1.statistics.endpoints.log_statistic_event.delay')
    def test_ok(self, log_statistic_event_mock):
        self.login()

        payload = {'event': 'Test API',
                   'attributes': {'x': 1, 'y': 2, 'z': 3},
                   'key': 'value'}
        response = self.client.post(self.api_url, data=json.dumps(payload),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        log_statistic_event_mock.assert_called_once_with(
            event_name=payload['event'],
            event_user=mock.ANY,
            event_data=payload['attributes']
        )

    def test_not_authenticated_failure(self):
        payload = {'event': 'Test API',
                   'attributes': {'x': 1, 'y': 2, 'z': 3},
                   'key': 'value'}
        response = self.client.post(self.api_url, data=json.dumps(payload),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 403)

    def test_no_event_failure(self):
        self.login()

        payload = {'attributes': {'x': 1, 'y': 2, 'z': 3},
                   'key': 'value'}
        response = self.client.post(self.api_url, data=json.dumps(payload),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)

    @mock.patch('api_v1.statistics.endpoints.log_statistic_event.delay')
    def test_no_attributes_ok(self, log_statistic_event_mock):
        self.login()

        payload = {'event': 'Test API',
                   'key': 'value'}
        response = self.client.post(self.api_url, data=json.dumps(payload),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        log_statistic_event_mock.assert_called_once_with(
            event_name=payload['event'],
            event_user=mock.ANY,
            event_data=None
        )
