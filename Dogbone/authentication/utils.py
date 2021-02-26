import random
import string

from itsdangerous import URLSafeSerializer
from django.conf import settings


def random_str(length=8):
    """
    Generate a random string. Used generally for setting default passwords and salts
    :param length: the length of the string
    :return: the random string
    """
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))


def add_salt(payload):
    """
    Add salt to a string
    Example: 'some@email.com' => 'some@email.com||vjsnf43'
    :param payload:
    :return: salted payload
    """
    return payload + '||' + random_str(8)


def remove_salt(salted_payload):
    """
    Remove salt from payload
    Example: 'some@email.com||vjsnf43' => 'some@email.com'
    :param salted_payload:
    :return: unsalted payload
    """
    if not salted_payload:
        return ''
    chunks = salted_payload.split('||')
    return chunks[0]


def encrypt_str(payload):
    """
    Use an URLSafeSerializer and salt the payload
    :param payload:
    :return: encrypted
    """

    serializer = URLSafeSerializer(settings.SECRET_KEY)
    return serializer.dumps(add_salt(payload))


def decrypt_str(payload):
    """
    Use and URLSafeSerializer to decrypt the payload
    :param payload:
    :return: decrypted
    """

    serializer = URLSafeSerializer(settings.SECRET_KEY)
    return remove_salt(serializer.loads(payload))