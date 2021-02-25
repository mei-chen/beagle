from .utils import get_all_subclasses
from datetime import timedelta

WEEK = timedelta(days=7)
TEN_DAYS = timedelta(days=10)
MONTH = timedelta(days=30)
TWO_MONTHS = timedelta(days=30 * 2 + 1)
THREE_MONTHS = timedelta(days=30 * 3 + 1)
SIX_MONTHS = timedelta(days=30 * 6 + 3)
YEAR = timedelta(days=365)

USD = 'USD'
EUR = 'EUR'
CAN = 'CAN'

# Subscription types
PAID = 'PAID'
ENTERPRISE = 'ENTERPRISE'
FREE = 'FREE'

ALL_SUBSCRIPTIONS = {
    PAID:
        ['YEARLY_PAID_SUBSCRIPTION',
         'MONTHLY_PAID_SUBSCRIPTION'],
    ENTERPRISE:
        ['YEARLY_ENTERPRISE_SUBSCRIPTION',
         'MONTHLY_ENTERPRISE_SUBSCRIPTION']
}

# Amount of private repos allowed for user
SUBSCRIPTION_ALLOWANCES = {
    FREE: 3,
    ALL_SUBSCRIPTIONS[PAID][0]: 20,
    ALL_SUBSCRIPTIONS[PAID][1]: 20,
    ALL_SUBSCRIPTIONS[ENTERPRISE][0]: -1,  # Infinite
    ALL_SUBSCRIPTIONS[ENTERPRISE][1]: -1
}


class InvalidSubscriptionException(Exception):
    pass


class Subscription(object):
    __abstract__ = True

    # Naming
    uid = None
    name = "Abstract Subscription"
    description = "This should not be used as an actual subscription. " \
                  "Please override this class"

    # Financial
    price = 0.0                 # unit price (float | None)
    currency = USD              # Example: 'USD', 'EUR', 'CAN'

    # Time
    duration = None             # None | datetime.timedelta

    def __str__(self):
        return "%s - [%s%s] (%s)" % \
               (self.name, self.currency if self.price else "",
                self.price if self.price else "FREE", self.description)

    def __repr__(self):
        return "<Subscription %s (%s)>" % \
               (self.name, self.description)

    @classmethod
    def all(cls):
        """
        Get all the non-abstract subscriptions
        :return:
        """

        result = [sub for sub in get_all_subclasses(cls) if not sub.__abstract__]
        result.sort(key=lambda x: x.uid)

        return result

    @classmethod
    def all_uids(cls):
        return [s.uid for s in cls.all()]

    @classmethod
    def choices(cls):
        return [(s.uid, s.name) for s in cls.all()]

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


class TrialSubscription(Subscription):
    pass


class PaidSubscription(Subscription):
    pass


class YearlyPaidSubscription(PaidSubscription):
    __abstract__ = False
    uid = ALL_SUBSCRIPTIONS[PAID][0]
    name = "Terry Yearly Paid Subscription"
    description = "The standard paid package (on a year by year basis)"

    duration = YEAR
    price = 20.0 * 12
    currency = USD


class MonthlyPaidSubscription(PaidSubscription):
    __abstract__ = False
    uid = ALL_SUBSCRIPTIONS[PAID][1]
    name = "Terry Monthly Paid Subscription"
    description = "The standard paid package (on a month by month basis)"

    duration = MONTH
    price = 20.0
    currency = USD


class YearlyEnterpriseSubscription(PaidSubscription):
    __abstract__ = False
    uid = ALL_SUBSCRIPTIONS[ENTERPRISE][0]
    name = "Terry Yearly Enterprise Subscription"
    description = "The enterprise package (on a year by year basis)"

    duration = YEAR
    price = 79.0 * 12 * 3
    currency = USD


class MonthlyEnterpriseSubscription(PaidSubscription):
    __abstract__ = False
    uid = ALL_SUBSCRIPTIONS[ENTERPRISE][1]
    name = "Terry Monthly Enterprise Subscription"
    description = "The enterprise package (on a month by month basis)"

    duration = MONTH
    price = 99.0 * 3
    currency = USD


def to_paypal_duration(subscription):
    if subscription.duration == YEAR:
        return 'Y'

    elif subscription.duration == MONTH:
        return 'M'
