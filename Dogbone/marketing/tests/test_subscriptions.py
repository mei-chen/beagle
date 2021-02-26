from django.test import TestCase
from marketing.subscriptions import Subscription
from marketing.currencies import Currency


class SubscriptionTestCase(TestCase):
    def test_subclasses(self):
        class Subscription1(Subscription):
            __abstract__ = False
            uid = "SUBS1"
            name = "Subscription1"
            description = "Description1"

        class Subscription2(Subscription):
            __abstract__ = False
            uid = "SUBS2"
            name = "Subscription2"
            description = "Description2"

        self.assertIn(Subscription1, Subscription.all())
        self.assertIn(Subscription2, Subscription.all())

    def test_choices(self):
        class Subscription1(Subscription):
            __abstract__ = False
            uid = "SUBS11"
            name = "Subscription11"
            description = "Description1"

        class Subscription2(Subscription):
            __abstract__ = False
            uid = "SUBS21"
            name = "Subscription21"
            description = "Description2"

        self.assertIn((Subscription1.uid, str(Subscription1)), Subscription.choices())
        self.assertIn((Subscription2.uid, str(Subscription2)), Subscription.choices())

    def test_get_by_uid(self):
        class Subscription1(Subscription):
            __abstract__ = False
            uid = "SUBS111"
            name = "Subscription111"
            description = "Description1"

        class Subscription2(Subscription):
            __abstract__ = False
            uid = "SUBS211"
            name = "Subscription211"
            description = "Description2"

        self.assertEqual(Subscription1, Subscription.get_by_uid("SUBS111"))
        self.assertEqual(Subscription2, Subscription.get_by_uid("SUBS211"))

    def test_get_by_name(self):
        class Subscription1(Subscription):
            __abstract__ = False
            uid = "SUBS1111"
            name = "Subscription1111"
            description = "Description1"

        class Subscription2(Subscription):
            __abstract__ = False
            uid = "SUBS2111"
            name = "Subscription2111"
            description = "Description2"

        self.assertEqual(Subscription1, Subscription.get_by_name("Subscription1111"))
        self.assertEqual(Subscription2, Subscription.get_by_name("Subscription2111"))

    def test_free_str(self):
        class SomeSubscription(Subscription):
            __abstract__ = False
            uid = "ID"
            name = "SS"
            description = "DESC"

        self.assertEqual("SS - [FREE] (DESC)", str(SomeSubscription))

    def test_paid_str(self):
        class SomeSubscription(Subscription):
            __abstract__ = False
            uid = "ID1"
            name = "SS1"
            description = "DESC"

            price = 15.0

        self.assertEqual("SS1 - [USD15.0] (DESC)", str(SomeSubscription))

    def test_paid_can_str(self):
        class SomeSubscription(Subscription):
            __abstract__ = False
            uid = "ID11"
            name = "SS11"
            description = "DESC"

            price = 115.0
            currency = Currency.CAN

        self.assertEqual("SS11 - [CAN115.0] (DESC)", str(SomeSubscription))

    def test_nested_subscriptions(self):
        class Type1Subscription(Subscription):
            __abstract__ = True

        class Type2Subscription(Subscription):
            __abstract__ = True

        class Type1Subscription1(Type1Subscription):
            __abstract__ = False
            uid = "Type1Subscription1"
            name = "Type1Subscription1"
            description = "Type1Subscription1"

        class Type1Subscription2(Type1Subscription):
            __abstract__ = False
            uid = "Type1Subscription2"
            name = "Type1Subscription2"
            description = "Type1Subscription2"

        class Type2Subscription1(Type2Subscription):
            __abstract__ = False
            uid = "Type2Subscription1"
            name = "Type2Subscription1"
            description = "Type2Subscription1"

        self.assertIn(Type1Subscription1, Subscription.all())
        self.assertIn(Type1Subscription2, Subscription.all())
        self.assertIn(Type2Subscription1, Subscription.all())
        self.assertEqual(set(Type1Subscription.all()), set([Type1Subscription1, Type1Subscription2]))
        self.assertEqual(set(Type2Subscription.all()), set([Type2Subscription1]))

    def test_subscription_includes(self):
        class Type1Subscription(Subscription):
            __abstract__ = True

        class Type2Subscription(Subscription):
            __abstract__ = True

        class Type1Subscription1(Type1Subscription):
            __abstract__ = False
            uid = "Type1Subscription1"
            name = "Type1Subscription1"
            description = "Type1Subscription1"

        class Type1Subscription2(Type1Subscription):
            __abstract__ = False
            uid = "Type1Subscription2"
            name = "Type1Subscription2"
            description = "Type1Subscription2"

        class Type2Subscription1(Type2Subscription):
            __abstract__ = False
            uid = "Type2Subscription1"
            name = "Type2Subscription1"
            description = "Type2Subscription1"

        self.assertTrue(Type1Subscription.includes(Type1Subscription1))
        self.assertTrue(Type1Subscription.includes(Type1Subscription2))

        self.assertTrue(Type2Subscription.includes(Type2Subscription1))
