import datetime
from freezegun import freeze_time
from pytz import UTC

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from marketing.subscriptions import Subscription
from marketing.models import PurchasedSubscription, Coupon


class UnlimitedSubscription(Subscription):
    __abstract__ = False
    uid = "Unlimited"
    name = "This Subscription"
    description = "This description"
    price = 200.0


class SevenDaySubscription(Subscription):
    __abstract__ = False
    uid = "7day"
    name = "7day Subscription"
    description = "7day description"
    price = 10.99
    duration = datetime.timedelta(days=7)


class UserTestCase(TestCase):
    def test_get_current_subscription(self):
        """
        Test if `get_current_subscription` for a user with an active subscription works as expected
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')
        purchased = PurchasedSubscription(buyer=user,
                                          subscription=UnlimitedSubscription.uid,
                                          start=timezone.now() - datetime.timedelta(days=5),
                                          end=timezone.now() + datetime.timedelta(days=5))
        purchased.save()

        self.assertEqual(purchased, PurchasedSubscription.get_first_current_subscription(user))

    def test_get_current_subscription_without_one(self):
        """
        Test if `get_current_subscription` for a user without an active subscription works as expected
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')

        self.assertEqual(None, PurchasedSubscription.get_first_current_subscription(user))

    def test_has_no_active_subscription(self):
        """
        Test `PurchasedSubscription.has_active_subscription` for user without active subscription
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')
        self.assertFalse(PurchasedSubscription.has_active_subscription(user))

    def test_has_active_subscription(self):
        """
        Test `PurchasedSubscription.has_active_subscription` for user with active subscription
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')
        purchased = PurchasedSubscription(buyer=user,
                                          subscription=UnlimitedSubscription.uid)

        purchased.save()
        self.assertTrue(PurchasedSubscription.has_active_subscription(user))

    def test_earliest_subscription_time(self):
        """
        Test no active subscription
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')
        self.assertEqual(PurchasedSubscription.earliest_subscription_start(user),
                         timezone.datetime.now(tz=UTC).replace(hour=0, minute=0, second=0, microsecond=0))

    def test_earliest_subscription_time_with_subscription(self):
        """
        Test `PurchasedSubscription.earliest_subscription_start` for a user with an active subscription
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')
        purchased = PurchasedSubscription(buyer=user,
                                          subscription=UnlimitedSubscription.uid,
                                          start=timezone.now() - datetime.timedelta(days=5),
                                          end=timezone.now() + datetime.timedelta(days=5))
        purchased.save()

        self.assertEqual(PurchasedSubscription.earliest_subscription_start(user),
                         (timezone.datetime.now(tz=UTC) + datetime.timedelta(days=5))
                         .replace(hour=0, minute=0, second=0, microsecond=0))

    def test_earliest_subscription_time_with_multiple_subscriptions(self):
        """
        Test `PurchasedSubscription.earliest_subscription_start`
        for a user with more than on subscription, one being active
        """

        user = User.objects.create_user('username', email='some@email.com', password='p@$$')
        purchased1 = PurchasedSubscription(buyer=user,
                                           subscription=UnlimitedSubscription.uid,
                                           start=timezone.now() - datetime.timedelta(days=5),
                                           end=timezone.now() + datetime.timedelta(days=5))
        purchased1.save()

        purchased2 = PurchasedSubscription(buyer=user,
                                           subscription=UnlimitedSubscription.uid,
                                           start=timezone.now() + datetime.timedelta(days=6),
                                           end=timezone.now() + datetime.timedelta(days=25))
        purchased2.save()

        self.assertEqual(PurchasedSubscription.earliest_subscription_start(user),
                         (timezone.datetime.now(tz=UTC) + datetime.timedelta(days=25))
                         .replace(hour=0, minute=0, second=0, microsecond=0))


class PurchasedSubscriptionTestCase(TestCase):
    def test_get_current_subscription(self):
        """
        Test getting the current subscription of the user
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')

        purchased = PurchasedSubscription(buyer=user,
                                          subscription=UnlimitedSubscription.uid)

        purchased.save()
        current_subscription = PurchasedSubscription.get_first_current_subscription(user)
        self.assertEqual(purchased, current_subscription)

    def test_get_weekly_subscription(self):
        """
        Test user with different subscription in different time frames
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')

        purchased = PurchasedSubscription(buyer=user,
                                          subscription=SevenDaySubscription.uid)

        purchased.save()
        current_subscription = PurchasedSubscription.get_first_current_subscription(user)
        self.assertEqual(purchased, current_subscription)

        over3days = timezone.now() + datetime.timedelta(days=3)

        with freeze_time(over3days):
            current_subscription = PurchasedSubscription.get_first_current_subscription(user)
            self.assertEqual(current_subscription, current_subscription)

        over6days23hours = timezone.now() + datetime.timedelta(days=6, hours=23)

        with freeze_time(over6days23hours):
            current_subscription = PurchasedSubscription.get_first_current_subscription(user)
            self.assertEqual(current_subscription, current_subscription)

        over7days = timezone.now() + datetime.timedelta(days=7, minutes=2)

        with freeze_time(over7days):
            current_subscription = PurchasedSubscription.get_first_current_subscription(user)
            self.assertEqual(current_subscription, None)

        ago1day = timezone.now() - datetime.timedelta(days=1)

        with freeze_time(ago1day):
            current_subscription = PurchasedSubscription.get_first_current_subscription(user)
            self.assertEqual(current_subscription, None)


class TestCoupon(TestCase):
    def test_user_already_used_coupon(self):
        """
        Test if the already used by user logic works
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')
        coupon = Coupon(title='Some coupon',
                        code='BEAGLE_IS_COOL',
                        subscription=SevenDaySubscription.uid,
                        free=True)

        coupon.save()

        coupon.create_subscription(user, persist=True)

        self.assertEqual(PurchasedSubscription.objects.filter(buyer=user, coupon_used=coupon,
                                                              subscription=SevenDaySubscription.uid).count(), 1)

        self.assertTrue(coupon.used_by(user))

    def test_use_count(self):
        """
        Test if the use counter accurately tracks the use
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')
        coupon = Coupon(title='Some coupon',
                        code='BEAGLE_IS_COOL',
                        subscription=SevenDaySubscription.uid,
                        free=True)

        coupon.save()
        coupon.create_subscription(user, persist=True)
        coupon = Coupon.objects.get(pk=coupon.pk)
        self.assertEqual(coupon.use_count, 1)

    def test_max_use_count(self):
        """
        Test if hte max_use_count restriction works accordingly
        """
        user = User.objects.create_user('username', email='some@email.com', password='p@$$')
        coupon = Coupon(title='Some coupon',
                        code='BEAGLE_IS_COOL',
                        subscription=SevenDaySubscription.uid,
                        free=True,
                        max_use_count=1)

        coupon.save()
        coupon.create_subscription(user, persist=True)
        coupon = Coupon.objects.get(pk=coupon.pk)
        self.assertTrue(coupon.is_expired)

    def test_get_subscription(self):
        """
        Test if the subscription is correctly retrieved
        """
        coupon = Coupon(title='Some coupon',
                        code='BEAGLE_IS_COOL',
                        subscription=SevenDaySubscription.uid,
                        free=True)

        coupon.save()

        self.assertEqual(coupon.get_subscription(), SevenDaySubscription)

    def test_purchase_price_free(self):
        """
        Test if the free benefit works correctly
        """
        coupon = Coupon(title='Some coupon',
                        code='BEAGLE_IS_COOL',
                        subscription=SevenDaySubscription.uid,
                        free=True)

        coupon.save()

        self.assertTrue(coupon.is_free)
        self.assertEqual(coupon.purchase_price, 0.0)

    def test_purchase_price_percent_discount(self):
        """
        Test if the special percent benefit works correctly
        """
        coupon = Coupon(title='Some coupon',
                        code='BEAGLE_IS_COOL',
                        subscription=UnlimitedSubscription.uid,
                        discount_percent=20)
        coupon.save()
        self.assertFalse(coupon.is_free)
        self.assertEqual(coupon.purchase_price, 160.0)

    def test_purchase_price_unit_discount(self):
        """
        Test if the unit discount works correctly
        """
        coupon = Coupon(title='Some coupon',
                        code='BEAGLE_IS_COOL',
                        subscription=UnlimitedSubscription.uid,
                        discount_units=15)
        coupon.save()
        self.assertFalse(coupon.is_free)
        self.assertEqual(coupon.purchase_price, 185.0)

    def test_purchase_price_special(self):
        """
        Test if the special price benefit works correctly
        """
        coupon = Coupon(title='Some coupon',
                        code='BEAGLE_IS_COOL',
                        subscription=UnlimitedSubscription.uid,
                        special_price=15)
        coupon.save()
        self.assertFalse(coupon.is_free)
        self.assertEqual(coupon.purchase_price, 15.0)

    def test_expire_date(self):
        """
        Test if a coupon expires after a certain date
        """
        coupon = Coupon(title='Some coupon',
                        code='BEAGLE_IS_COOL',
                        subscription=UnlimitedSubscription.uid,
                        special_price=15,
                        start=datetime.datetime(2014, 5, 10),
                        end=datetime.datetime(2014, 6, 10))
        coupon.save()

        with freeze_time(datetime.datetime(2014, 5, 20)):
            self.assertFalse(coupon.is_expired)
            self.assertTrue(coupon.is_available)

        with freeze_time(datetime.datetime(2014, 6, 11)):
            self.assertTrue(coupon.is_expired)
            self.assertFalse(coupon.is_available)
