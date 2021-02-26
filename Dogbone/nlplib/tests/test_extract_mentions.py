from unittest import TestCase
from nlplib.utils import extract_mentions


class MentionsTestCase(TestCase):
    def test_simple(self):
        text = "RT @user1: who are @thing and @user2?"
        result = extract_mentions(text)
        self.assertEqual(set(['user1', 'thing', 'user2']), result)

    def test_beaglebot(self):
        text = "@beaglebot what is indemnification"
        result = extract_mentions(text)
        self.assertEqual(set(['beaglebot']), result)

    def test_beagle(self):
        text = "@beagle how do we define litigation?"
        result = extract_mentions(text)
        self.assertEqual(set(['beagle']), result)

    def test_beagleai(self):
        text = "@beagleai: how do we define litigation?"
        result = extract_mentions(text)
        self.assertEqual(set(['beagleai']), result)

    def test_beagle_end(self):
        text = "Who let the dogs out? @beagle"
        result = extract_mentions(text)
        self.assertEqual(set(['beagle']), result)