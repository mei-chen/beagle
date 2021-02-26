import django.dispatch


# A keyword has been activated
keyword_activated = django.dispatch.Signal(providing_args=["user", "keyword"])

# A keyword has been deactivated
keyword_deactivated = django.dispatch.Signal(providing_args=["user", "keyword"])

# A keyword has been created
keyword_created = django.dispatch.Signal(providing_args=["user", "keyword"])

# A keyword has been deleted
keyword_deleted = django.dispatch.Signal(providing_args=["user", "keyword"])
