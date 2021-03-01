class SubscriptionException(Exception):
    pass


class InvalidSubscriptionException(SubscriptionException):
    pass


class MalformedSubscriptionException(SubscriptionException):
    pass


class ShoppingCartInvalidQuantityException(Exception):
    pass


class ShoppingCartInvalidItemException(Exception):
    pass


class ShoppingCartCurrencyMismatchException(Exception):
    pass


class CouponNotApplicableException(Exception):
    pass


class ActionDoesNotExist(Exception):
    pass