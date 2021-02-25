from allauth.account.forms import SignupForm
from django import forms
from django.utils.translation import ugettext_lazy as _

from marketing.models import Coupon


class ExtendedSignupForm(SignupForm):
    first_name = forms.CharField(
        label=_('First Name'), max_length=30, required=False
    )
    last_name = forms.CharField(
        label=_('Last Name'), max_length=30, required=False
    )
    coupon = forms.CharField(
        label=_('Invitation Code'), max_length=100
    )

    def clean_coupon(self):
        data = self.cleaned_data['coupon']

        coupon = Coupon.get_by_code(data)

        if not coupon:
            raise forms.ValidationError('Invalid invitation code!')

        if not coupon.is_available:
            raise forms.ValidationError('Invitation is no longer available!')

        return data

    def save(self, request):
        user = super(ExtendedSignupForm, self).save(request)
        # All the fields were already validated, and a new user was
        # successfully created and signed up by applying some existing coupon
        Coupon.apply_by_code(self.cleaned_data['coupon'])
        return user
