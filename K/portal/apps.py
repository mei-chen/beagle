from __future__ import unicode_literals

from django.apps import AppConfig


class PortalConfig(AppConfig):
    name = 'portal'

    def ready(self):
        from portal import signals  # NOQA
