import logging
import pytz
import re
import requests

from django_mobile.middleware import MobileDetectionMiddleware
from django_mobile import set_flavour
from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)


class ExtendedMobileDetectionMiddleware(MobileDetectionMiddleware):
    # Example from django-mobile package

    user_agents_android_search = u"(?:android)"
    user_agents_mobile_search = u"(?:mobile)"
    user_agents_tablets_search = u"(?:%s)" % u'|'.join(('ipad', 'tablet', ))

    def __init__(self):
        super(ExtendedMobileDetectionMiddleware, self).__init__()
        self.user_agents_android_search_regex = re.compile(self.user_agents_android_search,
                                                           re.IGNORECASE)
        self.user_agents_mobile_search_regex = re.compile(self.user_agents_mobile_search,
                                                          re.IGNORECASE)
        self.user_agents_tablets_search_regex = re.compile(self.user_agents_tablets_search,
                                                           re.IGNORECASE)

    def process_request(self, request):
        is_tablet = False

        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent:
            # Ipad or Blackberry
            if self.user_agents_tablets_search_regex.search(user_agent):
                is_tablet = True
            # Android-device. If User-Agent doesn't contain Mobile, then it's a tablet
            elif (self.user_agents_android_search_regex.search(user_agent) and
                  not self.user_agents_mobile_search_regex.search(user_agent)):
                is_tablet = True
            else:
                # otherwise, let the superclass make decision
                super(ExtendedMobileDetectionMiddleware, self).process_request(request)

        # set tablet flavour. It can be `mobile`, `tablet` or anything you want
        if is_tablet:
            set_flavour(settings.FLAVOURS[2], request)


class UserCookieMiddleware(object):

    def process_response(self, request, response):
        if hasattr(request, 'user'):
            if request.user.is_authenticated() and not request.COOKIES.get('user'):
                response.set_cookie('user', request.user.email)
            elif request.COOKIES.get('user') and not request.user.is_authenticated():
                response.delete_cookie('user')
        return response


class UserTimezoneMiddleware(object):

    LOCALHOST_IP = '127.0.0.1'
    FREEGEOIP_URL = 'http://freegeoip.net/json/%s'

    def process_request(self, request):
        user_ip = request.client_ip

        # Tweak for requests from localhost during development and testing
        # (otherwise responses will be empty)
        if user_ip == self.LOCALHOST_IP:
            user_ip = ''

        user_time_zone = request.session.get('user_time_zone')

        if not user_time_zone:
            try:
                response = requests.get(self.FREEGEOIP_URL % user_ip)
                response_json = response.json()
                user_time_zone = response_json['time_zone']
                # If valid time zone was detected, cache it in current session
                timezone.activate(pytz.timezone(user_time_zone))
                logger.info(u'Setting user_time_zone=%s for user=%s',
                            user_time_zone, request.user)
                request.session['user_time_zone'] = user_time_zone
            except:
                timezone.deactivate()
        else:
            timezone.activate(pytz.timezone(user_time_zone))
