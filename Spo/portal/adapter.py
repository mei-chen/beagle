from allauth.account.adapter import DefaultAccountAdapter


class EmailAsUsernameAccountAdapter(DefaultAccountAdapter):

    def save_user(self, request, user, form, commit=True):
        # Use already validated unique email as username
        form.cleaned_data.setdefault(
            'username', form.cleaned_data.get('email')
        )
        return super(EmailAsUsernameAccountAdapter, self).save_user(
            request, user, form, commit
        )
