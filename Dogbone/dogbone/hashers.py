from django.contrib.auth.hashers import PBKDF2PasswordHasher

class MyPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """
    A subclass of PBKDF2PasswordHasher that uses more iterations.
    """
    iterations = PBKDF2PasswordHasher.iterations + 75000
