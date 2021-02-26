from django.core.urlresolvers import reverse
from dogbone.testing.base import BeagleWebTest
from marketing.models import PurchasedSubscription, Coupon
from dogbone.app_settings.marketing_settings import YearlyPaidSubscription, PremiumMonthlyPaidSubscription


class PurchaseRouterTestCase(BeagleWebTest):

    ROUTER_URL = reverse('purchase_route')

    def test_simple(self):
        response = self.client.get(self.ROUTER_URL, follow=True)
        self.assertRedirects(response, reverse('signup') + '?next=%2Fpurchase',
                             status_code=302,
                             target_status_code=200,)

    def test_with_coupon(self):
        coupon = Coupon.objects.create(title='10% off Coupon',
                                       code='GETME10PERCENT',
                                       subscription=YearlyPaidSubscription.uid)

        response = self.client.get(self.ROUTER_URL + '?coupon=%s' % coupon.code, follow=True)

        self.assertRedirects(response, reverse('signup') + '?coupon=' + coupon.code + '&next=%2Fpurchase%2FYEARLY_PAID_SUBSCRIPTION%3Fcoupon%3DGETME10PERCENT',
                             status_code=302,
                             target_status_code=200,)
        self.assertContains(response, coupon.code)

    def test_with_subscription(self):
        response = self.client.get(self.ROUTER_URL + '?subscription=%s' % YearlyPaidSubscription.uid, follow=True)

        self.assertRedirects(response, reverse('signup') + '?subscription=' + YearlyPaidSubscription.uid +
                             '&next=%2Fpurchase%2FYEARLY_PAID_SUBSCRIPTION',
                             status_code=302,
                             target_status_code=200,)
        self.assertContains(response, YearlyPaidSubscription.name)

    def test_with_coupon_and_subscription(self):
        coupon = Coupon.objects.create(title='10% off Coupon',
                                       code='GETME10PERCENT',
                                       subscription=YearlyPaidSubscription.uid)

        response = self.client.get(self.ROUTER_URL + '?coupon=%s&subscription=%s' % (coupon.code, YearlyPaidSubscription.uid), follow=True)

        self.assertRedirects(response, reverse('signup') + '?coupon=' + coupon.code + '&subscription=' + YearlyPaidSubscription.uid + '&next=%2Fpurchase%2FYEARLY_PAID_SUBSCRIPTION%3Fcoupon%3DGETME10PERCENT',
                             status_code=302,
                             target_status_code=200,)
        self.assertContains(response, coupon.code)
        self.assertContains(response, YearlyPaidSubscription.name)

    def test_with_coupon_and_subscription_non_default_subscription(self):
        coupon = Coupon.objects.create(title='10% off Coupon',
                                       code='GETME10PERCENT',
                                       subscription=PremiumMonthlyPaidSubscription.uid)

        response = self.client.get(self.ROUTER_URL + '?coupon=%s&subscription=%s' % (coupon.code, PremiumMonthlyPaidSubscription.uid), follow=True)

        self.assertRedirects(response, reverse('signup') + '?coupon=' + coupon.code + '&subscription=' + PremiumMonthlyPaidSubscription.uid + '&next=%2Fpurchase%2FPREMIUM_MONTHLY_PAID_SUBSCRIPTION%3Fcoupon%3DGETME10PERCENT',
                             status_code=302,
                             target_status_code=200,)
        self.assertContains(response, coupon.code)
        self.assertContains(response, PremiumMonthlyPaidSubscription.name)

    def test_authenticated_simple(self):
        self.login()

        response = self.client.get(self.ROUTER_URL, follow=True)
        self.assertRedirects(response, reverse('purchase'),
                             status_code=302,
                             target_status_code=200,)

        self.assertContains(response, YearlyPaidSubscription.name)

    def test_authenticated_with_coupon(self):
        coupon = Coupon.objects.create(title='10% off Coupon',
                                       code='GETME10PERCENT',
                                       subscription=YearlyPaidSubscription.uid)

        self.login()

        response = self.client.get(self.ROUTER_URL + '?coupon=%s' % coupon.code, follow=True)

        self.assertRedirects(response, reverse('purchase_subscription',
                             kwargs={'subscription_uid': YearlyPaidSubscription.uid}) + '?coupon=' + coupon.code,
                             status_code=302,
                             target_status_code=200,)

        self.assertContains(response, YearlyPaidSubscription.name)

    def test_authenticated_with_coupon_and_subscription(self):
        coupon = Coupon.objects.create(title='10% off Coupon',
                                       code='GETME10PERCENT',
                                       subscription=YearlyPaidSubscription.uid)

        self.login()

        response = self.client.get(self.ROUTER_URL + '?coupon=%s&subscription=%s' % (coupon.code, YearlyPaidSubscription.uid), follow=True)

        self.assertRedirects(response, reverse('purchase_subscription',
                             kwargs={'subscription_uid': YearlyPaidSubscription.uid}) + '?coupon=' + coupon.code,
                             status_code=302,
                             target_status_code=200,)

        self.assertContains(response, YearlyPaidSubscription.name)

    def test_authenticated_with_coupon_and_subscription_non_default_subscription(self):
        coupon = Coupon.objects.create(title='10% off Coupon Premium Monthly',
                                       code='GETME10PERCENT',
                                       subscription=PremiumMonthlyPaidSubscription.uid)

        self.login()

        response = self.client.get(self.ROUTER_URL + '?coupon=%s&subscription=%s' % (coupon.code, PremiumMonthlyPaidSubscription.uid), follow=True)

        self.assertRedirects(response, reverse('purchase_subscription',
                             kwargs={'subscription_uid': PremiumMonthlyPaidSubscription.uid}) + '?coupon=' + coupon.code,
                             status_code=302,
                             target_status_code=200,)

        self.assertContains(response, PremiumMonthlyPaidSubscription.name)
