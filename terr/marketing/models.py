from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.contrib.humanize.templatetags import humanize
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .subscriptions import Subscription, ALL_SUBSCRIPTIONS, ENTERPRISE


class Coupon(models.Model):
    title = models.CharField('Title', max_length=200)
    code = models.CharField('Promo Code', unique=True, max_length=100)
    subscription = models.CharField('Subscription', max_length=200,
                                    choices=Subscription.choices())
    description = models.TextField('Coupon description', null=True, blank=True)

    # Benefits
    free = models.BooleanField('Make it FREE?', default=False)
    special_price = models.FloatField('Special Price', null=True, default=None, blank=True)
    discount_percent = models.FloatField('Discount(Percent)', null=True, default=None, blank=True,
                                         validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    discount_units = models.FloatField('Discount(Units)', null=True, default=None, blank=True)

    max_use_count = models.IntegerField('How many times the coupon can be used', null=True, default=None, blank=True,
                                        validators=[MinValueValidator(1)],
                                        help_text="Leave blank if no such restriction is desired")
    use_count = models.IntegerField("How many times the coupon has been used", default=0)
    start_date = models.DateTimeField("Coupon available from this date", null=True, blank=True,
                                      help_text="Optional")
    end_date = models.DateTimeField("Coupon available until this date", null=True, blank=True,
                                    help_text="Optional")

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

        if self.end_date and timezone.now() > self.end_date:
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

        if self.start_date and self.start_date > timezone.now():
            return False

        if self.is_expired:
            return False

        return True

    @property
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
        elif self.special_price or self.special_price == 0:
            return self.special_price
        elif self.discount_percent:
            return round(
                (1 - self.discount_percent / 100.0) * subscription.price, 2
            )
        elif self.discount_units:
            new_price = subscription.price - self.discount_units
            if new_price < 0.0:
                new_price = 0.0
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

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super(Coupon, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.code


class PurchasedSubscription(models.Model):
    buyer = models.ForeignKey(User, help_text="The user that bought something")
    subscription = models.CharField('Subscription', max_length=200,
                                    choices=Subscription.choices(),
                                    help_text="The subscription package")
    expiration_date = models.DateTimeField()
    coupon_used = models.ForeignKey(Coupon, null=True, blank=True,
                                    help_text="The coupon the user used to get this subscription")

    @property
    def expired(self):
        """
        Is the subscription expired?
        :return: True|False
        """

        return timezone.now() > self.expiration_date

    @staticmethod
    def get_user_subscription(user):
        """
        Returns the best subscription available for user.
        :return: PurchasedSubscription or None
        """

        subscriptions = PurchasedSubscription.objects.filter(buyer=user)
        best_subscription = None

        for subscription in subscriptions:
            if not subscription.expired:
                if subscription.subscription in ALL_SUBSCRIPTIONS[ENTERPRISE]:
                    return subscription
                else:
                    best_subscription = subscription

        return best_subscription

    def __unicode__(self):
        return '%s: %s. Until %s' % (
            self.subscription,
            self.buyer,
            humanize.naturalday(self.expiration_date)
        )
