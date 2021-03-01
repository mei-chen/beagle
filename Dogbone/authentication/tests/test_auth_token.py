import mock
import hmac
import hashlib
import uuid
import datetime

from freezegun import freeze_time
from base64 import b64encode

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import now

try:
    from user_sessions.utils.tests import Client
    from user_sessions.models import Session
except:
    from django.test.client import Client
    from django.contrib.sessions.models import Session

from authentication.models import AuthToken
from authentication.backends import AuthTokenBackend


class AuthTokenTestCase(TestCase):
    client_class = Client

    def test_creation(self):
        user = User(username='username', email='email@mail.com')
        user.set_password('p@$$')
        user.save()
        # Remove the auto-created
        AuthToken.objects.get(user=user).delete()

        token, created = AuthToken.create_token_model(user)

        self.assertTrue(created)
        self.assertEqual(token.user, user)

        self.assertEqual(b64encode('%s:%s' % (user.pk, token.key)), token.token)
        self.assertIsNotNone(token.key_expire)

    def test_already_created(self):
        user = User(username='username', email='email@mail.com')
        user.set_password('p@$$')
        user.save()

        token1, _ = AuthToken.create_token_model(user)
        token2, created = AuthToken.create_token_model(user)

        self.assertFalse(created)
        self.assertEqual(token2.user, user)
        self.assertEqual(token1, token2)

    def test_proper_key_generation(self):
        with mock.patch('authentication.models.uuid.uuid4') as mock_uuid4:
            mock_uuid4.return_value = uuid.UUID(bytes='1234123412341234', version=4)

            user = User(username='username', email='email@mail.com')
            user.set_password('p@$$')
            user.save()
            token, _ = AuthToken.create_token_model(user)

            expected_key = hmac.new(uuid.UUID(bytes='1234123412341234', version=4).bytes,
                                    digestmod=hashlib.sha1).hexdigest()

            self.assertEqual(token.key, expected_key)

    def test_find_user(self):
        user = User(username='username', email='email@mail.com')
        user.set_password('p@$$')
        user.save()

        token, _ = AuthToken.create_token_model(user)

        u = AuthToken.find_user(token.token)

        self.assertEqual(u, user)

    def test_expire(self):
        user = User(username='username', email='email@mail.com')
        user.set_password('p@$$')
        user.save()

        token, _ = AuthToken.create_token_model(user)

        u = AuthToken.find_user(token.token)

        self.assertEqual(u, user)

        with freeze_time(now() + datetime.timedelta(seconds=AuthToken.DEFAULT_EXPIRE_TIME)):
            u = AuthToken.find_user(token.token)
            self.assertIsNone(u)

            t = AuthToken.objects.get(pk=token.pk)
            self.assertNotEqual(t.key, token.key)


class AuthenticationByTokenTestCase(TestCase):
    client_class = Client

    def test_auth(self):
        user = User(username='username', email='email@mail.com')
        user.set_password('p@$$')
        user.save()

        token, created = AuthToken.create_token_model(user)
        result = self.client.login(token=token.token)
        self.assertTrue(result)

        session = Session.objects.all()[0]
        session_data = session.get_decoded()
        uid = session_data.get('_auth_user_id')
        authenticated_user = User.objects.get(id=uid)

        self.assertEqual(authenticated_user, user)

    def test_regeneration_for_expired(self):
        user = User(username='username', email='email@mail.com')
        user.set_password('p@$$')
        user.save()

        # Since the token has just been created, it should work
        token, created = AuthToken.create_token_model(user)
        result = self.client.login(token=token.token)
        self.assertTrue(result)

        with freeze_time(now() + datetime.timedelta(seconds=AuthToken.DEFAULT_EXPIRE_TIME)):
            # The old token won't work anymore
            result = self.client.login(token=token.token)
            self.assertFalse(result)

            # Get the new token
            t = AuthToken.objects.get(pk=token.pk)

            # The new token should work
            result = self.client.login(token=t.token)
            self.assertTrue(result)

    def test_token_is_none(self):
        user = User(username='username', email='email@mail.com')
        user.set_password('p@$$')
        user.save()

        result = self.client.login(token=None)

        self.assertFalse(result)

    def test_session_when_token_is_none(self):
        user = User(username='username', email='email@mail.com')
        user.set_password('p@$$')
        user.save()

        result = self.client.login(token=None)
        all_sessions = Session.objects.all()
        self.assertEqual(len(all_sessions), 0)

    def test_get_user(self):
        user = User(username='username', email='email@mail.com')
        user.set_password('p@$$')
        user.save()

        backend = AuthTokenBackend()
        self.assertEqual(backend.get_user(user.pk), user)

