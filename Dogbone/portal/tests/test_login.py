from dogbone.testing.base import BeagleWebTest
from authentication.models import OneTimeLoginHash
from django.urls import reverse


class LoginTestCase(BeagleWebTest):

    def test_200(self):
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<input autofocus="autofocus" class="form-control" id="id_email" name="email" placeholder="Email Address" type="text" />')
        self.assertContains(response, '<input class="form-control" id="id_password" name="password" placeholder="Password" type="password" />')

    def test_redirect(self):
        self.login()
        url = reverse('login')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('account'), status_code=302)

    def test_next_redirect(self):
        self.login()
        url = reverse('login')
        response = self.client.get(url+'?next=' + reverse('account'))
        self.assertRedirects(response, reverse('account'), status_code=302)

    def test_autofocus_on_password(self):
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'email': self.DUMMY_EMAIL, 'password': 'WRONG_PASSWORD'})
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<input class="form-control" id="id_email" name="email" placeholder="Email Address" type="text" value="%s" />' % self.DUMMY_EMAIL)
        self.assertContains(response, '<input autofocus="autofocus" class="form-control" id="id_password" name="password" placeholder="Password" type="password" />')


class OneTimeLoginTestCase(BeagleWebTest):

    def test_login_view(self):
        onetime_hash_model = OneTimeLoginHash.create(self.user)
        login_hash = onetime_hash_model.get_hash()
        url = reverse('login') + '?hash=%s' % login_hash
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('account'), status_code=302, target_status_code=200)

    def test_already_used(self):
        onetime_hash_model = OneTimeLoginHash.create(self.user)
        login_hash = onetime_hash_model.get_hash()
        url = reverse('login') + '?hash=%s' % login_hash
        _ = self.client.get(url, follow=True)

        # Try to reuse it
        response = self.client.get(url, follow=False)
        response.status_code = 200

    def test_non_existing_hash(self):
        url = reverse('login') + '?hash=%s' % '1234'
        _ = self.client.get(url, follow=True)

        response = self.client.get(url, follow=False)
        self.assertEqual(response.status_code, 200)
