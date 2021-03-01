import mock
from django.core.urlresolvers import reverse
from django.conf import settings
from dogbone.testing.base import BeagleWebTest
from dogbone.app_settings.marketing_settings import YearlyPaidSubscription
from marketing.models import Coupon, PurchasedSubscription
from portal.tools import encrypt_str


class PaymentViewTest(BeagleWebTest):
    def test_200(self):
        url = reverse('purchase')
        self.login()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, str(YearlyPaidSubscription.price))

    def test_coupon(self):
        coupon = Coupon(title="Half Off",
                        code="HALFOFF",
                        subscription=YearlyPaidSubscription.uid,
                        discount_percent=50.0)

        coupon.save()
        self.login()

        url = reverse('purchase') + '?coupon=HALFOFF'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, str("2000.0"))

    @mock.patch('portal.views.log_intercom_custom_event')
    def test_free_coupon(self, mock_log_intercom):
        coupon = Coupon(title="Get It Free",
                        code="GETITFREE",
                        subscription=YearlyPaidSubscription.uid,
                        free=True)

        coupon.save()
        self.login()

        url = reverse('purchase') + '?coupon=GETITFREE'
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('payment_return'), status_code=302,
                             target_status_code=200)

        self.assertTrue(PurchasedSubscription.objects.filter(buyer=self.user, coupon_used=coupon).exists())
        self.assertEqual(Coupon.objects.get(pk=coupon.pk).use_count, 1)
        self.assertContains(response, 'WOW, Congrats! You now have your own Beagle subscription. Take it for a walk!')
        mock_log_intercom.assert_called_once_with(event_name='payment-accepted', email=self.DUMMY_EMAIL)

    def test_paypal_dict(self):
        with mock.patch('portal.views.PayPalPaymentsForm') as mock_paypal_form:
            with mock.patch('portal.tools.add_salt') as mock_add_salt:
                mock_add_salt.return_value = '12341234'

                url = reverse('purchase')
                self.login()

                _ = self.client.get(url)
                custom_field = encrypt_str('%s$%s$' % (YearlyPaidSubscription.uid, self.DUMMY_EMAIL))

                # mock_paypal_form.assert_called_with(initial={'amount': '948.0',
                #                                              'notify_url': mock.ANY,
                #                                              'invoice': mock.ANY,
                #                                              'business': settings.PAYPAL_RECEIVER_EMAIL,
                #                                              'item_name': YearlyPaidSubscription.name,
                #                                              'cancel_return': 'http://testserver' + reverse('payment_cancel'),
                #                                              'return_url': 'http://testserver' + reverse('payment_return'),
                #                                              'custom': custom_field})
                mock_paypal_form.assert_called_with(#button_type=mock.ANY,
                                                    initial={'business': 'iulius.curt@gmail.com',
                                                             'p3': 1,
                                                             'a3': '4000.0',
                                                             'notify_url': mock.ANY,
                                                             'invoice': mock.ANY,
                                                             'src': mock.ANY,
                                                             'cancel_return': 'http://testserver' + reverse('payment_cancel'),
                                                             'sra': mock.ANY,
                                                             'item_name': 'Beagle Yearly Paid Subscription',
                                                             'cmd': mock.ANY,
                                                             't3': 'Y',
                                                             'custom': custom_field,
                                                             'return_url': 'http://testserver' + reverse('payment_return'),})

    def test_paypal_dict_with_coupon(self):
        coupon = Coupon(title="Half Off",
                        code="HALFOFF",
                        subscription=YearlyPaidSubscription.uid,
                        discount_percent=50.0)

        coupon.save()

        with mock.patch('portal.views.PayPalPaymentsForm') as mock_paypal_form:
            with mock.patch('portal.tools.add_salt') as mock_add_salt:
                mock_add_salt.return_value = '12341234'

                url = reverse('purchase') + '?coupon=HALFOFF'
                self.login()

                _ = self.client.get(url)
                custom_field = encrypt_str('%s$%s$' % (YearlyPaidSubscription.uid, self.DUMMY_EMAIL))

                # mock_paypal_form.assert_called_with(initial={'amount': '948.0',
                #                                              'discount_amount': '474.0',
                #                                              'notify_url': mock.ANY,
                #                                              'invoice': mock.ANY,
                #                                              'business': settings.PAYPAL_RECEIVER_EMAIL,
                #                                              'item_name': YearlyPaidSubscription.name,
                #                                              'cancel_return': 'http://testserver' + reverse('payment_cancel'),
                #                                              'return_url': 'http://testserver' + reverse('payment_return'),
                #                                              'custom': custom_field})
                mock_paypal_form.assert_called_with(#button_type=mock.ANY,
                                                    initial={'business': 'iulius.curt@gmail.com',
                                                             'p3': 1,
                                                             'a3': '2000.0',
                                                             'notify_url': mock.ANY,
                                                             'invoice': mock.ANY,
                                                             'src': mock.ANY,
                                                             'cancel_return': 'http://testserver' + reverse('payment_cancel'),
                                                             'sra': mock.ANY,
                                                             'item_name': 'Beagle Yearly Paid Subscription',
                                                             'cmd': mock.ANY,
                                                             't3': 'Y',
                                                             'custom': custom_field,
                                                             'return_url': 'http://testserver' + reverse('payment_return'),})

