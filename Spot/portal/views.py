from allauth.account.views import SignupView
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView

from core.utils import user_to_dict
from portal.forms import ExtendedSignupForm


@login_required(login_url='/accounts/login/')
def index(request):
    context = {'HOT_LOAD': settings.HOT_LOAD}
    return render(request, 'portal/index.html', context)


class UserDetails(APIView):

    def get(self, request):
        return JsonResponse(user_to_dict(request.user))


class EmailAutofillSignupView(SignupView):
    form_class = ExtendedSignupForm

    def get_context_data(self, **kwargs):
        email = self.request.GET.get('email')
        if email:
            kwargs['email'] = email
        return super(EmailAutofillSignupView, self).get_context_data(**kwargs)
