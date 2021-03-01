import json
import mock
import datetime
import unittest

from user_sessions.models import Session
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from freezegun import freeze_time

from core.models import ExternalInvite, Document
from dogbone.testing.base import BeagleWebTest
from dogbone.app_settings.marketing_settings import StandardTrial, YearlyPaidSubscription, AllAccessTrial, UnlimitedBrowserExtensionSubscription
from marketing.models import Coupon, PurchasedSubscription


class IndexTestCase(BeagleWebTest):

    def test_200(self):
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_redirect(self):
        self.login()
        url = reverse('index')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('account'), status_code=302)


class LogoutTestCase(BeagleWebTest):

    def test_302(self):
        url = reverse('logout')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('index'), status_code=302)

    def test_logged_in(self):
        self.login()
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 200)
        url = reverse('logout')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('index'), status_code=302)

        response = self.client.get(reverse('account'))
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('account'), status_code=302)


class ReportTestCase(BeagleWebTest):
    def test_302(self):
        url = reverse('report', kwargs={'uuid': '123'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + '?next=' + url, status_code=302)

    def test_404(self):
        self.login()
        url = reverse('report', kwargs={'uuid': '1234'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_200(self):
        self.login()
        d = self.create_document('Title', self.user, pending=False)
        url = reverse('report', kwargs={'uuid': d.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class RegisterTestCase(BeagleWebTest):
    def test_200(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)

    @unittest.skip("Just redirecting")
    def test_post(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.views.hubspot_submit_form'):
            response = self.client.post(url, data={
                                                    'first': 'Che',
                                                    'last': 'Guevara',
                                                    'username': 'uuuuuuu',
                                                    'email': 'mail@email.com',
                                                    'phone': '+1(613)-967-1111',
                                                    'password': 'mypass',
                                                    'repeat_password': 'mypass'}, follow=True)

            self.assertRedirects(response, reverse('dashboard'),
                                 status_code=302,
                                 target_status_code=200,)

            try:
                created_user = User.objects.get(username='uuuuuuu')
                self.assertTrue(created_user.is_active)

                created_subscription = PurchasedSubscription.get_first_current_subscription(created_user)
                self.assertEqual(created_subscription.get_subscription(), AllAccessTrial)
            except User.DoesNotExist:
                self.assertTrue(False)

    @unittest.skip("Just redirecting")
    def test_not_matching_passwords(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'email': 'mail@email.com',
                                               'password': 'mypass',
                                               'repeat_password': 'somethingelse'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'Passwords do not match')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    @unittest.skip("Just redirecting")
    def test_missing_username(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'email': 'mail@email.com',
                                               'password': 'mypass',
                                               'repeat_password': 'mypass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'This field is required.')

        try:
            _ = User.objects.get(email='mail@email.com')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    @unittest.skip("Just redirecting")
    def test_missing_email(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'password': 'mypass',
                                               'repeat_password': 'mypass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'This field is required.')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    @unittest.skip("Just redirecting")
    def test_missing_first_name(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'username': 'uuuuuuu',
                                               'email': 'mail@email.com',
                                               'password': 'mypass',
                                               'repeat_password': 'mypass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'This field is required.')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    @unittest.skip("Just redirecting")
    def test_missing_password(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'email': 'mail@email.com',
                                               'repeat_password': 'somethingelse'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'This field is required.')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    @unittest.skip("Just redirecting")
    def test_missing_repeat_password(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'email': 'mail@email.com',
                                               'password': 'somethingelse'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'Passwords do not match')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    @unittest.skip("Just redirecting")
    def test_existing_email(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'email': self.DUMMY_EMAIL,
                                               'password': 'pass',
                                               'repeat_password': 'pass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'This email is already registered')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    @unittest.skip("Just redirecting")
    def test_existing_username(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'Che',
                                                'last': 'Guevara',
                                                'username': self.DUMMY_USERNAME,
                                                'email': 'email@email.com',
                                                'phone': '+1(613)-967-1111',
                                                'password': 'pass',
                                                'repeat_password': 'pass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email@email.com')
        self.assertContains(response, 'This username is already registered')

    @unittest.skip("Just redirecting")
    def test_invalid_prepopulated_email(self):
        url = reverse('register')
        response = self.client.get(url + '?payload=aaaa')
        self.assertEqual(response.status_code, 200)

    @unittest.skip("Just redirecting")
    def test_register_with_trial_coupon(self):
        coupon = Coupon(title='Trial Coupon',
                        code='GETMEIN',
                        subscription=StandardTrial.uid)

        coupon.save()

        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.views.hubspot_submit_form'):
            response = self.client.post(url, data={'first': 'Che',
                                                    'last': 'Guevara','username': 'uuuuuuu',
                                                    'email': 'mail@email.com',
                                                    'phone': '+1(613)-967-1111',
                                                    'password': 'mypass',
                                                    'repeat_password': 'mypass',
                                                    'coupon': 'GETMEIN'}, follow=True)

            # redirect the user to login page
            self.assertRedirects(response, reverse('dashboard'),
                                 status_code=302,
                                 target_status_code=200,)

            try:
                created_user = User.objects.get(username='uuuuuuu')
                self.assertTrue(created_user.is_active)
                purchased_subscriptions = PurchasedSubscription.objects.filter(buyer=created_user)
                self.assertEqual(len(purchased_subscriptions), 1)
            except User.DoesNotExist:
                self.assertTrue(False)

    @unittest.skip("Just redirecting")
    def test_register_with_payable_coupon(self):
        coupon = Coupon(title='20% of Yearly Coupon',
                        code='GETMEIN20OFF',
                        subscription=YearlyPaidSubscription.uid,
                        discount_percent=20)

        coupon.save()

        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.views.hubspot_submit_form'):
            response = self.client.post(url, data={'first': 'Che',
                                                    'last': 'Guevara',
                                                    'username': 'uuuuuuu',
                                                    'email': 'mail@email.com',
                                                    'phone': '+1(613)-967-1111',
                                                    'password': 'mypass',
                                                    'repeat_password': 'mypass',
                                                    'coupon': 'GETMEIN20OFF'}, follow=True)

            # redirect the user to login page
            self.assertRedirects(response, reverse('purchase') + '?coupon=GETMEIN20OFF',
                                 status_code=302,
                                 target_status_code=200,)

            try:
                created_user = User.objects.get(username='uuuuuuu')
                self.assertTrue(created_user.is_active)
                purchased_subscriptions = PurchasedSubscription.objects.filter(buyer=created_user)
                self.assertEqual(len(purchased_subscriptions), 0)
            except User.DoesNotExist:
                self.assertTrue(False)

    @unittest.skip("Just redirecting")
    def test_register_with_invalid_coupon(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.views.hubspot_submit_form'):
            response = self.client.post(url, data={'first': 'Che',
                                                   'last': 'Guevara',
                                                   'username': 'uuuuuuu',
                                                   'email': 'mail@email.com',
                                                   'phone': '+1(613)-967-1111',
                                                   'password': 'mypass',
                                                   'repeat_password': 'mypass',
                                                   'coupon': 'NOSUCHTHING'}, follow=True)

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'This promo code is not valid, please try again.')
            self.assertRaises(User.DoesNotExist, User.objects.get, username='uuuuuuu')

    @unittest.skip("Just redirecting")
    def test_register_with_expired_coupon(self):
        coupon = Coupon(title='Trial Coupon',
                        code='GETMEIN',
                        subscription=StandardTrial.uid,
                        start=datetime.datetime(year=2014, month=9, day=15, hour=10, minute=0, second=0),
                        end=datetime.datetime(year=2014, month=10, day=15, hour=10, minute=0, second=0))
        coupon.save()
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with freeze_time('2014-10-16'):
            with mock.patch('portal.views.hubspot_submit_form'):
                response = self.client.post(url, data={'first': 'hank',
                                                        'username': 'uuuuuuu',
                                                        'email': 'mail@email.com',
                                                        'phone': '+1(613)-967-1111',
                                                        'password': 'mypass',
                                                        'repeat_password': 'mypass',
                                                        'coupon': 'GETMEIN'}, follow=True)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'This promo code has expired.')
                self.assertRaises(User.DoesNotExist, User.objects.get, username='uuuuuuu')


class BrowserExtensionRegisterTestCase(BeagleWebTest):
    def test_200(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.views.hubspot_submit_form'):
            response = self.client.post(url, data={
                                                    'first': 'Che',
                                                    'last': 'Guevara',
                                                    'username': 'uuuuuuu',
                                                    'email': 'mail@email.com',
                                                    'phone': '+1(613)-967-1111',
                                                    'password': 'mypass',
                                                    'repeat_password': 'mypass'}, follow=True)

            self.assertRedirects(response, reverse('welcome_browser_extension'),
                                 status_code=302,
                                 target_status_code=200,)

            try:
                created_user = User.objects.get(username='uuuuuuu')
                self.assertTrue(created_user.is_active)

                created_subscription = PurchasedSubscription.get_first_current_subscription(created_user)
                self.assertEqual(created_subscription.get_subscription(), UnlimitedBrowserExtensionSubscription)
            except User.DoesNotExist:
                self.assertTrue(False)

    def test_not_matching_passwords(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'email': 'mail@email.com',
                                               'password': 'mypass',
                                               'repeat_password': 'somethingelse'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'Passwords do not match')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    def test_missing_username(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'email': 'mail@email.com',
                                               'password': 'mypass',
                                               'repeat_password': 'mypass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'This field is required.')

        try:
            _ = User.objects.get(email='mail@email.com')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    def test_missing_email(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'password': 'mypass',
                                               'repeat_password': 'mypass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'This field is required.')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    def test_missing_first_name(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'username': 'uuuuuuu',
                                               'email': 'mail@email.com',
                                               'password': 'mypass',
                                               'repeat_password': 'mypass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'This field is required.')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    def test_missing_password(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'email': 'mail@email.com',
                                               'repeat_password': 'somethingelse'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'This field is required.')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    def test_missing_repeat_password(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'email': 'mail@email.com',
                                               'password': 'somethingelse'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'Passwords do not match')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    def test_existing_email(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'hank',
                                               'username': 'uuuuuuu',
                                               'email': self.DUMMY_EMAIL,
                                               'password': 'pass',
                                               'repeat_password': 'pass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uuuuuuu')
        self.assertContains(response, 'This email is already registered')

        try:
            _ = User.objects.get(username='uuuuuuu')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    def test_existing_username(self):
        url = reverse('register_browser_extension')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'first': 'Che',
                                               'last': 'Guevara',
                                               'username': self.DUMMY_USERNAME,
                                               'email': 'email@email.com',
                                               'phone': '+1(613)-967-1111',
                                               'password': 'pass',
                                               'repeat_password': 'pass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email@email.com')
        self.assertContains(response, 'This username is already registered')

    def test_upload_app_upload_with_extension_subscription(self):
        FAKE_FILE_HANDLE = self.get_temporary_text_file()

        self.make_extension_user(self.user)
        self.login()
        response = self.client.get(reverse('upload_file'))
        self.assertEqual(response.status_code, 200)

        with mock.patch('core.tasks.process_document_conversion.delay') as mock_process_document_conversion:
            with mock.patch('portal.views.log_intercom_custom_event.delay') as mock_ile:
                with mock.patch('portal.models.update_intercom_document_count.delay') as mock_idc:
                    with mock.patch('portal.models.hubspot_update_contact_properties.delay') as mock_hua:
                        with mock.patch('portal.tasks.hubspot_get_vid') as mock_hgv:
                            mock_hgv.return_value = 2133
                            response = self.client.post(reverse('upload'),
                                                {'filesource': 'local', 'file': FAKE_FILE_HANDLE})

                            # No documents were created
                            created_documents = Document.objects.all()
                            self.assertEqual(len(created_documents), 0)

                            self.assertFalse(mock_process_document_conversion.called)
                            self.assertEqual(response.status_code, 403)

                            self.assertFalse(mock_ile.called)
                            self.assertFalse(mock_idc.called)
                            self.assertFalse(mock_hua.called)
                            self.assertFalse(mock_hgv.called)


class AccountTestCase(BeagleWebTest):
    def test_302(self):
        url = reverse('account')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('account'), status_code=302)

    def test_200(self):
        self.login()
        url = reverse('account')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ExternalRegisterTestCase(BeagleWebTest):
    def test_account_creation(self):
        # Make a request to the external invite API endpoint and create an external invite
        self.make_paid(self.user)
        self.login()
        document = self.create_document('Title', self.user, pending=False)
        api_url = reverse('document_issued_invitations_list_view', kwargs={'uuid': document.uuid})
        with mock.patch('api_v1.invites.endpoints.send_external_invite.delay') as mock_send_invite:
            with mock.patch('portal.views.hubspot_submit_form'):
                response = self.client.post(api_url + '?external=true',
                                            data=json.dumps({'invitee': 'external@email.com'}),
                                            content_type='application/json')

                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)

                self.assertEqual(len(data['objects']), 1)

                # Check that the external invite was created
                ext_invites = ExternalInvite.objects.all()
                self.assertEqual(len(ext_invites), 1)

                # Check that the send email request was properly called
                mock_send_invite.assert_called_once_with(ext_invites[0].pk, mock.ANY)
                register_url = mock_send_invite.call_args[0][1]
                print 'REGISTER_URL', register_url

                # Check that the email redirects properly
                self.logout()
                response = self.client.get(register_url)
                self.assertRedirects(response, reverse('report', kwargs={'uuid': document.uuid}), status_code=302)

                # Check that the user account was properly created
                ext_user = User.objects.get(email='external@email.com')
                self.assertEqual(ext_user.username, 'external@email.com')

                # Check that a session is opened
                self.assertGreaterEqual(len(Session.objects.filter(user=ext_user)), 1)
