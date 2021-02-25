from __future__ import unicode_literals

import requests

from urllib import urlencode

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from terry.utils import BITBUCKET_OAUTH_URL, GITLAB_OAUTH_URL


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    github_access_token = models.CharField(max_length=64, blank=True)
    bitbucket_refresh_token = models.CharField(max_length=64, blank=True)
    gitlab_refresh_token = models.CharField(max_length=64, blank=True)

    # For Github App created users only
    github_installation_id = models.CharField(max_length=64, blank=True)

    @property
    def bitbucket_access_token(self):
        if not self.bitbucket_refresh_token:
            return ''

        response = requests.post(
            BITBUCKET_OAUTH_URL,
            data={'grant_type': 'refresh_token',
                  'refresh_token': self.bitbucket_refresh_token},
            auth=requests.auth.HTTPBasicAuth(
                settings.BITBUCKET_OAUTH_CLIENT_ID,
                settings.BITBUCKET_OAUTH_SECRET
            )
        )
        payload = response.json()

        access_token = payload['access_token']

        return access_token

    @property
    def gitlab_access_token(self):
        if not self.gitlab_refresh_token:
            return ''

        response = requests.post(
            GITLAB_OAUTH_URL + '?' + urlencode({
                'grant_type': 'refresh_token',
                'refresh_token': self.gitlab_refresh_token
            })
        )
        payload = response.json()

        access_token = payload['access_token']
        # Each time we refresh access token, refresh token also gets updated
        self.gitlab_refresh_token = payload['refresh_token']
        self.save()

        return access_token


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
