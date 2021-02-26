import mock
from django.test import TestCase
from django.contrib.auth.models import User
from portal.tasks import add_keyword_to_cache, remove_keyword_from_cache
from keywords.models import SearchKeyword


class UserProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='Tester')
        self.profile = self.user.details

    def test_tags_add_userprofile(self):
        """ Checks that sentences are properly created on doc init """
        self.assertFalse(self.profile.tags)
        self.profile.add_tag('tag1')
        self.profile.add_tag('tag2')
        self.assertEqual(self.profile.tags, ['tag1', 'tag2'])

    def test_profile_duplicate_tags(self):
        self.assertEqual(len(self.profile.tags), 0)

        self.profile.add_tag('tag1')
        self.profile.add_tag('tag2')
        self.assertEqual(len(self.profile.tags), 2)

        self.profile.add_tag('tag2')
        self.assertEqual(len(self.profile.tags), 2)


class UserProfileKeywordCacheTestCase(TestCase):
    def test_add_keyword_to_cache(self):
        user = User.objects.create(username='Tester')

        kw = SearchKeyword.objects.create(keyword='ThisIsKeyword', owner=user, active=True)
        add_keyword_to_cache(kw.pk)

        user = User.objects.get(username='Tester')
        self.assertEqual(user.details.keywords, ['thisiskeyword'])

        kw = SearchKeyword.objects.create(keyword='kw2', owner=user, active=True)
        add_keyword_to_cache(kw.pk)

        user = User.objects.get(username='Tester')
        self.assertEqual(user.details.keywords, ['thisiskeyword', 'kw2'])

    def test_add_duplicate_keyword_to_cache(self):
        user = User.objects.create(username='Tester')

        kw = SearchKeyword.objects.create(keyword='kw', owner=user, active=True)
        add_keyword_to_cache(kw.pk)

        user = User.objects.get(username='Tester')
        self.assertEqual(user.details.keywords, ['kw'])

        add_keyword_to_cache(kw.pk)

        user = User.objects.get(username='Tester')
        self.assertEqual(user.details.keywords, ['kw'])

    def test_remove_keyword_from_cache(self):
        user = User.objects.create(username='Tester')

        kw = SearchKeyword.objects.create(keyword='kw', owner=user, active=True)
        add_keyword_to_cache(kw.pk)

        remove_keyword_from_cache(user.pk, 'kw')

        user = User.objects.get(username='Tester')
        self.assertEqual(user.details.keywords, [])

    @mock.patch('portal.models.add_keyword_to_cache.delay')
    def test_add_keyword_to_cache_on_create(self, mock_add):
        user = User.objects.create(username='Tester')
        kw = SearchKeyword.objects.create(keyword='kw', owner=user, active=True)

        mock_add.assert_called_once_with(kw.pk)

    @mock.patch('portal.models.add_keyword_to_cache.delay')
    def test_add_keyword_to_cache_on_activate(self, mock_add):
        user = User.objects.create(username='Tester')
        kw = SearchKeyword.objects.create(keyword='kw', owner=user, active=False)

        self.assertEqual(mock_add.called, False)
        kw.activate()

        mock_add.assert_called_once_with(kw.pk)

    @mock.patch('portal.models.remove_keyword_from_cache.delay')
    def test_add_keyword_to_cache_on_delete(self, mock_remove):
        user = User.objects.create(username='Tester')
        kw = SearchKeyword.objects.create(keyword='kw', owner=user, active=True)
        kw.delete()
        mock_remove.assert_called_once_with(user.pk, 'kw')

    @mock.patch('portal.models.remove_keyword_from_cache.delay')
    def test_add_keyword_to_cache_on_deactivate(self, mock_remove):
        user = User.objects.create(username='Tester')
        kw = SearchKeyword.objects.create(keyword='kw', owner=user, active=True)
        kw.deactivate()

        mock_remove.assert_called_once_with(user.pk, 'kw')


class UserProfileSettingsTestCase(TestCase):
    def test_add_settings(self):
        user_profile = User.objects.create(username='Tester').details

        sett = {'a': True, 'b': False}
        user_profile.update_settings(sett)
        self.assertEqual(sett, user_profile.settings)

        # Check if saved
        user_profile = User.objects.get(username='Tester').details
        self.assertEqual(sett, user_profile.settings)

        sett = {'a': True, 'b': True, 'c': False}
        user_profile.update_settings({'b': True, 'c': False})
        self.assertEqual(sett, user_profile.settings)

        user_profile = User.objects.get(username='Tester').details
        self.assertEqual(sett, user_profile.settings)
