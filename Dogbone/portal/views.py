import json
import logging
import random
import requests
import string
import urllib
import uuid

from constance import config
from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from itsdangerous import URLSafeSerializer
from paypal.standard.forms import PayPalPaymentsForm

from authentication.models import PasswordResetRequest, OneTimeLoginHash
from core.models import Document, Batch
from core.tasks import send_password_request
from dogbone.actions import has_permission
from dogbone.app_settings.marketing_settings import YearlyPaidSubscription, to_paypal_duration
from integrations.tasks import update_intercom_custom_attribute, log_intercom_custom_event
from marketing.helpers import ShoppingCart
from marketing.models import Coupon, PurchasedSubscription
from marketing.subscriptions import Subscription, InvalidSubscriptionException
from portal.files_processors import FilesUploadProcessor
from portal.models import UserProfile
from portal.services import get_document_parties
from portal.services import get_processed_time
from watcher.services import build_google_auth_flow, save_google_credentials
from .forms import LoginForm, ResetPasswordForm, UpdatePasswordForm, BrowserExtensionRegisterForm
from .tasks import hubspot_submit_form
from .tools import remove_salt, add_salt, encrypt_str


def error400(request, message):
    return render(request, '400.html', {'message': message}, status=400)


def error404(request, exception):
    return render(request, '404.html', status=404)


def error403(request):
    return render(request, '403.html', status=403)


def index(request):
    """ Homepage """
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('account'))
    return render(request, 'index.html', {})


def login(request):
    """ Login form page """
    if request.user.is_authenticated:
        if request.GET.get('next'):
            return HttpResponseRedirect(request.GET['next'])
        else:
            return HttpResponseRedirect(reverse('account'))

    try:
        login_hash = request.GET['hash']
        user = auth.authenticate(login_hash=login_hash, resolve_after=True)
        if user is not None:
            auth.login(request, user)
            if request.GET.get('next'):
                return HttpResponseRedirect(request.GET['next'])
            else:
                return HttpResponseRedirect(reverse('upload_file'))
    except KeyError:
        pass
    except OneTimeLoginHash.DoesNotExist:
        return HttpResponseRedirect(reverse('login'))

    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        # validate the form and authenticate the user
        if login_form.is_valid():
            # login the user
            auth.login(request, login_form.user)
            logging.info('logging in user %s' % str(login_form.user.email))
            if request.GET.get('next'):
                return HttpResponseRedirect(request.GET['next'])
            else:
                return HttpResponseRedirect(reverse('upload_file'))
    else:
        login_form = LoginForm()

    return render(request, 'login.html', {'form': login_form})


def _generate_access_token(service):
    """
    Generates some random access token (valid for using in an external service).
    """

    MIN_TOKEN_VALUE_LENGTH = 50
    MAX_TOKEN_VALUE_LENGTH = 100

    ALPHANUMERIC_CHARSET = (
        string.ascii_lowercase + string.ascii_uppercase + string.digits
    )

    length = random.randint(MIN_TOKEN_VALUE_LENGTH, MAX_TOKEN_VALUE_LENGTH)
    return ''.join(random.choice(ALPHANUMERIC_CHARSET) for _ in range(length))


def _connect(service, user, connect_uri, login_uri):
    """
    Connects a dogbone user to an external service by creating/updating
    the corresponding user for/from that service. Also shares some personal
    access token (from dogbone to the service) and then tries to login
    by authenticating the user in the service via that token.
    """

    SERIALIZER_SECRET_KEY = '/*[dogbone]->(%s)*/' % service

    user_profile = UserProfile.get_or_create_profile(user)

    access_token_attr_name = '%s_access_token' % service

    current_access_token = getattr(user_profile, access_token_attr_name, None)

    access_token = current_access_token
    if access_token is None:
        access_token = _generate_access_token(service)

    input_json = {
        'user': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
        'access_token': access_token,
    }

    response = requests.post(connect_uri, json=input_json)

    redirect_uri = login_uri

    if response.status_code == 200:
        try:
            output_json = response.json()
            access_token = output_json['access_token']
        except:
            pass

        if current_access_token is None:
            setattr(user_profile, access_token_attr_name, access_token)

        serializer = URLSafeSerializer(SERIALIZER_SECRET_KEY)
        access_token = serializer.dumps(access_token)

        redirect_uri += '?access_token=%s' % access_token

    return redirect_uri


_SUPPORTED_SERVICES = frozenset([
    'spot',
    'kibble',
])


def _authorize(service, request):
    """
    Authorizes a user in an external service using dogbone authentication.
    The service must belong to the set of supported services.
    The request must include both connect_uri and login_uri as query string
    parameters.
    """

    if service not in _SUPPORTED_SERVICES:
        message = "Service '%s' is unknown, supported services are %s" % (
            service, sorted(_SUPPORTED_SERVICES)
        )
        return error400(request, message)

    user = request.user
    connect_uri = request.GET.get('connect_uri')
    login_uri = request.GET.get('login_uri')

    if connect_uri is None or login_uri is None:
        message = 'Both connect_uri and login_uri parameters ' \
                  'must be specified in query string'
        return error400(request, message)

    if user.is_authenticated:
        redirect_uri = _connect(service, user, connect_uri, login_uri)
        return HttpResponseRedirect(redirect_uri)

    if request.method == 'POST':
        login_form = LoginForm(request.POST)

        if login_form.is_valid():
            user = login_form.user
            auth.login(request, user)

            redirect_uri = _connect(service, user, connect_uri, login_uri)
            return HttpResponseRedirect(redirect_uri)

    else:
        login_form = LoginForm()

    return render(request, 'login.html', {'form': login_form})


def spot_authorize(request):
    return _authorize('spot', request)


def kibble_authorize(request):
    return _authorize('kibble', request)


def reset_password(request):
    if request.user.is_authenticated:
        if request.GET.get('next'):
            return HttpResponseRedirect(request.GET['next'])
        else:
            return HttpResponseRedirect(reverse('account'))

    success = False

    if request.method == 'POST':
        reset_password_form = ResetPasswordForm(request.POST)

        if reset_password_form.is_valid():
            password_request = PasswordResetRequest.create(reset_password_form.cleaned_data['email'])

            # Create a personalized signup url
            serializer = URLSafeSerializer(settings.SECRET_KEY)
            encoded_secret = serializer.dumps(add_salt(password_request.secret))
            update_email_url = request.build_absolute_uri(reverse('update_password'))
            update_email_url = "%s?payload=%s" % (update_email_url, encoded_secret)

            # Send an email to the external user
            send_password_request.delay(password_request.pk, update_email_url)
            success = True
    else:
        reset_password_form = ResetPasswordForm()

    return render(request, 'reset_password.html', {'form': reset_password_form,
                                                   'success': success})


def update_password(request):
    if request.user.is_authenticated:
        if request.GET.get('next'):
            return HttpResponseRedirect(request.GET['next'])
        else:
            return HttpResponseRedirect(reverse('account'))

    if 'payload' not in request.GET:
        raise Http404()

    serializer = URLSafeSerializer(settings.SECRET_KEY)
    try:
        decoded_secret = remove_salt(serializer.loads(request.GET['payload']))
        reset_request = PasswordResetRequest.objects.get(secret=decoded_secret)

        if reset_request.resolved:
            return HttpResponseRedirect(reverse('reset_password'))

    except:
        # In case the secret is not decodable or the reset request does not exist
        raise Http404()

    if request.method == 'POST':
        update_form = UpdatePasswordForm(request.POST)
        if update_form.is_valid():
            # TODO: Set a message to the session
            reset_request.user.set_password(update_form.cleaned_data['password'])
            reset_request.user.save()

            reset_request.resolve()
            return HttpResponseRedirect(reverse('login'))
    else:
        update_form = UpdatePasswordForm()

    return render(request, 'update_password.html', {'form': update_form})


def register_browser_extension(request):
    """ Register Form page """
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('account'))

    register_form = BrowserExtensionRegisterForm()

    if request.method == 'POST':
        register_form = BrowserExtensionRegisterForm(request.POST)

        # Validate the form and create the user
        if register_form.is_valid():
            if settings.DEBUG is False:
                # Submit this new user to Hubspot (if DEBUG==False)
                hubspot_submit_form.delay(settings.HUBSPOT_REGISTER_FORM_GUID,
                                          hutk=request.COOKIES.get('hubspotutk'),
                                          ip=request.client_ip,
                                          url=request.build_absolute_uri(),
                                          page_name='BrowserExtensionRegisterForm',
                                          data={
                                              'firstname': register_form.user.first_name,
                                              'lastname': register_form.user.last_name,
                                              'phone': register_form.user.details.phone,
                                              'coupon_code': register_form.cleaned_data.get('coupon'),
                                              'email': register_form.user.email,
                                              'username': register_form.user.username,
                                              'lifecyclestage': 'lead',
                                              'hs_lead_status': 'UNQUALIFIED',
                                              'blog_default_hubspot_blog_subscription': 'weekly'
                                          })

            # We automatically log the user in, just to make the process easier
            authenticated_user = auth.authenticate(username=register_form.cleaned_data.get('email'),
                                                   password=register_form.cleaned_data.get('password'))
            auth.login(request, authenticated_user)
            return HttpResponseRedirect(reverse('welcome_browser_extension'))

    return render(request, 'register_browser_extension.html', {'form': register_form})


@login_required(login_url=reverse_lazy('login'))
def welcome_browser_extension(request):
    return render(request, 'welcome_browser_extension.html')


@csrf_exempt
@login_required(login_url=reverse_lazy('login'))
def upload(request):
    allow, _ = has_permission(request, 'app_upload')
    if not allow:
        logging.warning('%s tried to upload without proper subscription' % request.user)
        # TODO: after introducing batches, payload has changed, so change it properly
        return HttpResponse(json.dumps({'document': None}),
                            content_type='application/json',
                            status=403)

    processor = FilesUploadProcessor(
        data=request.POST,
        files=request.FILES,
        user=request.user,
        time_zone=request.session.get('user_time_zone')
    )

    processor.main()
    message = processor.get_endpoint_message()

    status = 302 if message['errors'] else 200

    return HttpResponse(json.dumps(message),
                        content_type='application/json',
                        status=status)


@login_required(login_url=reverse_lazy('login'))
def summary(request, *args, **kwargs):
    batch_id = kwargs.get('id')
    try:
        batch = Batch.objects.get(id=batch_id)
    except KeyError:
        return HttpResponseRedirect(reverse('account'))
    except Batch.DoesNotExist:
        raise Http404()

    if batch.is_trivial:
        if batch.is_empty:
            return error404(request)
        else:
            document = batch.get_documents()[0]
            return redirect('report', uuid=document.uuid)

    for document in batch.get_documents():
        if not document.has_access(request.user):
            return error403(request)

    return render(request, 'summary-report.html', {'id': batch_id})


@login_required(login_url=reverse_lazy('login'))
def summary_details(request, *args, **kwargs):
    batch_id = kwargs['id']
    batch = Batch.objects.get(id=batch_id)

    result = {
        'upload_id': batch.id,
        'upload_title': batch.name,
        'batch_owner': batch.owner.username,
        'docstats': batch.get_batch_docstats()
                    if batch.is_analyzed else '',
        'analyzed': True,
        'documents_count': batch.documents_count,
        'created': str(batch.created),
        'documents': []
    }

    for document in batch.get_documents():
        if not document.processing_end_timestamp:
            result['documents'].append({
                'title': document.title,
                'error': document.error_message,
                'uploaded': '-',
            })
        else:
            company, contractor = get_document_parties(document=document)

            result['documents'].append({
                'title': document.title,
                'type': document.get_agreement_type_display(),
                'error': document.error_message,
                'uploaded': get_processed_time(document),
                'company': company,
                'contractor': contractor,
                'url': '/report/{}'.format(document.uuid)
            })

    return HttpResponse(json.dumps(result), status=200,
                        content_type='application/json')


@login_required(login_url=reverse_lazy('login'))
def google_drive_auth_callback(request):
    code = request.GET.get('code')

    if code:
        flow = build_google_auth_flow(request)
        credentials = flow.step2_exchange(code)
        save_google_credentials(request.user, credentials)

    return HttpResponseRedirect('/account#/settings')


@login_required(login_url=reverse_lazy('login'))
def dropbox_auth_callback(request):
    return render(request, 'dropbox_access.html')


@login_required(login_url=reverse_lazy('login'))
def report(request, *args, **kwargs):
    uuid = kwargs.get('uuid')
    try:
        document = Document.objects.get(uuid=uuid)
    except KeyError:
        return HttpResponseRedirect(reverse('account'))
    except Document.DoesNotExist:
        raise Http404()

    if not document.has_access(request.user):
        return error403(request)

    include_tour = False
    if request.user.details.initial_tour is None:
        request.user.details.initial_tour = now()
        request.user.details.save()
        include_tour = True

    return render(request, 'react-report.html', {'uuid': uuid, 'include_tour': include_tour})


@login_required(login_url=reverse_lazy('login'))
def upload_file(request):
    from core.tools import user_is_paid

    if user_is_paid(request.user):
        return render(request, 'react-upload-file.html', {})
    else:
        # Send the free user to a get started page
        return HttpResponseRedirect(reverse('account'))


@login_required(login_url=reverse_lazy('login'))
def getstarted(request):
    if request.user.is_superuser:
        return render(request, 'react-get-started.html', {})
    else:
        return HttpResponseRedirect(reverse('account'))


def logout(request):
    """ Logout and redirect to homepage """
    if request.user.is_authenticated:
        auth.logout(request)
    return HttpResponseRedirect(reverse('index'))


@login_required(login_url=reverse_lazy('login'))
def dashboard(request):
    return render(request, 'dashboard.html', {})


@login_required(login_url=reverse_lazy('login'))
def account(request):
    context = {
        'DROPBOX_APP_KEY': config.DROPBOX_APP_KEY
    }
    return render(request, 'react-account.html', context)


@login_required(login_url=reverse_lazy('login'))
def redeem_coupon(request):
    coupon_code = request.GET.get('coupon')
    if coupon_code:
        coupon = Coupon.get_by_code(coupon_code)
        if coupon is None:
            messages.error(request, "This is not a valid coupon code, please try again")
        elif not coupon.is_available:
            messages.error(request, "This is coupon has expired, sorry")
        elif coupon.used_by(request.user):
            messages.error(request, "Sorry, you already redeemed this coupon")
        elif not coupon.is_free:
            messages.error(request, "Sorry, this coupon is not redeemable without paying")
        else:
            coupon.create_subscription(request.user, persist=True)
            coupon.add_user_to_group(request.user)
            messages.success(request, "Your coupon has been applied. We added you a \"%s\" subscription" %
                             coupon.get_subscription().name)

    return render(request, "redeem_coupon.html")


@login_required(login_url=reverse_lazy('login'))
def purchase(request, subscription_uid=YearlyPaidSubscription.uid):
    """
    Marketing copy
    - GET add a coupon ?coupon=COUPON_CODE
    - POST send data to PayPal
    """
    # Create the shopping cart for one yearly subscription
    cart = ShoppingCart()

    try:
        subscription = Subscription.get_by_uid(subscription_uid)
    except InvalidSubscriptionException:
        return redirect(reverse('purchase'))

    cart.add(subscription, 1)

    valid_coupon = None

    coupon_code = request.GET.get('coupon')
    if coupon_code:
        coupon = Coupon.get_by_code(coupon_code)
        if coupon is None:
            messages.error(request, "This is not a valid coupon code, please try again")
        elif not coupon.is_available:
            messages.error(request, "This is coupon has expired, sorry")
        elif not cart[0].coupon_applies(coupon):
            messages.error(request, "Sorry, this coupon doesn't apply for our yearly subscription")
        elif coupon.used_by(request.user):
            messages.error(request, "Sorry, you already redeemed this coupon")
        else:
            cart.apply_coupon(coupon)
            valid_coupon = coupon

    cart.save_to_session(request)

    # If everything is free, redirect to success page
    if cart.is_free and valid_coupon:
        valid_coupon.create_subscription(request.user, persist=True)
        valid_coupon.add_user_to_group(request.user)
        return redirect(reverse('payment_return'))

    paypal_dict = {
        "cmd": PayPalPaymentsForm.CMD_CHOICES[3][0],  # `_xclick-subscriptions`
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        # "amount": str(YearlyPaidSubscription.price),
        "sra": PayPalPaymentsForm.REATTEMPT_ON_FAIL_CHOICES[0][0],  # 1
        "src": PayPalPaymentsForm.RECURRING_PAYMENT_CHOICES[0][0],  # 1
        "a3": str(cart.total_price),  # monthly price
        "p3": 1,  # duration of each unit (depends on unit)
        "t3": to_paypal_duration(subscription),  # duration unit ("M for Month")
        "custom": encrypt_str('%s$%s$' % (subscription.uid, request.user.email)),
        "item_name": subscription.name,
        "invoice": uuid.uuid4(),
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return_url": request.build_absolute_uri(reverse('payment_return')),
        "cancel_return": request.build_absolute_uri(reverse('payment_cancel')),
    }

    # Apply a discount if there's a valid coupon
    if valid_coupon is not None:
        # paypal_dict["discount_amount"] = str(YearlyPaidSubscription.price - cart.total_price)
        paypal_dict["custom"] = encrypt_str('%s$%s$%s' % (subscription.uid,
                                                          request.user.email,
                                                          valid_coupon.code))

    paypal_form = PayPalPaymentsForm(initial=paypal_dict)
    return render(request, "purchase.html", {"paypal_form": paypal_form,
                                             "coupon": valid_coupon,
                                             "cart": cart,
                                             "display_subscription": subscription})


@login_required(login_url=reverse_lazy('login'))
def purchase_2mo_limited_edition(request):
    """
    Marketing copy
    - GET add a coupon ?coupon=COUPON_CODE
    - POST send data to PayPal
    """
    # Create the shopping cart for one yearly subscription
    from dogbone.app_settings.marketing_settings import TwoMonthsLimitedEditionPaidSubscription
    cart = ShoppingCart()

    try:
        subscription = Subscription.get_by_uid(TwoMonthsLimitedEditionPaidSubscription.uid)
    except InvalidSubscriptionException:
        return redirect(reverse('purchase'))

    cart.add(subscription, 1)

    valid_coupon = None

    coupon_code = request.GET.get('coupon')
    if coupon_code:
        coupon = Coupon.get_by_code(coupon_code)
        if coupon is None:
            messages.error(request, "This is not a valid coupon code, please try again")
        elif not coupon.is_available:
            messages.error(request, "This is coupon has expired, sorry")
        elif not cart[0].coupon_applies(coupon):
            messages.error(request, "Sorry, this coupon doesn't apply for our yearly subscription")
        elif coupon.used_by(request.user):
            messages.error(request, "Sorry, you already redeemed this coupon")
        else:
            cart.apply_coupon(coupon)
            valid_coupon = coupon

    cart.save_to_session(request)

    # If everything is free, redirect to success page
    if cart.is_free and valid_coupon:
        valid_coupon.create_subscription(request.user, persist=True)
        valid_coupon.add_user_to_group(request.user)
        return redirect(reverse('payment_return'))

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": str(TwoMonthsLimitedEditionPaidSubscription.price),
        "custom": encrypt_str('%s$%s$' % (subscription.uid, request.user.email)),
        "item_name": subscription.name,
        "invoice": uuid.uuid4(),
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return_url": request.build_absolute_uri(reverse('payment_return')),
        "cancel_return": request.build_absolute_uri(reverse('payment_cancel')),
    }

    # Apply a discount if there's a valid coupon
    if valid_coupon is not None:
        paypal_dict["discount_amount"] = str(TwoMonthsLimitedEditionPaidSubscription.price - cart.total_price)
        paypal_dict["custom"] = encrypt_str('%s$%s$%s' % (subscription.uid,
                                                          request.user.email,
                                                          valid_coupon.code))

    paypal_form = PayPalPaymentsForm(initial=paypal_dict)
    return render(request, "purchase_2mo.html", {"paypal_form": paypal_form,
                                                 "coupon": valid_coupon,
                                                 "cart": cart,
                                                 "display_subscription": subscription})


@login_required(login_url=reverse_lazy('login'))
@csrf_exempt
def payment_return(request):
    """
    Payment has been successful
    - Create a subscription and a payment Record
    - Create a CRM notification
    - Set success message [DONE]
    - Get back to your account button
    """

    ShoppingCart.delete_from_session(request)
    logging.info('The user=%s Arrived on payment_return page' % request.user)

    # Log in intercom successful payment
    log_intercom_custom_event(email=request.user.email, event_name="payment-accepted")

    # Log in intercom user is now a paid user
    update_intercom_custom_attribute.delay(email=request.user.email,
                                           attribute_name="Account Type",
                                           attribute_value="Paid")

    # # TODO: Check that the payment was actually successful
    # payment_successful = True
    #
    # if payment_successful:
    #     logging.info('The user=%s purchased a subscription' % request.user)
    #
    #     # TODO: Notify the CRM that the user purchased a Subscription
    #
    #     if len(cart) == 0:
    #
    #         # Just create a Yearly Subscription and investigate ... we don't want anybody angry
    #         logging.error("Something went wrong with a purchase. "
    #                       "The user=%s had 0 items in the shopping cart" % request.user)
    #         from dogbone.app_settings.marketing_settings import YearlyPaidSubscription
    #         item = ShoppingCartItem(YearlyPaidSubscription, 1)
    #     elif len(cart) > 1:
    #         logging.error("Something went wrong with a purchase. "
    #                       "The user=%s has %s items in the shopping cart" % (request.user, len(cart)))
    #         item = cart[0]
    #     else:
    #         item = cart[0]
    #
    #     if item.coupon:
    #         subscription = item.coupon.create_subscription(request.user)
    #     else:
    #         subscription = PurchasedSubscription(buyer=request.user,
    #                                              subscription=item.item.uid)
    #     subscription.save()
    #
    #     payment_record = PaymentRecord(buyer=request.user,
    #                                    redeemed_coupon=subscription.coupon_used,
    #                                    purchased_subscription=subscription,
    #                                    amount=cart.total_price,
    #                                    currency=cart.currency,
    #                                    ip_address=get_client_ip(request),
    #                                    browser=request.META.get('HTTP_USER_AGENT', '__UNKNOWN__'),
    #
    #                                    # TODO: Figure out a way to compute this
    #                                    processing_time=0.0,
    #
    #                                    # TODO: Figure out a way to get this back from PayPal
    #                                    transaction_id='')
    #     payment_record.save()
    #
    #     messages.success(request, "You have successfully bought a Beagle subscription!")
    #
    # else:
    #     pass

    return render(request, "payment_return.html")


@login_required(login_url=reverse_lazy('login'))
@csrf_exempt
def payment_cancel(request):
    """
    The user canceled the payment
    - Log that the user canceled the payment midway [DONE]
    - Set a session message [DONE]
    - Create a CRM notification
    - Redirect to purchase page [DONE]
    """
    ShoppingCart.delete_from_session(request)
    logging.warning('The user=%s canceled the payment midway' % request.user)

    log_intercom_custom_event(email=request.user.email, event_name="payment-canceled")

    messages.error(request, "You have canceled the payment")

    return redirect(reverse('purchase'))


def purchase_route(request):
    from dogbone.app_settings.marketing_settings import PaidSubscription, TrialSubscription, AllAccessTrial
    from marketing.subscriptions import Subscription
    from core.tools import user_had_trial

    coupon = request.GET.get('coupon', None)
    subscription_uid = request.GET.get('subscription', None)
    try:
        subscription = Subscription.get_by_uid(subscription_uid)
    except InvalidSubscriptionException:
        subscription = None

    # Add the desired subscription and the coupon to the url and redirect to purchase page
    if subscription:
        redirect_url = reverse('purchase_subscription', kwargs={'subscription_uid': subscription_uid})
        if coupon:
            redirect_url += '?coupon=%s' % coupon
    else:
        if coupon:
            try:
                coupon_model = Coupon.objects.get(code=coupon)
                redirect_url = reverse('purchase_subscription',
                                       kwargs={
                                           'subscription_uid': coupon_model.get_subscription().uid}) + '?coupon=%s' % coupon
            except Coupon.DoesNotExist:
                redirect_url = reverse('purchase')
        else:
            redirect_url = reverse('purchase')

    if request.user.is_authenticated:
        # If the user is authenticated and is already a paid user
        current_subscriptions = PurchasedSubscription.get_current_subscriptions(request.user)
        if any([PaidSubscription.includes(subscription.get_subscription()) for subscription in current_subscriptions]):
            return redirect(reverse('dashboard'))

        # If the user is authenticated but it is not paid
        if TrialSubscription.includes(subscription):
            # If the user `didn't` already had a trial
            if not user_had_trial(request.user):
                PurchasedSubscription.purchase_subscription(request.user, AllAccessTrial)
            return redirect(reverse('dashboard'))

        # Just redirect to the purchase url
        return redirect(redirect_url)

    kwargs = {'next': redirect_url}
    if coupon:
        kwargs['coupon'] = coupon

    if subscription:
        kwargs['subscription'] = subscription_uid

    return redirect(reverse('signup') + '?%s' % urllib.parse.urlencode(kwargs))
