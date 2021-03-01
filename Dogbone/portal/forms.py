import logging

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from marketing.models import Coupon, PurchasedSubscription


class LoginForm(forms.Form):
    """
    User login form
    """
    email = forms.EmailField(label="E-mail", required=True,
                             widget=forms.TextInput(attrs={'class': "form-control",
                                                           'placeholder': "Email Address",
                                                           'autofocus': "autofocus"}))
    password = forms.CharField(label="Password", required=True,
                               widget=forms.PasswordInput(attrs={'class': "form-control",
                                                                 'placeholder': 'Password'}))

    def __init__(self, *args, **kwargs):
        self.user = None
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        """
        Validate data
        """

        cleaned_data = self.cleaned_data
        email = cleaned_data.get('email')

        if email:
            email = email.lower()
            if 'autofocus' in self.fields['email'].widget.attrs:
                self.fields['email'].widget.attrs.pop('autofocus')
            self.fields['password'].widget.attrs.update({'autofocus': 'autofocus'})

        password = cleaned_data.get('password')

        self.user = authenticate(username=email,
                                 password=password)

        if self.user is None:
            raise forms.ValidationError('Invalid email or password')
        if not self.user.is_active:
            raise forms.ValidationError('This account is disabled')

        return cleaned_data


class ResetPasswordForm(forms.Form):
    """
    Password reset form
    """
    email = forms.EmailField(label="E-mail",
                             required=True,
                             widget=forms.TextInput(attrs={
                                 'class': "form-control",
                                 'placeholder': "Email Address"}))

    def clean(self):
        email = self.cleaned_data.get('email')

        # Check if the user already exists
        if not self.errors.get('email') and not User.objects.filter(email__iexact=email):
            raise forms.ValidationError('This email is not associated with a Beagle account')

        return self.cleaned_data


class UpdatePasswordForm(forms.Form):
    """ Password update form (after requesting a Password reset) """

    password = forms.CharField(label="Password", required=True,
                               widget=forms.PasswordInput(attrs={'class': "form-control",
                                                                 'placeholder': "Password"}))
    repeat_password = forms.CharField(label="Password", required=True,
                                      widget=forms.PasswordInput(attrs={'class': "form-control",
                                                                        'placeholder': "Confirm Password"}))

    def clean(self):
        password = self.cleaned_data.get('password')
        repeat_password = self.cleaned_data.get('repeat_password')

        # Check that passwords are the same
        if password != repeat_password:
            raise forms.ValidationError('Passwords do not match')

        return self.cleaned_data


class RegisterForm(forms.Form):
    """
    Form used for registering people to Beagle.ai
    """


    first = forms.CharField(label="First Name", required=True,
                            widget=forms.TextInput(attrs={'class': "form-control required",
                                                          'id': "first",
                                                          'placeholder': "First Name",
                                                          'autofocus': "autofocus"}))
    last = forms.CharField(label="Last Name", required=False,
                           widget=forms.TextInput(attrs={'class': "form-control",
                                                         'id': 'last',
                                                         'placeholder': "Last Name"}))
    username = forms.CharField(label="Username", required=True,
                               widget=forms.TextInput(attrs={'class': "form-control required",
                                                             'id': 'username',
                                                             'placeholder': "Username"}))
    email = forms.EmailField(label="E-mail", required=True,
                             widget=forms.TextInput(attrs={'class': "form-control required",
                                                           'id': 'email',
                                                           'placeholder': "Email Address"}))
    phone = forms.CharField(label="Phone Number(optional)", required=False,
                            widget=forms.TextInput(attrs={'class': "form-control",
                                                          'id': 'phone',
                                                          'placeholder': "Phone Number"}))
    password = forms.CharField(label="Password", required=True,
                               widget=forms.PasswordInput(attrs={'class': "form-control required",
                                                                 'id': 'password',
                                                                 'placeholder': "Password"}))
    repeat_password = forms.CharField(label="Password", required=True,
                                      widget=forms.PasswordInput(attrs={'class': "form-control required",
                                                                        'id': 'repeat_password',
                                                                        'placeholder': "Confirm Password"}))
    coupon = forms.CharField(label="Coupon Code", required=False,
                             widget=forms.TextInput(attrs={'class': "form-control",
                                                           'id': 'coupon',
                                                           'placeholder': "If you have a promo code, enter it here"}))

    def __init__(self, *args, **kwargs):
        if 'prepopulated_email' in kwargs:
            self._email = kwargs.pop('prepopulated_email')
        else:
            self._email = None

        self.user = None
        self.coupon = None

        super(RegisterForm, self).__init__(*args, **kwargs)
        if self._email:
            self.fields['email'].initial = self._email
            self.fields['email'].widget.attrs['readonly'] = True

    def clean(self):
        first = self.cleaned_data.get('first')
        last = self.cleaned_data.get('last')
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        phone = self.cleaned_data.get('phone')
        password = self.cleaned_data.get('password')
        repeat_password = self.cleaned_data.get('repeat_password')
        coupon_code = self.cleaned_data.get('coupon')

        if not email or not username or not first:
            return self.cleaned_data

        email = email.lower()

        # Check that passwords are the same
        if password != repeat_password:
            raise forms.ValidationError('Passwords do not match')

        # Check if the email is already used
        if User.objects.filter(email__iexact=email):
            raise forms.ValidationError('This email is already registered')

        # Check if the username is already used
        if User.objects.filter(username=username):
            raise forms.ValidationError('This username is already registered')

        # Check for whitespace in username
        if ' ' in username:
            raise forms.ValidationError('User names may not contain any special characters, symbols or spaces')

        try:
            # Actually create the user
            self.user = User(username=username, email=email)
            self.user.set_password(password)

            # All coupons should be UPPERCASE
            coupon_code = coupon_code.upper() if coupon_code else None

            if coupon_code:
                self.coupon = Coupon.get_by_code(coupon_code)
                if self.coupon is None:
                    raise Exception("This promo code is not valid, please try again.")

                if not self.coupon.is_available:
                    raise Exception("This promo code has expired.")

            self.user.save()

            # Add optional form data
            if phone:
                self.user.details.phone = phone
            if first:
                self.user.first_name = first
            if last:
                self.user.last_name = last

            self.user.details.save()
            self.user.save()

            if self.coupon:
                if self.coupon.is_free:
                    # create the PurchasedSubscription
                    self.coupon.create_subscription(self.user, persist=True)

                    # Add the user to the coupon's group
                    self.coupon.add_user_to_group(self.user)

            else:
                from dogbone.app_settings.marketing_settings import AllAccessTrial
                PurchasedSubscription.purchase_subscription(self.user, AllAccessTrial)

        except Exception as e:
            logging.warning("Exception encountered in RegisterForm: %s" % str(e))
            raise forms.ValidationError(str(e))

        return self.cleaned_data


class SimpleRegisterForm(forms.Form):
    """
    Simplified Form used for registering people to Beagle.ai
    """

    first = forms.CharField(label="First Name", required=False,
                            widget=forms.TextInput(attrs={'class': "form-control",
                                                          'id': "first",
                                                          'placeholder': "First Name",
                                                          'autofocus': "autofocus"}))
    last = forms.CharField(label="Last Name", required=False,
                           widget=forms.TextInput(attrs={'class': "form-control",
                                                         'id': 'last',
                                                         'placeholder': "Last Name"}))
    email = forms.EmailField(label="E-mail", required=True,
                             widget=forms.TextInput(attrs={'class': "form-control required",
                                                           'id': 'email',
                                                           'placeholder': "Email Address"}))
    password = forms.CharField(label="Password", required=True,
                               widget=forms.PasswordInput(attrs={'class': "form-control required",
                                                                 'id': 'password',
                                                                 'placeholder': "Password"}))
    coupon = forms.CharField(label="Coupon Code", required=False,
                             widget=forms.TextInput(attrs={'class': "form-control",
                                                           'id': 'coupon',
                                                           'placeholder': "If you have a promo code, enter it here"}))

    def __init__(self, *args, **kwargs):
        if 'prepopulated_email' in kwargs:
            self._email = kwargs.pop('prepopulated_email')
        else:
            self._email = None

        self.user = None
        self.coupon = None

        super(SimpleRegisterForm, self).__init__(*args, **kwargs)
        if self._email:
            self.fields['email'].initial = self._email
            self.fields['email'].widget.attrs['readonly'] = True

    def clean(self):
        first = self.cleaned_data.get('first')
        last = self.cleaned_data.get('last')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        coupon_code = self.cleaned_data.get('coupon')

        if not email or not password:
            return self.cleaned_data

        email = email.lower()

        # Make sure the lowercase email in in `cleaned_data`
        self.cleaned_data['email'] = email

        # Check if the email is already used
        if User.objects.filter(email__iexact=email):
            raise forms.ValidationError('This email is already registered')

        try:
            # Actually create the user
            username = email

            if len(username) > 30:
              username = username[:30]

              # Checking if username exists to prevent edge case if multiple users with 28 characters being similar
              if User.objects.filter(username=username).exists():
                username = username[:28] + ("_%d" % (User.objects.filter(username__startswith=username[:28]).count()))

            self.user = User(username=username, email=email)
            self.user.set_password(password)

            # All coupons should be UPPERCASE
            coupon_code = coupon_code.upper() if coupon_code else None

            if coupon_code:
                self.coupon = Coupon.get_by_code(coupon_code)
                if self.coupon is None:
                    raise Exception("This promo code is not valid, please try again.")

                if not self.coupon.is_available:
                    raise Exception("This promo code has expired.")

            self.user.save()

            # Add optional form data
            if first:
                self.user.first_name = first
            if last:
                self.user.last_name = last

            self.user.details.save()
            self.user.save()

            if self.coupon:
                if self.coupon.is_free:
                    # create the PurchasedSubscription
                    self.coupon.create_subscription(self.user, persist=True)

                    # Add the user to the coupon's group
                    self.coupon.add_user_to_group(self.user)

            else:
                from dogbone.app_settings.marketing_settings import AllAccessTrial
                PurchasedSubscription.purchase_subscription(self.user, AllAccessTrial)

        except Exception as e:
            logging.warning("Exception encountered in RegisterForm: %s" % str(e))
            raise forms.ValidationError(str(e))

        return self.cleaned_data


class BrowserExtensionRegisterForm(forms.Form):
    """
    Form used for registering to the Beagle.ai Browser extension
    """

    first = forms.CharField(label="First Name", required=True,
                            widget=forms.TextInput(attrs={'class': "form-control required",
                                                          'id': "first",
                                                          'placeholder': "First Name"}))
    last = forms.CharField(label="Last Name", required=False,
                           widget=forms.TextInput(attrs={'class': "form-control",
                                                         'id': 'last',
                                                         'placeholder': "Last Name"}))
    username = forms.CharField(label="Username", required=True,
                               widget=forms.TextInput(attrs={'class': "form-control required",
                                                             'id': 'username',
                                                             'placeholder': "Username"}))
    email = forms.EmailField(label="E-mail", required=True,
                             widget=forms.TextInput(attrs={'class': "form-control required",
                                                           'id': 'email',
                                                           'placeholder': "Email Address"}))
    phone = forms.CharField(label="Phone Number(optional)", required=False,
                            widget=forms.TextInput(attrs={'class': "form-control",
                                                          'id': 'phone',
                                                          'placeholder': "Phone Number"}))

    password = forms.CharField(label="Password", required=True,
                               widget=forms.PasswordInput(attrs={'class': "form-control required",
                                                                 'id': 'password',
                                                                 'placeholder': "Password"}))
    repeat_password = forms.CharField(label="Password", required=True,
                                      widget=forms.PasswordInput(attrs={'class': "form-control required",
                                                                        'id': 'repeat_password',
                                                                        'placeholder': "Confirm Password"}))

    def __init__(self, *args, **kwargs):
        self.user = None
        super(BrowserExtensionRegisterForm, self).__init__(*args, **kwargs)

    def clean(self):
        first = self.cleaned_data.get('first')
        last = self.cleaned_data.get('last')
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        phone = self.cleaned_data.get('phone')
        password = self.cleaned_data.get('password')
        repeat_password = self.cleaned_data.get('repeat_password')

        if not email or not username or not first:
            return self.cleaned_data

        email = email.lower()

        # Check that passwords are the same
        if password != repeat_password:
            raise forms.ValidationError('Passwords do not match')

        # Check if the email is already used
        if User.objects.filter(email__iexact=email):
            raise forms.ValidationError('This email is already registered')

        # Check if the username is already used
        if User.objects.filter(username=username):
            raise forms.ValidationError('This username is already registered')

        # Check for whitespace in username
        if ' ' in username:
            raise forms.ValidationError('User names may not contain any special characters, symbols or spaces')

        try:
            # Actually create the user
            self.user = User(username=username, email=email)
            self.user.set_password(password)
            self.user.save()

            # Add optional form data
            if phone:
                self.user.details.phone = phone
            if first:
                self.user.first_name = first
            if last:
                self.user.last_name = last

            self.user.details.save()
            self.user.save()

            from dogbone.app_settings.marketing_settings import UnlimitedBrowserExtensionSubscription
            PurchasedSubscription.purchase_subscription(self.user, UnlimitedBrowserExtensionSubscription)

        except Exception as e:
            logging.warning("Exception encountered in BrowserExtensionRegisterForm: %s" % str(e))
            raise forms.ValidationError(str(e))

        return self.cleaned_data
