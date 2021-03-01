from django.test import TestCase
from django.contrib.auth.models import User
from portal.settings import UserSettings


class UserSettingsTest(TestCase):

    def test_settings_defaults(self):
        user = User.objects.create(username='Tester1')
        settings = UserSettings(user)
        self.assertEqual(settings.get_setting('default_report_view'),
                         settings.DEFAULTS['default_report_view'])

    def test_custom_settings(self):
        user = User.objects.create(username='Tester1')
        user.details.settings = {'some_fancy_setting': True}
        user.details.save()
        user.save()

        settings = UserSettings(user)
        self.assertTrue(settings.get_setting('some_fancy_setting'))
