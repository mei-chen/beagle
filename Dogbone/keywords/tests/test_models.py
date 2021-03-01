import mock
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from keywords.models import SearchKeyword


class SearchKeywordTestCase(TestCase):

    def test_make_standard_simple(self):
        """
        Checking is the standardization procedure properly handles an already standard keyword
        """
        self.assertEqual('a-keyword', SearchKeyword.make_standard('a-keyword'))

    def test_make_standard_with_spaces(self):
        """
        Checking if the standardization procedure properly handles spaces
        """
        self.assertEqual('a-keyword', SearchKeyword.make_standard('a-keyword   '))
        self.assertEqual('a-keyword', SearchKeyword.make_standard('  a-keyword'))

    def test_make_standard_with_capitalized_case(self):
        """
        Checking if the standardization procedure properly handles capital letters
        """
        self.assertEqual('a-keyword', SearchKeyword.make_standard('A-Keyword'))
        self.assertEqual('a-keyword', SearchKeyword.make_standard('a-keyWORD'))

    def test_auto_standardize(self):
        """
        Checking if the keyword is standardized before model is saved
        """
        u = User.objects.create(username='ausername')
        kw = SearchKeyword.objects.create(keyword='ThisIsKeyword', owner=u)
        self.assertEqual(kw.keyword, 'thisiskeyword')

    @mock.patch('keywords.signals.keyword_created.send')
    def test_keyword_created_signal(self, mock_created_send):
        """
        Testing if the `keyword_created` signal is emitted
        """
        u = User.objects.create(username='ausername')
        kw = SearchKeyword.objects.create(keyword='ThisIsKeyword', owner=u)
        mock_created_send.assert_called_once_with(SearchKeyword, user=u, keyword=kw)

    @mock.patch('keywords.signals.keyword_deleted.send')
    def test_keyword_deleted_signal(self, mock_deleted_send):
        """
        Testing if the `keyword_deleted` signal is emitted
        """
        u = User.objects.create(username='ausername')
        kw = SearchKeyword.objects.create(keyword='ThisIsKeyword', owner=u)
        kw.delete()
        mock_deleted_send.assert_called_once_with(SearchKeyword, user=u, keyword=kw)

    @mock.patch('keywords.signals.keyword_activated.send')
    def test_keyword_activated_signal(self, mock_activated_send):
        """
        Testing if the `keyword_activated` signal is emitted
        """
        u = User.objects.create(username='ausername')
        kw = SearchKeyword.objects.create(keyword='ThisIsKeyword', owner=u, active=False)
        kw.activate()
        mock_activated_send.assert_called_once_with(SearchKeyword, user=u, keyword=kw)

    @mock.patch('keywords.signals.keyword_deactivated.send')
    def test_keyword_deactivated_signal(self, mock_deactivated_send):
        """
        Testing if the `keyword_deactivated` signal is emitted
        """
        u = User.objects.create(username='ausername')
        kw = SearchKeyword.objects.create(keyword='ThisIsKeyword', owner=u, active=True)
        kw.deactivate()
        mock_deactivated_send.assert_called_once_with(SearchKeyword, user=u, keyword=kw)

    def test_to_dict(self):
        """
        Testing that the simple model serialization works properly
        """
        u = User.objects.create(username='ausername')
        kw = SearchKeyword.objects.create(keyword='ThisIsKeyword', owner=u, active=True)
        self.assertEqual(kw.to_dict(), {
            'keyword': 'thisiskeyword',
            'active': True,
            'created': mock.ANY,
            'exact_match': False
        })

    def test_unique_together(self):
        """
        Testing that the user can't have the same keyword twice
        """
        user = User.objects.create(username='ausername')
        SearchKeyword.objects.create(keyword='ThisIsKeyword', owner=user)
        self.assertRaises(IntegrityError, SearchKeyword.objects.create, keyword='thisiskeyword', owner=user)

    def test_matches1(self):
        """
        Testing if a keyword matches a certain sentence correctly
        """
        sentence = 'This is a test with an interesting keyword inside'
        user = User.objects.create(username='me', password='123')
        kw = SearchKeyword.objects.create(owner=user, keyword='interesting')
        self.assertTrue(kw.matches(sentence))

    def test_matches2(self):
        """
        Testing if a keyword matches a certain sentence correctly
        """
        sentence = 'This is a test with FuNKy-WriTTen keyword inside'
        user = User.objects.create(username='me', password='123')
        kw = SearchKeyword.objects.create(owner=user, keyword='funky-written')
        self.assertTrue(kw.matches(sentence))

    def test_matches3(self):
        """
        Testing if a keyword matches a certain sentence correctly
        """
        sentence = 'This is a test with an interestingly keyword inside'
        user = User.objects.create(username='me', password='123')
        kw = SearchKeyword.objects.create(owner=user, keyword='interesting', exact_match=False)
        self.assertTrue(kw.matches(sentence))

    def test_not_matches1(self):
        """
        Testing if a keyword doesn't match a certain sentence correctly
        """
        sentence = 'This is a test with an interesting keyword inside'
        user = User.objects.create(username='me', password='123')
        kw = SearchKeyword.objects.create(owner=user, keyword='not-interesting')
        self.assertFalse(kw.matches(sentence))

    def test_not_exact_matches(self):
        """
        Testing if a keyword doesn't match a certain sentence correctly
        """
        sentence = 'This is a test with an interestingly keyword inside'
        user = User.objects.create(username='me', password='123')
        kw = SearchKeyword.objects.create(owner=user, keyword='interesting', exact_match=True)
        self.assertFalse(kw.matches(sentence))
