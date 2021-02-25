# Django
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


PROVIDERS = {
    'bitbucket_oauth2': 'Bitbucket',
    'github': 'GitHub',
    'gitlab': 'GitLab',
}


class Command(BaseCommand):
    help = 'Updates credentials for social apps corresponding to' \
           'currently supported auth providers: %s' % PROVIDERS.values()

    def handle(self, *args, **options):
        # Get rid of invalid apps
        SocialApp.objects.exclude(provider__in=PROVIDERS.keys()).delete()

        for key, value in PROVIDERS.items():
            # Leave only a single app per provider
            apps = SocialApp.objects.filter(provider=key)
            if apps.count() > 1:
                apps.delete()
            app = apps.first() or SocialApp(provider=key)

            # Unify names
            app.name = '%s Social App' % value

            app.client_id = getattr(
                settings, '%s_LOGIN_CLIENT_ID' % value.upper(), ''
            )
            app.secret = getattr(
                settings, '%s_LOGIN_SECRET' % value.upper(), ''
            )

            # The app should be saved before using any many-to-many relationship
            app.save()

            # Leave only the main site
            app.sites.clear()
            site = Site.objects.get(id=settings.SITE_ID)
            app.sites.add(site)
