import mock
import datetime

from django.urls import reverse
from django.contrib.auth.models import User
from freezegun import freeze_time

from dogbone.testing.base import BeagleWebTest
from dogbone.app_settings.marketing_settings import StandardTrial, YearlyPaidSubscription, AllAccessTrial
from marketing.models import Coupon, PurchasedSubscription


class SimpleRegisterTestCase(BeagleWebTest):
    def test_200(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.generic.hubspot_submit_form'):
            response = self.client.post(url, data={'email': 'mail@email.com',
                                                   'password': 'mypass'}, follow=True)

            self.assertRedirects(response, reverse('dashboard'),
                                 status_code=302,
                                 target_status_code=200,)

            try:
                created_user = User.objects.get(email='mail@email.com')
                self.assertTrue(created_user.is_active)

                created_subscription = PurchasedSubscription.get_first_current_subscription(created_user)
                self.assertEqual(created_subscription.get_subscription(), AllAccessTrial)
            except User.DoesNotExist:
                self.assertTrue(False)

    def test_post_case_insensitive(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.generic.hubspot_submit_form'):
            response = self.client.post(url, data={'email': 'Mail@eMail.COM',
                                                   'password': 'mypass'}, follow=True)

            self.assertRedirects(response, reverse('dashboard'),
                                 status_code=302,
                                 target_status_code=200,)

            try:
                User.objects.get(email='mail@email.com')
            except User.DoesNotExist:
                self.assertTrue(False)

    def test_register_then_login(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.generic.hubspot_submit_form'):
            self.client.post(url, data={'email': 'Mail@eMail.COM', 'password': 'mypass'})

        self.client.logout()

        url = reverse('login')

        # Try to login with the original mixed case email
        response = self.client.post(url, data={'email': 'Mail@eMail.COM',
                                               'password': 'mypass'})

        self.assertEqual(response.status_code, 302)
        self.client.logout()

        # Try to login with the lowercase email
        response = self.client.post(url, data={'email': 'mail@email.com',
                                               'password': 'mypass'})

        self.assertEqual(response.status_code, 302)
        self.client.logout()

        # Try to login with an non-existing email
        response = self.client.post(url, data={'email': 'non-nexisting-Mail@eMail.COM',
                                               'password': 'mypass'})

        self.assertEqual(response.status_code, 200)



    def test_missing_email(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'password': 'mypass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')

    def test_missing_password(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'email': 'mail@email.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mail@email.com')
        self.assertContains(response, 'This field is required.')

        try:
            _ = User.objects.get(email='mail@email.com')
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    def test_existing_email(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={'email': self.DUMMY_EMAIL,
                                               'password': 'pass'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This email is already registered')

        try:
            _ = User.objects.get(username=self.DUMMY_EMAIL)
            self.assertTrue(False)
        except User.DoesNotExist:
            pass

    def test_invalid_prepopulated_email(self):
        url = reverse('signup')
        response = self.client.get(url + '?payload=aaaa')
        self.assertEqual(response.status_code, 200)

    def test_register_with_trial_coupon(self):
        coupon = Coupon(title='Trial Coupon',
                        code='GETMEIN',
                        subscription=StandardTrial.uid)

        coupon.save()

        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.views.hubspot_submit_form'):
            response = self.client.post(url, data={'email': 'mail@email.com',
                                                   'password': 'mypass',
                                                   'coupon': 'GETMEIN'}, follow=True)

            # redirect the user to login page
            self.assertRedirects(response, reverse('dashboard'),
                                 status_code=302,
                                 target_status_code=200,)

            try:
                created_user = User.objects.get(email='mail@email.com')
                self.assertTrue(created_user.is_active)
                purchased_subscriptions = PurchasedSubscription.objects.filter(buyer=created_user)
                self.assertEqual(len(purchased_subscriptions), 1)
            except User.DoesNotExist:
                self.assertTrue(False)

    def test_register_with_payable_coupon(self):
        coupon = Coupon(title='20% of Yearly Coupon',
                        code='GETMEIN20OFF',
                        subscription=YearlyPaidSubscription.uid,
                        discount_percent=20)

        coupon.save()

        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.views.hubspot_submit_form'):
            response = self.client.post(url, data={'email': 'mail@email.com',
                                                   'password': 'mypass',
                                                   'coupon': 'GETMEIN20OFF'}, follow=True)

            # redirect the user to login page
            self.assertRedirects(response,
                                 reverse('purchase_subscription', kwargs={'subscription_uid': YearlyPaidSubscription.uid}) + '?coupon=GETMEIN20OFF',
                                 status_code=302,
                                 target_status_code=200,)

            try:
                created_user = User.objects.get(email='mail@email.com')
                self.assertTrue(created_user.is_active)
                purchased_subscriptions = PurchasedSubscription.objects.filter(buyer=created_user)
                self.assertEqual(len(purchased_subscriptions), 0)
            except User.DoesNotExist:
                self.assertTrue(False)

    def test_register_with_invalid_coupon(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with mock.patch('portal.views.hubspot_submit_form'):
            response = self.client.post(url, data={'email': 'mail@email.com',
                                                   'password': 'mypass',
                                                   'coupon': 'NOSUCHTHING'}, follow=True)

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'This promo code is not valid, please try again.')
            self.assertRaises(User.DoesNotExist, User.objects.get, username='uuuuuuu')

    def test_register_with_expired_coupon(self):
        coupon = Coupon(title='Trial Coupon',
                        code='GETMEIN',
                        subscription=StandardTrial.uid,
                        start=datetime.datetime(year=2014, month=9, day=15, hour=10, minute=0, second=0),
                        end=datetime.datetime(year=2014, month=10, day=15, hour=10, minute=0, second=0))
        coupon.save()
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        with freeze_time('2014-10-16'):
            with mock.patch('portal.views.hubspot_submit_form'):
                response = self.client.post(url, data={'email': 'mail@email.com',
                                                       'password': 'mypass',
                                                       'coupon': 'GETMEIN'}, follow=True)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'This promo code has expired.')
                self.assertRaises(User.DoesNotExist, User.objects.get, username='uuuuuuu')


    def test_register_with_email_greater_than_30_characters_is_success(self):
        url = reverse('signup')
        email = 'test_register_with_email_greater_than_30_characters_is_success@beagle.com'

        with mock.patch('portal.generic.hubspot_submit_form'):
            response = self.client.post(
                url,
                data={'email': email, 'password': 'mypass'},
                follow=True
            )

            user = User.objects.get(email=email)

            self.assertEqual(user.email, email)
            self.assertEqual(len(user.username), 30)
            self.assertEqual(user.username, email[:30])

            self.assertRedirects(
                response,
                reverse('dashboard'),
                status_code=302,
                target_status_code=200
            )

    def test_register_with_email_greater_than_30_characters_with_similar_email_is_success(self):
        url = reverse('signup')
        email = 'test_register_with_email_greater_than_30_characters_is_success@beagle.com'
        similar_email = 'test_register_with_email_greater_than_30_characters_is_success+@beagle.com'

        user_existing = User.objects.create(username=email[:30], email=email)

        with mock.patch('portal.generic.hubspot_submit_form'):
            response = self.client.post(
                url,
                data={'email': similar_email, 'password': 'mypass'},
                follow=True
            )

            user = User.objects.get(email=similar_email)
            self.assertEqual(user.email, similar_email)
            self.assertEqual(user.username, similar_email[:28] + "_1")
            self.assertEqual(len(user.username), 30)

            self.assertRedirects(
                response,
                reverse('dashboard'),
                status_code=302,
                target_status_code=200
            )
