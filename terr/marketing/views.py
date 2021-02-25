import logging
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm

from .forms import CouponForm
from .subscriptions import (
    MonthlyPaidSubscription, to_paypal_duration, SUBSCRIPTION_ALLOWANCES,
    ALL_SUBSCRIPTIONS, PAID
)
from .utils import encrypt_str
from .models import PurchasedSubscription, Coupon


@login_required(login_url='/accounts/login/')
def apply_for_subscription(request):

    coupon_code = ''
    if request.method == 'POST':
        coupon_form = CouponForm(request.POST)
        if coupon_form.is_valid():
            coupon_code = coupon_form['coupon_code'].value()
    else:
        coupon_form = CouponForm()

    coupon = Coupon.get_by_code(coupon_code)

    if coupon and coupon.is_available:
        subscription = coupon.get_subscription()
        price = coupon.purchase_price
    else:
        subscription = MonthlyPaidSubscription
        price = subscription.price

    paypal_dict = {
        'cmd': PayPalPaymentsForm.CMD_CHOICES[3][0],
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'sra': PayPalPaymentsForm.REATTEMPT_ON_FAIL_CHOICES[0][0],  # Reattempt billing on failed cc transaction
        'src': PayPalPaymentsForm.RECURRING_PAYMENT_CHOICES[0][0],  # Is billing recurring?
        'a3': str(price),                                           # Subscription Price
        'p3': 1,                                                    # Subscription Duration
        't3': to_paypal_duration(subscription),                     # Duration unit ('M for Month')
        'custom': encrypt_str('%s$%s$%s' %
                              (subscription.uid, request.user.username, coupon_code)),
        'item_name': subscription.name,
        'invoice': uuid.uuid4(),
        'notify_url': request.build_absolute_uri(reverse('paypal-ipn')),
        'return_url': request.build_absolute_uri(reverse('marketing:payment_return')),
        'cancel_return': request.build_absolute_uri(reverse('marketing:payment_cancel'))
    }

    # Remove .0 from price
    if price == int(price):
        price = int(price)

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {
        'form': form,
        'coupon_form': coupon_form,
        'price': '%s/mo' % price,
        'public': 'unlimited',
        'private': SUBSCRIPTION_ALLOWANCES[ALL_SUBSCRIPTIONS[PAID][0]],
        'user': request.user.username
    }

    if coupon:
        context['coupon'] = {
            'title': coupon.title,
            'description': coupon.description
        }

    return render(request, 'marketing/payment.html', context)


@login_required(login_url='/accounts/login/')
@csrf_exempt
def payment_return(request):
    """
    Payment has been successful
    """
    logging.info('The user "%s" arrived on payment_return page' % request.user)
    subscription = PurchasedSubscription.get_user_subscription(request.user)

    return render(request, "marketing/payment_return.html",
                  {'subscription': subscription})


@login_required(login_url='/accounts/login/')
@csrf_exempt
def payment_cancel(request):
    """
    The user canceled the payment
    """
    logging.warning('The user "%s" canceled the payment midway' % request.user)

    return redirect(reverse('portal:index'))
