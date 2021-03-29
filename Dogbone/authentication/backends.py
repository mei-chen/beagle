from itsdangerous import BadSignature

from django.contrib.auth.models import User
from .models import OneTimeLoginHash, AuthToken


class EmailOrUsernameModelBackend(object):
    """ Authenticate user by username or email """

    def authenticate(self, request, username=None, password=None):
        if '@' in username:
            kwargs = {'email': username.lower()}
        else:
            kwargs = {'username': username}

        try:
            user = User.objects.get(**kwargs)
            if user.check_password(password):
                return user
            else:
                return None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id=None):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class OneTimeLoginHashModelBackend(object):
    """ Authenticate user by GET request hash """

    def authenticate(self, request, login_hash, resolve_after=True):

        try:
            login_secret = OneTimeLoginHash.get_secret(login_hash)
            one_time_hash = OneTimeLoginHash.timeframed.get(secret=login_secret, resolved=False)
            if resolve_after:
                one_time_hash.resolve()

            return one_time_hash.user
        except BadSignature:
            return None
        except OneTimeLoginHash.DoesNotExist:
            return None

    def get_user(self, user_id=None):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class AuthTokenBackend(object):
    """ Authenticate user by token """

    def authenticate(self, request, token=None):
        if token is None:
            return None

        user = AuthToken.find_user(token)

        if user is None:
            return None

        return user

    def get_user(self, user_id=None):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None