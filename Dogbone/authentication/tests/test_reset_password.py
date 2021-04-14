import mock
from django.urls import reverse
from dogbone.testing.base import BeagleWebTest
from authentication.models import PasswordResetRequest


class ResetPasswordTest(BeagleWebTest):

    def test_url(self):
        """ Check that the url actually exists """

        response = self.client.get(reverse('reset_password'))
        self.assertEqual(response.status_code, 200)

    def test_302(self):
        """ Check if we get redirected when we're logged in """
        self.make_paid(self.user)
        self.login()
        response = self.client.get(reverse('reset_password'))
        self.assertRedirects(response, reverse('account'), status_code=302)

    def test_302_next(self):
        """ Check if we get properly redirected when we have a next param """
        self.make_paid(self.user)
        self.login()
        response = self.client.get(reverse('reset_password') + '?next=' + reverse('account'))
        self.assertRedirects(response, reverse('account'), status_code=302)

    def test_reset_password_form(self):
        """ Check that the form contains the appropriate field """
        response = self.client.get(reverse('reset_password'))
        self.assertIn('<input class="form-control" id="id_email" name="email" placeholder="Email Address" type="text" />',
                      response.content.decode('utf-8'))

    def test_reset_password_redirect_logged_in(self):
        """ Check that if logged in we get a redirect to the dashboard """
        self.login()
        response = self.client.get(reverse('reset_password'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account'), status_code=302)

    def test_form_post(self):
        """ Check that the email is sent, and the PasswordResetRequest is created """
        response = self.client.get(reverse('reset_password'))

        with mock.patch('portal.views.send_password_request.delay') as mock_send_password_request:
            response = self.client.post(reverse('reset_password'), {
                'email': self.DUMMY_EMAIL
            })
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'We have sent an email with a reset password URL. Check that out!')

            reset_requests = PasswordResetRequest.objects.filter(user=self.user)
            self.assertEqual(len(reset_requests), 1)

            reset_request = reset_requests[0]
            self.assertEqual(reset_request.user, self.user)
            self.assertEqual(reset_request.resolved, False)
            self.assertIsNotNone(reset_request.secret)
            self.assertIsNone(reset_request.email_sent_date)

            mock_send_password_request.assert_called_once_with(reset_request.pk, mock.ANY)
            reset_password_url = mock_send_password_request.call_args[0][1]

            response = self.client.get(reset_password_url)
            self.assertEqual(response.status_code, 200)

    def test_password_reset(self):
        """
        Actually reset the password
        """
        self.make_paid(self.user)

        response = self.client.get(reverse('reset_password'))
        with mock.patch('portal.views.send_password_request.delay') as mock_send_password_request:
            response = self.client.post(reverse('reset_password'), {
                'email': self.DUMMY_EMAIL
            })
            reset_password_url = mock_send_password_request.call_args[0][1]

            response = self.client.get(reset_password_url)
            response = self.client.post(reset_password_url, {
                'password': 'newpass',
                'repeat_password': 'not-matching',
            })

            # It shouldn't redirect
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Passwords do not match')

            response = self.client.post(reset_password_url, {
                'password': 'newpass',
                'repeat_password': 'newpass',
            })

            # We should get redirected to login
            self.assertRedirects(response, reverse('login'), status_code=302)

            # Check that the password actually works
            response = self.client.post(reverse('login'), {
                'password': 'newpass',
                'email': self.DUMMY_EMAIL,
            })

            self.assertRedirects(response, reverse('upload_file'), status_code=302)

    def test_reusing_url(self):
        _ = self.client.get(reverse('reset_password'))
        with mock.patch('portal.views.send_password_request.delay') as mock_send_password_request:
            _ = self.client.post(reverse('reset_password'), {
                'email': self.DUMMY_EMAIL
            })
            reset_password_url = mock_send_password_request.call_args[0][1]

            _ = self.client.get(reset_password_url)
            response = self.client.post(reset_password_url, {
                'password': 'newpass',
                'repeat_password': 'newpass',
            })

            # We should get redirected to login
            self.assertRedirects(response, reverse('login'), status_code=302)

            response = self.client.get(reset_password_url)
            self.assertRedirects(response, reverse('reset_password'), status_code=302)


class UpdatePasswordTest(BeagleWebTest):
    def test_302(self):
        """
        What happens when we hit the url while logged in
        """

        self.login()
        url = reverse('update_password')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('account'), status_code=302)

    def test_302_next(self):
        self.login()
        url = reverse('update_password')
        response = self.client.get(url + '?next=' + reverse('account'))
        self.assertRedirects(response, reverse('account'), status_code=302)

    def test_no_payload(self):
        url = reverse('update_password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_wrong_payload(self):
        url = reverse('update_password')
        response = self.client.get(url + '?payload=aaaaa')
        self.assertEqual(response.status_code, 404)