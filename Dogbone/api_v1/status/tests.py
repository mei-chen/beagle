import json
from django.urls import reverse
from dogbone.testing.base import BeagleWebTest
from constance.test import override_config


class ApplicationStatusTestCase(BeagleWebTest):

    def test_200(self):
        api_url = reverse('app_status_view')
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

    @override_config(BROWSER_EXTENSION_ENABLED=True)
    def test_enabled(self):
        api_url = reverse('app_status_view')
        response = self.client.get(api_url)
        data = json.loads(response.content)
        self.assertEqual(data, {'extension': {'enabled': True}})

    @override_config(BROWSER_EXTENSION_ENABLED=False)
    @override_config(BROWSER_EXTENSION_DISABLED_MESSAGE='The Service is under development. Please try again later.')
    def test_disabled(self):
        api_url = reverse('app_status_view')
        response = self.client.get(api_url)
        data = json.loads(response.content)
        self.assertEqual(data, {'extension': {
            'enabled': False,
            'message': 'The Service is under development. Please try again later.'}})

    @override_config(BROWSER_EXTENSION_ENABLED=False)
    @override_config(BROWSER_EXTENSION_DISABLED_MESSAGE='Wut?!')
    def test_disabled(self):
        api_url = reverse('app_status_view')
        response = self.client.get(api_url)
        data = json.loads(response.content)
        self.assertEqual(data, {'extension': {
            'enabled': False,
            'message': 'Wut?!'}})
