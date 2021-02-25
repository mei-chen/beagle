import logging

from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils import timezone
from paypal.standard.ipn.signals import (
    valid_ipn_received, invalid_ipn_received, payment_was_flagged)
from paypal.standard.models import ST_PP_COMPLETED

from marketing.utils import decrypt_str
from marketing.models import PurchasedSubscription, Coupon
from marketing.subscriptions import Subscription, InvalidSubscriptionException


@receiver(valid_ipn_received)
def handle_successful_transaction(sender, **kwargs):
    logging.info('Arrived at handle_successful_transaction')
    if sender.payment_status == ST_PP_COMPLETED:
        logging.info('handle_successful_transaction: Payment status completed')

        uid, username, coupon_code = decrypt_str(sender.custom).split('$')
        logging.info(
            'handle_successful_transaction: uid=%s, username=%s, coupon=%s' %
            (uid, username, coupon_code)
        )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logging.error('Received payment confirmation for an invalid username=%s' % username)
            return

        try:
            subscription = Subscription.get_by_uid(uid)
        except InvalidSubscriptionException:
            logging.error('Received payment confirmation for an invalid subscription uid=%s' % uid)
            return

        expiration_date = subscription.duration + timezone.now()

        purchased_subscription = PurchasedSubscription(
            buyer=user,
            subscription=uid,
            expiration_date=expiration_date
        )

        if coupon_code:
            coupon = Coupon.get_by_code(coupon_code)
            if coupon:
                coupon.use_count += 1
                coupon.save()
                purchased_subscription.coupon_used = coupon
            else:
                logging.error('Received payment confirmation with invalid coupon code=%s' % coupon_code)

        purchased_subscription.save()


@receiver(invalid_ipn_received)
def handle_failed_transaction(sender, **kwargs):
    logging.error('Arrived handle_failed_transaction, please check payment')


@receiver(payment_was_flagged)
def handle_payment_was_flagged(sender, **kwargs):
    try:
        logging.error("PayPal transaction was flagged with: flag=%s" % sender.flag_info)
    except Exception as e:
        logging.error('Exception in handle_payment_was_flagged exc=%s', str(e))
