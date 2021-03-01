from datetime import timedelta
from django.utils.timezone import now
from django.core.urlresolvers import reverse
from dogbone.testing.base import BeagleWebTest
from marketing.models import PurchasedSubscription, Coupon
from dogbone.app_settings.marketing_settings import YearlyPaidSubscription


class RedeemCouponTest(BeagleWebTest):

    def test_get_200(self):
        self.login()
        url = reverse('redeem_coupon')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_form_field_exists(self):
        self.login()
        url = reverse('redeem_coupon')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'redeem_coupon.html')
        self.assertContains(response, '<input name="coupon" placeholder="Have a coupon code? Enter it here" value="" autocomplete=off>')

    def test_redeem_coupon(self):
        self.login()
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 0)
        url = reverse('redeem_coupon')
        _ = Coupon.objects.create(title='AWESOMENESS',
                                  code='AWSM',
                                  subscription=YearlyPaidSubscription.uid,
                                  free=True)
        response = self.client.get(url + '?coupon=AWSM')
        self.assertContains(response, '<li class="success">Your coupon has been applied. We added you a &quot;Beagle Yearly Paid Subscription&quot; subscription</li>')
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 1)
        ps = PurchasedSubscription.get_current_subscriptions(self.user)[0]
        self.assertEqual(ps.get_subscription(), YearlyPaidSubscription)

    def test_non_existing_coupon(self):
        self.login()
        url = reverse('redeem_coupon')
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 0)
        response = self.client.get(url + '?coupon=NONEXISTING')
        self.assertContains(response, '<li class="error">This is not a valid coupon code, please try again</li>')
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 0)

    def test_expired_coupon(self):
        self.login()
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 0)
        url = reverse('redeem_coupon')
        now_time = now()
        coupon = Coupon.objects.create(title='AWESOMENESS',
                                       code='AWSM',
                                       subscription=YearlyPaidSubscription.uid,
                                       free=True,
                                       start=now_time - timedelta(days=7),
                                       end=now_time - timedelta(days=2))
        self.assertTrue(coupon.is_expired)
        response = self.client.get(url + '?coupon=AWSM')
        self.assertContains(response, '<li class="error">This is coupon has expired, sorry</li>')
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 0)

    def test_already_redeemed_coupon(self):
        self.login()
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 0)
        url = reverse('redeem_coupon')
        _ = Coupon.objects.create(title='AWESOMENESS',
                                  code='AWSM',
                                  subscription=YearlyPaidSubscription.uid,
                                  free=True)
        _ = self.client.get(url + '?coupon=AWSM')
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 1)
        response = self.client.get(url + '?coupon=AWSM')
        self.assertContains(response, '<li class="error">Sorry, you already redeemed this coupon</li>')
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 1)

    def test_not_free_coupon(self):
        self.login()
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 0)
        url = reverse('redeem_coupon')
        coupon = Coupon.objects.create(title='AWESOMENESS',
                                       code='AWSM',
                                       subscription=YearlyPaidSubscription.uid,
                                       special_price=150)
        self.assertFalse(coupon.is_free)
        response = self.client.get(url + '?coupon=AWSM')
        self.assertContains(response, '<li class="error">Sorry, this coupon is not redeemable without paying</li>')
        self.assertEqual(len(PurchasedSubscription.objects.filter(buyer=self.user)), 0)
