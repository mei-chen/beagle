from django.contrib.auth.models import User
from django.db.models import Q


def get_user_by_identifier(identifier):
    # First try to retrieve the user by ID
    try:
        return User.objects.get(pk=int(identifier))
    except (ValueError, User.DoesNotExist):
        pass

    # Try to get it by email or username
    try:
        return User.objects.get(Q(username=identifier) | Q(email__iexact=identifier))
    except User.DoesNotExist:
        return None