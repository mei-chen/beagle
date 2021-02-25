from __future__ import unicode_literals

from django.apps import AppConfig


class MarketingConfig(AppConfig):
    name = 'marketing'

    def ready(self):
        # For signals to register
        import marketing.signals.handlers
