from portal.tools import encrypt_str, decrypt_str
from dogbone.testing.base import BeagleWebTest


class EncryptionTest(BeagleWebTest):
    def test_encrypt(self):
        to_encrypt = 'thisisasecret'
        encrypted = encrypt_str(to_encrypt)
        self.assertIsNotNone(encrypted)
        decrypted = decrypt_str(encrypted)
        self.assertEqual(to_encrypt, decrypted)
