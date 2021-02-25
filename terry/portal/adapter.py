from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        # By default there is no username in data, so the Bitbucket provider
        # tries to imply some username based on first_name, last_name, email
        if sociallogin.account.provider == 'bitbucket_oauth2':
            data['username'] = sociallogin.account.extra_data['username']

        return super(CustomSocialAccountAdapter, self).populate_user(
            request, sociallogin, data
        )
