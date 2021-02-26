from datetime import timedelta
from marketing.subscriptions import Subscription
from marketing.currencies import Currency


WEEK = timedelta(days=7)
TEN_DAYS = timedelta(days=10)
MONTH = timedelta(days=30)
TWO_MONTHS = timedelta(days=30 * 2 + 1)
THREE_MONTHS = timedelta(days=30 * 3 + 1)
SIX_MONTHS = timedelta(days=30 * 6 + 3)
YEAR = timedelta(days=365)


class WebApplicationSubscription(Subscription):
    __abstract__ = True


class BrowserExtensionSubscription(Subscription):
    __abstract__ = True


class TrialSubscription(WebApplicationSubscription):
    __abstract__ = True


class PaidSubscription(WebApplicationSubscription):
    __abstract__ = True


class AllAccessTrial(TrialSubscription):
    __abstract__ = False
    uid = "ALL_ACCESS_TRIAL"
    name = "Beagle 7day Trial"
    description = "Trial accessible to everyone - 7days of Beagle, free"

    duration = WEEK
    price = None


class ExtendedAllAccessTrial(TrialSubscription):
    __abstract__ = False
    uid = "EXTENDED_ALL_ACCESS_TRIAL"
    name = "Beagle 10day Trial"
    description = "Trial accessible to everyone, if they talk to an official Beagle"

    duration = TEN_DAYS
    price = None


class TwoWeekAllAccessTrial(TrialSubscription):
    __abstract__ = False
    uid = "TWO_WEEK_ALL_ACCESS_TRIAL"
    name = "Beagle 2week Trial"
    description = "Trial accessible to everyone, if they talk to an official Beagle"

    duration = 2 * WEEK
    price = None


class StandardTrial(TrialSubscription):
    __abstract__ = False
    uid = "STANDARD_TRIAL"
    name = "Beagle Standard Trial"
    description = "Default 30 day trial"

    duration = MONTH
    price = None


class ThreeMonthsTrial(TrialSubscription):
    __abstract__ = False
    uid = "3MO_STANDARD_TRIAL"
    name = "Beagle 3 months Standard Trial"
    description = "3 months trial"

    duration = THREE_MONTHS
    price = None


class SixMonthsTrial(TrialSubscription):
    __abstract__ = False
    uid = "6MO_STANDARD_TRIAL"
    name = "Beagle 6 months Standard Trial"
    description = "6 months trial"

    duration = SIX_MONTHS
    price = None


class YearlyPaidSubscription(PaidSubscription):
    __abstract__ = False
    uid = "YEARLY_PAID_SUBSCRIPTION"
    name = "Beagle Yearly Paid Subscription"
    description = "The standard paid package (on a year by year basis)"

    duration = YEAR
    price = 4000.0
    currency = Currency.USD


class MonthlyPaidSubscription(PaidSubscription):
    __abstract__ = False
    uid = "MONTHLY_PAID_SUBSCRIPTION"
    name = "Beagle Monthly Paid Subscription"
    description = "The standard paid package (on a month by month basis)"

    duration = MONTH
    price = 380.0
    currency = Currency.USD


class TwoMonthsLimitedEditionPaidSubscription(PaidSubscription):
    __abstract__ = False
    uid = "TWO_MONTHS_LIMITED_EDITION_SUBSCRIPTION"
    name = "Beagle 2 Months Subscription [LIMITED EDITION]"
    description = "2 Mo for $75 ... It's a steal!"

    duration = TWO_MONTHS
    price = 75.0
    currency = Currency.USD


class PremiumYearlyPaidSubscription(PaidSubscription):
    __abstract__ = False
    uid = "PREMIUM_YEARLY_PAID_SUBSCRIPTION"
    name = "Premium Beagle Yearly Paid Subscription"
    description = "The premium paid package (on a year by year basis)"

    duration = YEAR
    price = 125.0 * 12
    currency = Currency.USD


class PremiumMonthlyPaidSubscription(PaidSubscription):
    __abstract__ = False
    uid = "PREMIUM_MONTHLY_PAID_SUBSCRIPTION"
    name = "Premium Beagle Monthly Paid Subscription"
    description = "The premium paid package (on a month by month basis)"

    duration = MONTH
    price = 150.0
    currency = Currency.USD


class UnlimitedBrowserExtensionSubscription(BrowserExtensionSubscription):
    __abstract__ = False
    uid = "UNLIMITED_BROWSER_EXTENSION_SUBSCRIPTION"
    name = "Beagle Unlimited Browser Free Subscription"
    description = "Giving the Beagle extension for free"


def to_paypal_duration(subscription):
    if subscription.duration == YEAR:
        return 'Y'

    if subscription.duration == MONTH:
        return 'M'

    return 'Y'
