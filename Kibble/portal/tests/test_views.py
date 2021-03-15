from django.urls import reverse

from django.test import TestCase


class LoginViewTest(TestCase):
    def setUp(self):
        self.url = reverse('account_login')

    def test_login_empty_fields(self):
        """
        Field errors are displayed on login page
        """
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        errors = response.context['form'].errors
        self.assertIn('login', errors.keys())
        self.assertIn('password', errors.keys())
        self.assertNotIn('__all__', errors.keys())
        for k, v in errors.items():
            self.assertIn(v[0], response.content)

    def test_login_wrong_password(self):
        """
        Non-field errors are displayed on login page
        """
        response = self.client.post(
            self.url, {'login': 'foo', 'password': 'bar'})
        self.assertEqual(response.status_code, 200)
        errors = response.context['form'].errors
        self.assertNotIn('login', errors.keys())
        self.assertNotIn('password', errors.keys())
        self.assertIn('__all__', errors.keys())
        for k, v in errors.items():
            self.assertIn(v[0], response.content)
