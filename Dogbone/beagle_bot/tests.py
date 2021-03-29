# -*- coding: utf-8 -*-
import mock
import json
from unittest import TestCase, skip
from django.urls import reverse
from dogbone.testing.base import BeagleWebTest
from beagle_bot.luis import LUIS
from beagle_bot.bot import BeagleBot
from beagle_bot.tasks import ask_beagle
from core.models import Sentence
from beagle_realtime.notifications import NotificationManager


class BeagleBotTest(TestCase):
    def test_simple(self):
        with mock.patch('beagle_bot.bot.LuisAPI.ask') as mock_luis_ask:
            mock_luis_ask.return_value = 'advocado', 0.99
            with mock.patch('beagle_bot.bot.WikipediaDefinitionFetcher.find_definition') as mock_find_definition:
                mock_find_definition.return_value = {'title': 'Advocado', 'definition': 'Something cool!'}

                comment_dict, response_type = BeagleBot.ask('What is advocado ?')

                self.assertEqual(comment_dict, {'body': 'Something cool!', 'status': 0, 'title': 'Advocado'})
                self.assertEqual(response_type, BeagleBot.ResponseTypes.WIKIPEDIA)

    def test_no_result(self):
        with mock.patch('beagle_bot.bot.LuisAPI.ask') as mock_luis_ask:
            mock_luis_ask.return_value = 'lolozaurus', 0.99
            with mock.patch('beagle_bot.bot.WikipediaDefinitionFetcher.find_definition') as mock_find_definition:
                mock_find_definition.return_value = None

                comment_dict, response_type = BeagleBot.ask('What is lolozaurus ?')

                self.assertEqual(comment_dict, {'body': None, 'status': 1, 'title': 'Sorry, Beagle is still a puppy in training'})
                self.assertEqual(response_type, BeagleBot.ResponseTypes.ERROR)

    def test_low_confidence(self):
        with mock.patch('beagle_bot.bot.LuisAPI.ask') as mock_luis_ask:
            mock_luis_ask.return_value = 'lolozaurus', 0.01
            with mock.patch('beagle_bot.bot.WikipediaDefinitionFetcher.find_definition'):
                comment_dict, response_type = BeagleBot.ask('What is lolozaurus ?')

                self.assertEqual(comment_dict, {'body': None, 'status': 1, 'title': 'Sorry, the question seems a bit ambiguous ...'})
                self.assertEqual(response_type, BeagleBot.ResponseTypes.ERROR)

    def test_blacks_dict(self):
        with mock.patch('beagle_bot.bot.LuisAPI.ask') as mock_luis_ask:
            mock_luis_ask.return_value = 'abadengo', 0.99
            comment_dict, response_type = BeagleBot.ask('What is abadengo ?')

            self.assertEqual(comment_dict,
                             {'body': 'In Spanish law. Land owned by an ecclesiastical corporation, '
                                      'and therefore exempt from taxation. In particular, lands or towns '
                                      'under the dominion and jurisdiction of an abbot',
                              'status': 0,
                              'title': 'Abadengo'})
            self.assertEqual(response_type, BeagleBot.ResponseTypes.BLACKS)


@skip('The Luis API seems to work, so there is no need in additional dummy requests')
class LUISTest(TestCase):
    """ Tests for the LUIS integration """

    def setUp(self):
        self.luis = LUIS()

    def test_simple_call(self):
        q = 'I am asking a dog for help here... I feel so dumb.'
        subject, score = self.luis.ask(q)
        if subject == None == score:  # not available
            return
        self.assertIsNone(subject)
        self.assertTrue(0.0 <= score <= 1.0)

    def test_empty_q(self):
        q = ''
        subject, score = self.luis.ask(q)
        if subject == None == score:  # not available
            return
        self.assertIsNone(subject)
        self.assertTrue(0.0 <= score <= 1.0)

    def test_longest_q_possible(self):
        q = '''Lorem ipsum dolor sit amet, consectetur adipiscing elit cras viverra vitae ligula sed placerat
        suspendisse malesuada risus in justo placerat, id venenatis neque fringilla venenatis neque fringilla.'''
        subject, score = self.luis.ask(q)
        if subject == None == score:  # not available
            return
        self.assertIsNone(subject)
        self.assertTrue(0.0 <= score <= 1.0)

    def test_easy_indemnification(self):
        q = 'What is indemnification?'
        subject, score = self.luis.ask(q)
        if subject == None == score:  # not available
            return
        self.assertEqual('indemnification', subject)
        self.assertTrue(0.0 <= score <= 1.0)


class SentenceBeagleBotCommentTest(BeagleWebTest):

    # TODO: Test BeagleBot.ask()

    @classmethod
    def setUpClass(cls):
        super(SentenceBeagleBotCommentTest, cls).setUpClass()

        cls.sentences = ['I like flowers.', 'I don\'t like butter.']
        cls.document = cls.create_analysed_document(
            'My beautiful document', cls.sentences, cls.user
        )

        cls.make_paid(cls.user)

    def setUp(self):
        super(SentenceBeagleBotCommentTest, self).setUp()

        self.login()

    def test_ask_beagle(self):
        return_mock = mock.Mock()
        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as _:
            with mock.patch('beagle_bot.tasks.BeagleBot.ask') as mock_ask:
                mock_ask.return_value = {'title': 'Some Stuff', 'body': 'Some other stuff'}, BeagleBot.ResponseTypes.WIKIPEDIA
                ask_beagle("@[beagle] : Who likes flowers?",
                           Sentence.objects.get(pk=self.document.sentences_pks[0]),
                           0,
                           self.document)

                sentence = Sentence.objects.get(pk=self.document.sentences_pks[0])
                self.assertEqual(sentence.comments, {'comments': [
                    {'uuid': mock.ANY,
                     'author': '@beagle',
                     'timestamp': mock.ANY,
                     'response_type': BeagleBot.ResponseTypes.WIKIPEDIA,
                     'message': None,
                     'response': {'body': 'Some other stuff', 'title': 'Some Stuff'}}]})

                return_mock.publish.assert_called_once()
                payload = json.loads(return_mock.publish.call_args[0][1])

                self.assertEqual(payload,
                                 {'created': mock.ANY,
                                  'event_name': 'message',
                                  'message': {'comment': {'author': {'username': '@beagle'},
                                                          'message': None,
                                                          'response': {'body': 'Some other stuff',
                                                                       'title': 'Some Stuff'},
                                                          'response_type': BeagleBot.ResponseTypes.WIKIPEDIA,
                                                          'timestamp': mock.ANY,
                                                          'uuid': mock.ANY},
                                              'notif': NotificationManager.ServerNotifications.COMMENT_ADDED_NOTIFICATION,
                                              'sentence': {'accepted': True,
                                                           'annotations': None,
                                                           'comments': [{'author': {'username': '@beagle'},
                                                                         'message': None,
                                                                         'response': {'body': 'Some other stuff',
                                                                                      'title': 'Some Stuff'},
                                                                         'response_type': BeagleBot.ResponseTypes.WIKIPEDIA,
                                                                         'timestamp': mock.ANY,
                                                                         'uuid': mock.ANY}],
                                                           'comments_count': 1,
                                                           'deleted': False,
                                                           'doc': self.document.uuid,
                                                           'external_refs': [],
                                                           'form': 'I like flowers.',
                                                           'idx': 0,
                                                           'likes': None,
                                                           'lock': None,
                                                           'style': None,
                                                           'newlines': mock.ANY,
                                                           'modified_by': self.DUMMY_USERNAME,
                                                           'rejected': False,
                                                           'uuid': mock.ANY}}})

    def test_post_comment_then_beagle_request(self):
        url = reverse('sentence_comments_list_view', kwargs={'uuid': self.document.uuid, 's_idx': 0})

        # Post a normal comment
        data = {'message': 'Awesome!'}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'objects': [{'author': mock.ANY,
                                             'message': 'Awesome!',
                                             'timestamp': mock.ANY,
                                             'uuid': mock.ANY}]})

        # Check the sentence model
        sentence = Sentence.objects.get(pk=self.document.sentences_pks[0])
        self.assertEqual(sentence.comments, {'comments': [
            {'timestamp': mock.ANY,
             'message': 'Awesome!',
             'uuid': mock.ANY,
             'author': self.DUMMY_USERNAME}]})

        # Post a normal comment
        data = {'message': 'Still Awesome!'}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'objects': [{'author': mock.ANY,
                                             'message': 'Still Awesome!',
                                             'timestamp': mock.ANY,
                                             'uuid': mock.ANY}]})

        # Check the sentence model
        sentence = Sentence.objects.get(pk=self.document.sentences_pks[0])
        self.assertEqual(sentence.comments, {'comments': [
            {'timestamp': mock.ANY,
             'message': 'Still Awesome!',
             'uuid': mock.ANY,
             'author': self.DUMMY_USERNAME},
            {'timestamp': mock.ANY,
             'message': 'Awesome!',
             'uuid': mock.ANY,
             'author': self.DUMMY_USERNAME}]})

        document_upload_count = self.user.details.document_upload_count

        return_mock = mock.Mock()
        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock):
            with mock.patch('beagle_bot.tasks.ask_beagle.delay') as mock_ask_beagle:
                # Post a Beagle request comment
                data = {'message': '@[beagle] What is indemnification?'}
                response = self.client.post(url, data=json.dumps(data), content_type='application/json')
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.content)
                self.assertEqual(data, {'objects': [{'author': mock.ANY,
                                                     'message': '@[beagle] What is indemnification?',
                                                     'timestamp': mock.ANY,
                                                     'uuid': mock.ANY}]})

                return_mock.publish.assert_called_once()
                payload = json.loads(return_mock.publish.call_args[0][1])

                user_payload = {'avatar': '/static/img/mug.png',
                                'email': self.DUMMY_EMAIL,
                                'first_name': None,
                                'id': mock.ANY,
                                'last_name': None,
                                'pending': False,
                                'job_title': None,
                                'company': None,
                                'username': self.DUMMY_USERNAME,
                                'date_joined': mock.ANY,
                                'last_login': mock.ANY,
                                'tags': mock.ANY,
                                'keywords': mock.ANY,
                                'settings': mock.ANY,
                                'is_paid': True,
                                'had_trial': mock.ANY,
                                'is_super': False,
                                'document_upload_count': document_upload_count,
                                'phone': None}

                self.assertEqual(payload,
                    {'created': mock.ANY,
                     'event_name': 'message',
                     'message': {'comment': {'author': user_payload,
                                             'message': '@[beagle] What is indemnification?',
                                             'timestamp': mock.ANY,
                                             'uuid': mock.ANY},
                                 'notif': NotificationManager.ServerNotifications.COMMENT_ADDED_NOTIFICATION,
                                 'sentence': {'accepted': True,
                                              'annotations': None,
                                              'comments': [{'author': user_payload,
                                                            'message': '@[beagle] What is indemnification?',
                                                            'timestamp': mock.ANY,
                                                            'uuid': mock.ANY},
                                                           {'author': user_payload,
                                                            'message': 'Still Awesome!',
                                                            'timestamp': mock.ANY,
                                                            'uuid': mock.ANY},
                                                           {'author': user_payload,
                                                            'message': 'Awesome!',
                                                            'timestamp': mock.ANY,
                                                            'uuid': mock.ANY}],
                                              'comments_count': 3,
                                              'deleted': False,
                                              'doc': self.document.uuid,
                                              'external_refs': [],
                                              'form': 'I like flowers.',
                                              'idx': 0,
                                              'likes': None,
                                              'lock': None,
                                              'style': None,
                                              'newlines': mock.ANY,
                                              'modified_by': self.DUMMY_USERNAME,
                                              'rejected': False,
                                              'uuid': mock.ANY}}})

                mock_ask_beagle.assert_called_once_with('@[beagle] What is indemnification?',
                                                        Sentence.objects.get(pk=self.document.sentences_pks[0]),
                                                        0, self.document)
