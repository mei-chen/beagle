import uuid
import hmac
import hashlib
import base64
import datetime
from itsdangerous import URLSafeSerializer

from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.conf import settings

from model_utils.models import TimeStampedModel, TimeFramedModel

from .utils import add_salt, remove_salt


class AuthToken(TimeStampedModel):
    """
    Token = base64(user_id:key)
    """

    DEFAULT_EXPIRE_TIME = 60 * 60 * 24 * 30  # 30 days

    user = models.OneToOneField(User, related_name='auth_token', on_delete=models.CASCADE)
    key = models.CharField(max_length=100, db_index=True)
    key_expire = models.DateTimeField(null=True, default=None)

    @classmethod
    def create_token_model(cls, user, expire=True, expire_seconds=None):
        """
        In case the user does not already have a `AuthToken` model associated, create it
        :param user:
        :return: tuple(AuthToken, created) -- created=True/False
        """
        try:
            t_object = AuthToken.objects.get(user_id=user.pk)
            return t_object, False
        except AuthToken.DoesNotExist:
            t_object = AuthToken(user=user)
            t_object._regenerate(expire, expire_seconds)
            return t_object, True

    @classmethod
    def generate_key(cls):
        """
        Generate a unique hashed key
        :return: a hexdigest
        """
        new_uuid = uuid.uuid4()
        return hmac.new(new_uuid.bytes, digestmod=hashlib.sha1).hexdigest()

    @classmethod
    def generate_token(cls, user_id, key):
        """
        Generate token, given the user_id and key
        :param user_id: The pk of the user
        :param key: the key of the token
        :return: the base64 encoded token
        """
        return base64.b64encode("%s:%s" % (user_id, key))

    @classmethod
    def decompose_token(cls, token):
        """
        Decompose the token in user_id and key
        :param token:
        :return: tuple(user_id, key)
        """
        decoded = base64.b64decode(token)
        user_id, key = decoded.split(':')
        return user_id, key

    @classmethod
    def find_user(cls, token):
        """
        Find the user given a token
        A token = base64(user_id:key)
        :param token: base64 encoded string
        :return: django.contrib.auth.models.User|None
        """

        try:
            user_id, key = cls.decompose_token(token)
            user_id = int(user_id)
        except ValueError:
            return None

        try:
            t_object = AuthToken.objects.get(key=key)
        except AuthToken.DoesNotExist:
            return None

        if t_object.user.pk != user_id:
            return None

        if t_object.is_expired:
            t_object._regenerate()
            return None

        return t_object.user

    @property
    def is_expired(self):
        """
        Check if it has expired
        :return: True/False
        """
        if self.key_expire is not None:
            return now() > self.key_expire

        return False

    @property
    def token(self):
        """
        Get the token of the model base64(user_id:key)
        """
        return self.__class__.generate_token(self.user.pk, self.key)

    def make_permanent(self):
        """
        Make the token permanent
        :return:
        """
        self.key_expire = None
        self.save()

    def refresh(self):
        """
        Refresh the token using the DEFAULT_EXPIRE_TIME
        :return:
        """
        self._regenerate()

    def _regenerate(self, expire=True, expire_seconds=None):
        """
        Regenerate the `key` and `key_expire`
        :param expire: If the token should not expire, set this to False
        :param expire_seconds: If the token expires, in how many seconds
        :return:
        """
        if expire_seconds is None:
            expire_seconds = self.__class__.DEFAULT_EXPIRE_TIME

        self.key = self.__class__.generate_key()

        if expire:
            self.key_expire = now() + datetime.timedelta(seconds=expire_seconds)
        else:
            self.key_expire = None

        self.save()


class PasswordResetRequest(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resolved = models.BooleanField(default=False)
    secret = models.CharField(max_length=100)
    email_sent_date = models.DateTimeField(null=True)

    @staticmethod
    def create(email):
        user = User.objects.get(email__iexact=email)
        secret = str(uuid.uuid4())
        password_reset_request = PasswordResetRequest(user=user, secret=secret)
        password_reset_request.save()
        return password_reset_request

    def resolve(self):
        self.resolved = True
        self.save()

    class Meta:
        verbose_name = 'Password Reset Request'
        verbose_name_plural = 'Password Reset Requests'

    def __str__(self):
        return 'Request From: %s on %s ' % (str(self.user), str(self.created))


class OneTimeLoginHash(TimeStampedModel, TimeFramedModel):

    DEFAULT_EXPIRE_TIME = datetime.timedelta(days=3)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resolved = models.BooleanField(default=False)
    secret = models.CharField(max_length=100, unique=True)
    email_sent_date = models.DateTimeField(null=True, blank=True)

    @classmethod
    def create(cls, user):
        secret = str(uuid.uuid4())
        start_time = now()
        login_hash = OneTimeLoginHash.objects.create(user=user, secret=secret,
                                                     start=start_time,
                                                     end=start_time + cls.DEFAULT_EXPIRE_TIME)
        return login_hash

    @staticmethod
    def get_secret(hash):
        serializer = URLSafeSerializer(settings.SECRET_KEY)
        login_secret = remove_salt(serializer.loads(hash))
        return login_secret

    @staticmethod
    def get_onetime_model(hash):
        secret = OneTimeLoginHash.get_secret(hash)
        try:
            return OneTimeLoginHash.objects.get(resolved=False, secret=secret)
        except OneTimeLoginHash.DoesNotExist:
            return None

    def get_hash(self):
        serializer = URLSafeSerializer(settings.SECRET_KEY)
        encoded_secret = serializer.dumps(add_salt(self.secret))
        return encoded_secret

    def resolve(self):
        self.resolved = True
        self.save()

    class Meta:
        verbose_name = 'One Time Login Hash'
        verbose_name_plural = 'One Time Login Hashes'

    def __str__(self):
        return 'One Time Login for: %s created on: %s ' % (str(self.user), str(self.created))
