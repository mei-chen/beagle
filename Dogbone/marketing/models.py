import datetime
import logging

from django.db import models
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User, Group
from model_utils.models import TimeStampedModel, TimeFramedModel

from .subscriptions import Subscription
from .currencies import Currency
from .helpers import price_f
from .signals import subscription_extended, subscription_purchased, subscription_expired


class Coupon(TimeStampedModel, TimeFramedModel):
    title = models.CharField('Title', max_length=200)
    code = models.CharField('Promo Code', unique=True, max_length=100)
    subscription = models.CharField('Subscription', max_length=200,
                                    choices=Subscription.choices())
    notes = models.TextField('Notes', null=True, blank=True,
                             help_text="Stuff you should remember about this coupon")

    # Benefits
    free = models.BooleanField('Make it FREE?', default=False,
                               help_text="Makes the subscription FREE")
    special_price = models.FloatField('Special Price', null=True, default=None, blank=True,
                                      help_text="A special price to a given subscription "
                                                "(in the currency of the subscription)")
    discount_percent = models.FloatField('Discount(Percent)', null=True, default=None, blank=True,
                                         validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
                                         help_text="A discount (in percents) to a given subscription")
    discount_units = models.FloatField('Discount(Units)', null=True, default=None, blank=True,
                                       help_text="A discount (in units) to a given subscription")

    max_use_count = models.IntegerField('How many times the coupon can be used', null=True, default=None, blank=True,
                                        validators=[MinValueValidator(1)],
                                        help_text="Leave blank if no such restriction is desired")
    use_count = models.IntegerField("How many times the coupon has been used", default=0,
                                    help_text="Helpful tracker of the popularity of coupons")

    @staticmethod
    def get_by_code(code):
        """
        Get the coupon model or None
        :param code: The coupon code
        :return: Coupon model
        """
        try:
            return Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return None

    @property
    def is_expired(self):
        """
        Is the coupon expired?
        :return: True|False
        """
        if self.end and datetime.date.today() > self.end.date():
            return True
        if self.max_use_count and self.use_count >= self.max_use_count:
            return True
        return False

    @property
    def is_available(self):
        """
        Is the coupon available at the moment
        :return: True|False
        """
        if self.start and self.start.date() > datetime.date.today():
            return False

        if self.is_expired:
            return False

        return True

    @property
    @method_decorator(price_f)
    def purchase_price(self):
        """
        Compute the subscriptions new price
        :return: the new price (float)
        """
        if self.free:
            return 0.0

        subscription = self.get_subscription()

        if not subscription.price:
            return 0.0

        if self.special_price:
            return self.special_price

        if self.discount_percent:
            return (1 - self.discount_percent / 100.0) * subscription.price

        if self.discount_units:
            new_price = subscription.price - self.discount_units
            if new_price < 0.0:
                return 0.0

            return new_price

        return subscription.price

    @property
    def is_free(self):
        """
        Is the coupon activation free?
        :return: True/False
        """
        return self.purchase_price == 0.0 or self.free

    def get_subscription(self):
        return Subscription.get_by_uid(self.subscription)

    def create_subscription(self, user, persist=True):
        """
        Create the a `PurchasedSubscription` (the coupon's attached one) for the user
        Note: the subscription starts `now` and ends when it's specified in the `Subscription` object
        :param user: the user to create the subscription for
        :return: the created `PurchasedSubscription`
        """
        purchased = PurchasedSubscription(buyer=user,
                                          coupon_used=self,
                                          subscription=self.subscription)
        if persist:
            purchased.save()

        self.use_count += 1
        self.save()

        return purchased

    def add_user_to_group(self, user):
        """
        Add the user to the group containing all users that used the coupon
        :param user: The `django.contrib.auth.models.User` object we want to add
        :return: the coupon group
        """
        coupon_group, _ = Group.objects.get_or_create(name=self.code + '_COUPON')
        coupon_group.user_set.add(user)
        coupon_group.save()

        return coupon_group

    def used_by(self, user):
        return PurchasedSubscription.objects.filter(buyer=user, coupon_used=self).exists()

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super(Coupon, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.code


class PurchasedSubscription(TimeStampedModel, TimeFramedModel):
    buyer = models.ForeignKey(User, help_text="The user that bought something")
    subscription = models.CharField('Subscription', max_length=200,
                                    choices=Subscription.choices(),
                                    help_text="The subscription package")
    coupon_used = models.ForeignKey(Coupon, null=True, blank=True,
                                    help_text="The coupon the user used to get this subscription")

    expired = models.BooleanField('Is expired', default=False)
    expire_info_emailed = models.DateTimeField('About to expire email DateTime', blank=True, null=True,
                                               help_text="Email informing that the subscription is about to expire")
    expire_warning_emailed = models.DateTimeField('Expired email DateTime', blank=True, null=True,
                                                  help_text="Email warning that the subscription has expired")

    @staticmethod
    def get_current_subscriptions(user):
        """
        Get all the current active subscription for the user
        :param user: a `User` model
        :return: the list of `PurchaseSubscription` models
        """
        subscriptions = PurchasedSubscription.timeframed.filter(buyer=user)
        if not subscriptions:
            return []

        return subscriptions

    @classmethod
    def get_first_current_subscription(cls, user):
        """
        Get the current active subscription for the user
        :param user: a `User` model
        :return: the `PurchaseSubscription` model or `None`
        """
        subscriptions = cls.get_current_subscriptions(user)
        if not subscriptions:
            return None
        if len(subscriptions) > 1:
            logging.warning("The user=%s has multiple active subscriptions" % user)

        return subscriptions[0]

    @classmethod
    def has_active_subscription(cls, user):
        """
        Check if a user has at least one active subscription

        :param user: a `User` model

        :return: True/False
        """
        subscription = cls.get_first_current_subscription(user)
        if not subscription:
            return False

        return True

    @classmethod
    def earliest_subscription_start(cls, user, subscription_class=Subscription):
        """
        Get the earliest time for the next subscription can start

        :param user: Django `User` model
        :param subscription_class: Filter the subscriptions. Get only subclasses of `subscription_class`

        :return: return datetime
        """

        if not cls.has_active_subscription(user):
            return timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Get all the user's subscriptions that have an end date
        subscriptions = PurchasedSubscription.objects.filter(buyer=user, end__isnull=False).order_by('-end')

        # Get all the subscriptions that are a subclass of the Subscription class
        subscriptions = [s for s in subscriptions if subscription_class.includes(s.get_subscription())]

        # if there are no subscriptions within that class, return now
        if not subscriptions:
            return timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        return subscriptions[0].end.replace(hour=0, minute=0, second=0, microsecond=0)


    @classmethod
    def purchase_subscription(cls, user, subscription, coupon=None, subscription_class=Subscription):
        """
        Attach a subscription to the user using a coupon (optional)
        :param user: a `User` model
        :param subscription: `Subscription` type
        :param coupon: `Coupon` model
        :param subscription_class: the subscription filtering superclass
        :return: the created `PurchasedSubscription`
        """
        if coupon:
            purchased_subscription = coupon.create_subscription(user, persist=False)
        else:
            purchased_subscription = PurchasedSubscription(buyer=user, subscription=subscription.uid)

        purchased_subscription.start = PurchasedSubscription.earliest_subscription_start(
            user, subscription_class=subscription_class)

        purchased_subscription.save()

        # Send the `subscription_purchased` signal
        subscription_purchased.send(sender=cls, user=user, purchased_subscription=purchased_subscription)

        return purchased_subscription

    def save(self, *args, **kwargs):
        if self.pk is None:
            subscription = self.get_subscription()
            if self.start is None:
                self.start = PurchasedSubscription.earliest_subscription_start(self.buyer)

            if subscription.duration is not None and self.end is None:
                self.end = self.start + subscription.duration

        super(PurchasedSubscription, self).save(*args, **kwargs)

    @property
    def is_active(self):
        """
        Check if the subscription is active right now
        :return: True/False
        """
        now = timezone.now()
        return (self.start is None or self.start <= now) and (self.end is None or self.end >= now)

    @property
    def is_expired(self):
        """
        Is the subscription expired?
        :return: True|False
        """
        if self.expired:
            return True

        if self.end and datetime.date.today() > self.end.date():
            return True

        return False

    @property
    @method_decorator(price_f)
    def purchase_price(self):
        """
        Compute the subscriptions price
        :return: the new price (float)
        """
        if self.coupon_used:
            return self.coupon_used.purchase_price

        return self.get_subscription().price

    def get_subscription(self):
        return Subscription.get_by_uid(self.subscription)

    def extend(self, days, persist=True):
        """
        Extend the subscription by a number of days
        :param days: the number of days to extend the subscription by
        :param persist: persist or not the model?
        :return:
        """
        self.end += datetime.timedelta(days=days)
        if persist:
            self.save()

        # Send the `subscription_extended` signal
        subscription_extended.send(sender=self.__class__, user=self.buyer, purchased_subscription=self)

    def mark(self, informed=False, warned=False, persist=True):
        """
        Use when warning emails are sent
        :param informed: if the info email has been sent
        :param warned: if the warning email has been sent
        :param persist: persist or not the model
        :return:
        """
        self.expire_info_emailed = informed
        self.expire_warning_emailed = warned

        if persist:
            self.save()

    def mark_expired(self, persist=True):
        """
        Mark the `PurchasedSubscription` as expired, sending the appropriate signal
        :param persist: persist the model or not
        """
        self.expired = True
        if persist:
            self.save()

        # Send the `subscription_expired` signal
        subscription_expired.send(self.__class__, user=self.buyer, purchased_subscription=self)

    def to_dict(self):
        subscription = self.get_subscription()
        return {
            'buyer': {
                'email': self.buyer.email,
                'id': self.buyer.pk,
                'username': self.buyer.username,
                'first_name': self.buyer.first_name,
                'last_name': self.buyer.last_name,
            },
            'id': self.pk,
            'coupon': None if self.coupon_used is None else self.coupon_used.code,
            'start': str(self.start),
            'start_tz': str(self.start.tzinfo) if self.start and self.start.tzinfo else None,
            'end': str(self.end) if self.end else None,
            'end_tz': str(self.end.tzinfo) if self.end and self.end.tzinfo else None,
            'days_remaining': (self.end - timezone.now()).days if self.end else None,
            'display_days_remaining': (self.end - timezone.now()).days + 1 if self.end else None,
            'expire_info_emailed': str(self.expire_info_emailed) if self.expire_info_emailed else None,
            'expire_warning_emailed': str(self.expire_warning_emailed) if self.expire_warning_emailed else None,
            'subscription': {
                'uid': subscription.uid,
                'name': subscription.name,
                'description': subscription.description,
                'price': subscription.price
            }
        }

    def __unicode__(self):
        return unicode(self.buyer) + ' - ' + unicode(self.get_subscription())


class PaymentRecord(TimeStampedModel):
    buyer = models.ForeignKey(User, help_text="The user that bought something")
    redeemed_coupon = models.ForeignKey(Coupon, null=True,
                                        help_text="In case the user redeemed a coupon")
    purchased_subscription = models.ForeignKey(PurchasedSubscription,
                                               help_text="What the user bought")
    amount = models.FloatField('Paid Amount')
    currency = models.TextField('Currency', choices=zip(Currency.ALL, Currency.ALL))
    ip_address = models.IPAddressField('Address', null=True)
    browser = models.TextField('Browser', null=True)
    processing_time = models.FloatField('Processing Time in seconds', null=True)

    transaction_id = models.TextField('3rd Party Transaction ID', max_length=200, null=True)

    @classmethod
    def create_record(cls, user, purchased_subscription, amount, currency, txn_id):
        payment_record = PaymentRecord(buyer=user,
                                       redeemed_coupon=purchased_subscription.coupon_used,
                                       purchased_subscription=purchased_subscription,
                                       amount=amount,
                                       currency=currency,
                                       transaction_id=txn_id)
        payment_record.save()
        return payment_record

    def get_subscription(self):
        return Subscription.get_by_uid(self.purchased_subscription.subscription)

