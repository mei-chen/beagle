from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect

from allauth.account.views import LoginView
from allauth.socialaccount.views import SignupView


class LoginViewCustom(LoginView):
    def get(self, request, *args, **kwargs):
        if request.GET:
            if request.GET.get('git_url'):
                request.session['git_url'] = request.GET['git_url']
            if request.GET.get('next'):
                request.session['redirect_uri'] = request.GET['next']

        return super(LoginViewCustom, self).get(request, *args, **kwargs)


class SignupViewCustom(SignupView):
    """
    Override allauth view to automatically merge accounts of different social providers
    """
    def dispatch(self, request, *args, **kwargs):
        data = request.session.get('socialaccount_sociallogin')
        email = None
        for email_data in data['email_addresses']:
            if email_data['primary']:
                email = email_data['email']
                break

        user = User.objects.get(email=email)
        user.backend = settings.AUTHENTICATION_BACKENDS[1]  # allauth backend
        login(request, user)

        connect_url = request.build_absolute_uri(
            '/accounts/%s/login/?process=connect' % data['account']['provider']
        )

        return redirect(connect_url)
