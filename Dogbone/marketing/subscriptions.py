from .currencies import Currency
from .exceptions import InvalidSubscriptionException
from .tools import get_all_subclasses


class MetaSubscription(type):
    def __str__(self):
        return "%s - [%s%s] (%s)" % \
               (self.name, self.currency if self.price else "",
                self.price if self.price else "FREE", self.description)

    def __repr__(self):
        return "<Subscription %s (%s)>" % \
               (self.name, self.description)


class Subscription:

    def __init__(self):
        pass

    __metaclass__ = MetaSubscription
    __abstract__ = True

    # Naming
    uid = None
    name = "Abstract Subscription"
    description = "This should not be used as an actual subscription. " \
                  "Please override this class"

    # Financial
    price = 0.0                 # unit price (float | None)
    currency = Currency.USD     # Example: 'USD', 'EUR', 'CAN'

    # Time
    duration = None             # None | datetime.timedelta

    @classmethod
    def all(cls):
        """
        Get all the non-abstract subscriptions
        :return:
        """
        return [sub for sub in get_all_subclasses(cls) if not sub.__abstract__]

    @classmethod
    def all_uids(cls):
        return [s.uid for s in cls.all()]

    @classmethod
    def choices(cls):
        return [(s.uid, str(s)) for s in cls.all()]

    @classmethod
    def get_by_name(cls, name):
        candidates = [klass for klass in cls.all() if klass.name == name]

        if len(candidates) != 1:
            raise InvalidSubscriptionException("Invalid subscription name")

        return candidates[0]

    @classmethod
    def get_by_uid(cls, uid):
        candidates = [klass for klass in cls.all() if klass.uid == uid]

        if len(candidates) != 1:
            raise InvalidSubscriptionException("Invalid subscription uid")

        return candidates[0]

    @classmethod
    def includes(cls, subscription):
        """
        Check if `subscription` is a kind of the the current `Subscription`
        - useful for situations like: is this a trial subscription or is it a paid one?
        :param subscription: a subclass of `Subscription` class
        :return: True/False
        """
        return subscription in cls.all()
