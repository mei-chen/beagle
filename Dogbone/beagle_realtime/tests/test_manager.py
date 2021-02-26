import json

from django.contrib.auth.models import User
import mock
from user_sessions.models import Session

from beagle_realtime.notifications import NotificationManager
from core.models import CollaborationInvite, Document
from dogbone.testing.base import BeagleWebTest


class NotificationManagerTestCase(BeagleWebTest):

    def test_send_empty(self):
        message = NotificationManager.create_message()
        result = message.send()
        self.assertFalse(result)

    def test_send(self):
        message = NotificationManager.create_message()
        message.set_channels(['my_channel'])
        message.set_event_name('my_message_type')
        message.set_message({'content': 'A sooooper message'})
        return_mock = mock.Mock()
        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as mock_connection:

            result = message.send()
            return_mock.publish.assert_called_once_with('my_channel', mock.ANY)
            payload = return_mock.publish.call_args[0][1]
            self.assertEqual(json.loads(payload), {'created': mock.ANY,
                                                   'message': {'content': 'A sooooper message'},
                                                   'event_name': 'my_message_type'})
            self.assertTrue(result)

    def test_user_send_no_session(self):
        user = User(username='un', email='email@mail.com')
        user.set_password('12341234')
        user.save()

        message = NotificationManager.create_user_message(user)

        message.set_event_name('my_message_type')
        message.set_message({'content': 'A sooooper message'})
        return_mock = mock.Mock()
        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as mock_connection:

            result = message.send()
            self.assertFalse(return_mock.publish.called)

            self.assertFalse(result)

    def test_user_send_with_session(self):
        user = User(username='un', email='email@mail.com')
        user.set_password('12341234')
        user.save()

        self.client.login(username='un', password='12341234')

        self.assertEqual(len(user.session_set.all()), 1)
        session = user.session_set.all()[0]

        message = NotificationManager.create_user_message(user)

        message.set_event_name('my_message_type')
        message.set_message({'content': 'A sooooper message'})
        return_mock = mock.Mock()
        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as mock_connection:

            result = message.send()
            return_mock.publish.assert_called_once_with('user-notifications.%s' % session.session_key, mock.ANY)
            payload = return_mock.publish.call_args[0][1]
            self.assertEqual(json.loads(payload), {'created': mock.ANY,
                                                   'message': {'content': 'A sooooper message'},
                                                   'event_name': 'my_message_type'})
            self.assertTrue(result)

    def test_multi_user(self):
        user1 = User(username='user1', email='email1@mail.com')
        user1.set_password('12341234')
        user1.save()

        user2 = User(username='user2', email='email2@mail.com')
        user2.set_password('12341234')
        user2.save()

        user3 = User(username='user3', email='email3@mail.com')
        user3.set_password('12341234')
        user3.save()

        document = self.create_document('Title', user1, pending=False)
        CollaborationInvite(document=document, inviter=user1, invitee=user2).save()
        CollaborationInvite(document=document, inviter=user1, invitee=user3).save()

        client1 = self.client_class()
        client1.login(username=user1.username, password='12341234')
        self.assertEqual(len(user1.session_set.all()), 1)

        client2 = self.client_class()
        client2.login(username=user2.username, password='12341234')
        self.assertEqual(len(user2.session_set.all()), 1)

        client3 = self.client_class()
        client3.login(username=user3.username, password='12341234')
        self.assertEqual(len(user3.session_set.all()), 1)

        document = Document.objects.all()[0]
        message = NotificationManager.create_document_message(document)
        message.set_event_name('my_message_type')
        message.set_message({'content': 'A sooooper message'})
        return_mock = mock.Mock()
        sessions = [s.session_key for s in Session.objects.all()]
        self.assertEqual(len(sessions), 3)

        accessed_sessions = []

        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as mock_connection:

            result = message.send()

            self.assertEqual(return_mock.publish.call_count, 3)

            for idx, call in enumerate(return_mock.publish.call_args_list):
                chunks = call[0][0].split('.')
                self.assertEqual(chunks[0], 'user-notifications')
                accessed_sessions.append(chunks[1])
                payload = call[0][1]
                self.assertEqual(json.loads(payload), {'created': mock.ANY,
                                                       'message': {'content': 'A sooooper message'},
                                                       'event_name': 'my_message_type'})
            self.assertTrue(result)

        accessed_sessions = set(accessed_sessions)
        self.assertEqual(accessed_sessions, set(sessions))


    def test_multi_user_except_user(self):
        user1 = User(username='user1', email='email1@mail.com')
        user1.set_password('12341234')
        user1.save()

        user2 = User(username='user2', email='email2@mail.com')
        user2.set_password('12341234')
        user2.save()

        user3 = User(username='user3', email='email3@mail.com')
        user3.set_password('12341234')
        user3.save()

        document = self.create_document('Title', user1, pending=False)
        CollaborationInvite(document=document, inviter=user1, invitee=user2).save()
        CollaborationInvite(document=document, inviter=user1, invitee=user3).save()

        client1 = self.client_class()
        client1.login(username=user1.username, password='12341234')
        self.assertEqual(len(user1.session_set.all()), 1)

        client2 = self.client_class()
        client2.login(username=user2.username, password='12341234')
        self.assertEqual(len(user2.session_set.all()), 1)

        client3 = self.client_class()
        client3.login(username=user3.username, password='12341234')
        self.assertEqual(len(user3.session_set.all()), 1)

        document = Document.objects.all()[0]
        message = NotificationManager.create_document_message(document, except_users=[user2])
        message.set_event_name('my_message_type')
        message.set_message({'content': 'A sooooper message'})
        return_mock = mock.Mock()
        sessions = [s.session_key for s in Session.objects.all()]
        self.assertEqual(len(sessions), 3)

        accessed_sessions = []

        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as mock_connection:

            result = message.send()

            self.assertEqual(return_mock.publish.call_count, 2)

            for idx, call in enumerate(return_mock.publish.call_args_list):
                chunks = call[0][0].split('.')
                self.assertEqual(chunks[0], 'user-notifications')
                accessed_sessions.append(chunks[1])
                payload = call[0][1]
                self.assertEqual(json.loads(payload), {'created': mock.ANY,
                                                       'message': {'content': 'A sooooper message'},
                                                       'event_name': 'my_message_type'})
            self.assertTrue(result)

        accessed_sessions = set(accessed_sessions)
        self.assertNotEqual(accessed_sessions, set(sessions))
        self.assertEqual(set(sessions) - accessed_sessions, set([s.session_key for s in user2.session_set.all()]))

    def test_multi_user_except_session(self):
        user1 = User(username='user1', email='email1@mail.com')
        user1.set_password('12341234')
        user1.save()

        user2 = User(username='user2', email='email2@mail.com')
        user2.set_password('12341234')
        user2.save()

        user3 = User(username='user3', email='email3@mail.com')
        user3.set_password('12341234')
        user3.save()

        document = self.create_document('Title', user1, pending=False)
        CollaborationInvite(document=document, inviter=user1, invitee=user2).save()
        CollaborationInvite(document=document, inviter=user1, invitee=user3).save()

        client1 = self.client_class()
        client1.login(username=user1.username, password='12341234')
        self.assertEqual(len(user1.session_set.all()), 1)

        client2 = self.client_class()
        client2.login(username=user2.username, password='12341234')
        self.assertEqual(len(user2.session_set.all()), 1)

        client3 = self.client_class()
        client3.login(username=user3.username, password='12341234')
        self.assertEqual(len(user3.session_set.all()), 1)

        document = Document.objects.all()[0]
        message = NotificationManager.create_document_message(document,
                                                              except_sessions=[user3.session_set.all()[0].session_key])
        message.set_event_name('my_message_type')
        message.set_message({'content': 'A sooooper message'})
        return_mock = mock.Mock()
        sessions = [s.session_key for s in Session.objects.all()]
        self.assertEqual(len(sessions), 3)

        accessed_sessions = []

        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as mock_connection:

            result = message.send()

            self.assertEqual(return_mock.publish.call_count, 2)

            for idx, call in enumerate(return_mock.publish.call_args_list):
                chunks = call[0][0].split('.')
                self.assertEqual(chunks[0], 'user-notifications')
                accessed_sessions.append(chunks[1])
                payload = call[0][1]
                self.assertEqual(json.loads(payload), {'created': mock.ANY,
                                                       'message': {'content': 'A sooooper message'},
                                                       'event_name': 'my_message_type'})
            self.assertTrue(result)

        accessed_sessions = set(accessed_sessions)
        self.assertNotEqual(accessed_sessions, set(sessions))
        self.assertEqual(set(sessions) - accessed_sessions, set([user3.session_set.all()[0].session_key]))

    def test_document_send_with_session(self):
        user1 = User(username='user1', email='email1@mail.com')
        user1.set_password('12341234')
        user1.save()

        user2 = User(username='user2', email='email2@mail.com')
        user2.set_password('12341234')
        user2.save()

        user3 = User(username='user3', email='email3@mail.com')
        user3.set_password('12341234')
        user3.save()

        # Since we can't have multiple sessions on the test client

        document = self.create_document('Title', user1, pending=False)
        CollaborationInvite(document=document, inviter=user1, invitee=user2).save()
        CollaborationInvite(document=document, inviter=user1, invitee=user3).save()


        self.client.login(username='user1', password='12341234')
        sessions = [s.session_key for s in Session.objects.all()]

        document = Document.objects.all()[0]
        message = NotificationManager.create_document_message(document)
        message.set_event_name('my_message_type')
        message.set_message({'content': 'A sooooper message'})
        return_mock = mock.Mock()
        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as mock_connection:

            result = message.send()
            return_mock.publish.assert_called_once_with('user-notifications.%s' % sessions[0], mock.ANY)
            payload = return_mock.publish.call_args[0][1]
            self.assertEqual(json.loads(payload), {'created': mock.ANY,
                                                   'message': {'content': 'A sooooper message'},
                                                   'event_name': 'my_message_type'})
            self.assertTrue(result)

        self.client.login(username='user2', password='12341234')
        sessions = [s.session_key for s in Session.objects.all()]

        document = Document.objects.all()[0]
        message = NotificationManager.create_document_message(document)
        message.set_event_name('my_message_type')
        message.set_message({'content': 'A sooooper message'})
        return_mock = mock.Mock()
        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as mock_connection:

            result = message.send()
            return_mock.publish.assert_called_once_with('user-notifications.%s' % sessions[0], mock.ANY)
            payload = return_mock.publish.call_args[0][1]
            self.assertEqual(json.loads(payload), {'created': mock.ANY,
                                                   'message': {'content': 'A sooooper message'},
                                                   'event_name': 'my_message_type'})
            self.assertTrue(result)

        self.client.login(username='user3', password='12341234')
        sessions = [s.session_key for s in Session.objects.all()]

        document = Document.objects.all()[0]
        message = NotificationManager.create_document_message(document)
        message.set_event_name('my_message_type')
        message.set_message({'content': 'A sooooper message'})
        return_mock = mock.Mock()
        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as mock_connection:

            result = message.send()
            return_mock.publish.assert_called_once_with('user-notifications.%s' % sessions[0], mock.ANY)
            payload = return_mock.publish.call_args[0][1]
            self.assertEqual(json.loads(payload), {'created': mock.ANY,
                                                   'message': {'content': 'A sooooper message'},
                                                   'event_name': 'my_message_type'})
            self.assertTrue(result)
