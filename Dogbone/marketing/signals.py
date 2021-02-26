import django.dispatch


subscription_purchased = django.dispatch.Signal(providing_args=["user", "purchased_subscription"])
subscription_extended = django.dispatch.Signal(providing_args=["user", "purchased_subscription"])
subscription_expired = django.dispatch.Signal(providing_args=["user", "purchased_subscription"])