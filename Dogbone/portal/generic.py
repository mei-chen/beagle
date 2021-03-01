import urllib
import logging
import urlparse
import itsdangerous

from django.shortcuts import render, redirect
from django.views.generic import View
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, resolve
from django.contrib import auth
from django.utils.timezone import now
from django.utils.datastructures import MultiValueDictKeyError

from core.models import ExternalInvite
from itsdangerous import URLSafeSerializer
from marketing.subscriptions import Subscription, InvalidSubscriptionException

from .models import UserProfile
from .tools import random_str, remove_salt
from .tasks import hubspot_submit_form


class RegisterView(View):

    template_name = None
    form_class = None

    def __init__(self, template_name, **kwargs):
        self.template_name = template_name
        super(RegisterView, self).__init__(**kwargs)

    @staticmethod
    def hubspot_fetch_user_data(register_form):
        return {
            'firstname': register_form.user.first_name,
            'lastname': register_form.user.last_name,
            'phone': register_form.user.details.phone,
            'coupon_code': register_form.cleaned_data.get('coupon'),
            'email': register_form.user.email,
            'username': register_form.user.username,
            'lifecyclestage': 'lead',
            'hs_lead_status': 'UNQUALIFIED',
            'blog_default_hubspot_blog_subscription': 'weekly'
        }

    @staticmethod
    def hubspot_fetch_invite_data(external_user, external_invite):
        return {
            'invited_by': external_invite.inviter.email,
            'email': external_user.email,
            'username': external_user.username,
            'lifecyclestage': 'lead',
            'hs_lead_status': 'UNQUALIFIED',
            'blog_default_hubspot_blog_subscription': 'weekly',
        }

    @staticmethod
    def hubspot_submit(request, form_guid, page_name, data):
        if settings.DEBUG is False:
            hubspot_submit_form.delay(form_guid,
                                      hutk=request.COOKIES.get('hubspotutk'),
                                      ip=request.client_ip,
                                      url=request.build_absolute_uri(),
                                      page_name=page_name,
                                      data=data)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('account')

        email = None
        try:
            serializer = URLSafeSerializer(settings.SECRET_KEY)
            email = remove_salt(serializer.loads(request.GET['payload']))

            # If we didn't get an email, swallow the error and act stupid
            if not email:
                logging.error('portal.register: Did not get an email in the payload, got: "%s"', str(email))
                return redirect('login')

            # Make sure the email is lowercase
            email = email.lower()

            # Check if the user already exists
            try:
                existing_user = User.objects.get(email__iexact=email)
                logging.warning('portal.register: an existing user tried to re-register: %s', str(existing_user))
                return redirect('login')
            except User.DoesNotExist:
                pass

            try:
                external_invite = ExternalInvite.objects.filter(email=email).order_by('-created')[0]
            except (ExternalInvite.DoesNotExist, IndexError, ValueError):
                # Act stupid again
                logging.error('portal.register: an email without an ExternalInvite tried to register: %s', str(email))
                return redirect('login')

            # Actually create the user account here
            external_user = User(email=email, username=email)
            external_user.backend = 'django.contrib.auth.backends.ModelBackend'
            external_user.save()

            if not external_user.details:
                UserProfile.objects.get_or_create(user=external_user)

            # TODO: Make this better - set this to now() so that the invited user skips the tour
            external_user.details.initial_tour = now()

            data = self.hubspot_fetch_invite_data(external_user, external_invite)
            self.hubspot_submit(request, settings.HUBSPOT_EXTERNAL_REGISTER_FORM_GUID,
                                'ExternalRegisterForm', data=data)

            # Authenticate the on-the-fly created user
            auth.login(request, external_user)

            from core.tools import sentence_url, document_url
            if external_invite.sentence is None:
                follow_url = request.build_absolute_uri(document_url(external_invite.document))
            else:
                sentence_index = external_invite.sentence.find_index()
                if sentence_index is None:
                    follow_url = request.build_absolute_uri(document_url(external_invite.document))
                else:
                    follow_url = request.build_absolute_uri(sentence_url(external_invite.sentence, sentence_index))

            return redirect(follow_url)

        except (itsdangerous.BadSignature, KeyError, ValueError):
            pass

        initial_data = {}
        if request.GET.get('coupon'):
            initial_data['coupon'] = request.GET['coupon']

        try:
            subscription = Subscription.get_by_uid(request.GET['subscription'])
        except (InvalidSubscriptionException, IndexError, MultiValueDictKeyError):
            subscription = None

        register_form = self.form_class(prepopulated_email=email, initial=initial_data)

        if request.method == 'POST':
            register_form = self.form_class(request.POST, prepopulated_email=email, initial=initial_data)

            # Validate the form and create the user
            if register_form.is_valid():
                data = self.hubspot_fetch_user_data(register_form)

                self.hubspot_submit(request, settings.HUBSPOT_REGISTER_FORM_GUID,
                                    'RegisterForm', data=data)

                # We automatically log the user in, just to make the process easier
                authenticated_user = auth.authenticate(username=register_form.user.email,
                                                       password=register_form.cleaned_data.get('password'))
                auth.login(request, authenticated_user)

                # If the user has to pay, redirect him to the pay page
                if register_form.coupon and not register_form.coupon.is_free:
                    # Small hack to get to override the URL coupon with the one in the form
                    if request.GET.get('next'):
                        parsed_url = urlparse.urlsplit(request.GET['next'])
                        resolved_url = resolve(parsed_url.path)

                        if resolved_url.url_name not in ['purchase_subscription', 'purchase']:
                            return redirect(request.GET['next'])

                        # Override the coupon code in the query params
                        query_params = dict(urlparse.parse_qsl(parsed_url.query))
                        query_params['coupon'] = register_form.coupon.code
                        rebuilt_url = '%s?%s' % (parsed_url.path, urllib.urlencode(query_params.items()))

                        return redirect(rebuilt_url)

                    return redirect(reverse('purchase_subscription', kwargs={
                        'subscription_uid': register_form.coupon.subscription
                    }) + '?coupon=%s' % register_form.coupon.code)

                if request.GET.get('next'):
                    return redirect(request.GET['next'])

                return redirect('dashboard')

        return render(request, self.template_name, {'form': register_form,
                                                    'subscription': subscription})
