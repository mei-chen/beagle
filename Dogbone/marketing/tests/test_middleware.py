import mock
import datetime
from freezegun import freeze_time
from pytz import UTC

from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.utils import timezone
from marketing.subscriptions import Subscription
from marketing.models import PurchasedSubscription, Coupon

from marketing.middleware import ActionManagerMiddleware


class ActionManagerMiddlewareTestCase(TestCase):
    def setUp(self):
        self.amm = ActionManagerMiddleware()
        self.request = mock.Mock()
        self.request.session = {}

    def test_process_without_user(self):
        self.request.user = None
        self.assertEqual(self.amm.process_request(self.request), None)
        self.assertTrue(hasattr(self.request, 'action_manager'))
        self.assertFalse(self.request.action_manager.is_valid)

    def test_process_with_anonymous_user(self):
        self.request.user = AnonymousUser()
        self.assertEqual(self.amm.process_request(self.request), None)
        self.assertTrue(hasattr(self.request, 'action_manager'))
        self.assertFalse(self.request.action_manager.is_valid)

    def test_process_with_authenticated_user(self):
        self.request.user = User(username='someusername', email='some@email.com')
        self.request.set_password('p@ss')
        self.request.user.save()
        self.assertEqual(self.amm.process_request(self.request), None)
        self.assertTrue(hasattr(self.request, 'action_manager'))
        self.assertTrue(self.request.action_manager.is_valid)
