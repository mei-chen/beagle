from django import forms

from .models import Coupon


class CouponForm(forms.Form):
    coupon_code = forms.CharField(widget=forms.TextInput(attrs={'max-length': 100, 'class' : 'form-control'}))

    def clean_coupon_code(self):
        data = self.cleaned_data['coupon_code']
        coupon = Coupon.get_by_code(data)
        if not coupon:
            raise forms.ValidationError("Invalid coupon code!")

        if not coupon.is_available:
            raise forms.ValidationError("Coupon is no longer available!")

        return data
