import mock
import json
from django.urls import reverse
from dogbone.testing.base import BeagleWebTest
from core.tools import render_notification
from core.models import CollaborationInvite, Sentence
from core.tasks import store_activity_notification, mark_as_read_sentence_related_notifications
from user_sessions.models import Session
from notifications.models import Notification


class NotificationTaskTest(BeagleWebTest):
    def test_success(self):
        self.make_paid(self.user)
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')
        document = self.create_document('Some Title', self.user, pending=False)

        stored_notifications = Notification.objects.all()
        self.assertEqual(len(stored_notifications), 0)

        self.login()

        return_mock = mock.Mock()
        with mock.patch('beagle_realtime.notifications.NotificationManager.redis_manager.get_connection',
                        return_value=return_mock) as _:

            store_activity_notification(
                actor=self.user,
                recipient=self.user,
                verb=' invited ',
                target=other_user,
                action_object=document,
                render_string='(actor) invited (target) to collaborate on (action_object)',
            )
            sessions = [s.session_key for s in Session.objects.all()]
            return_mock.publish.assert_called_once_with('user-notifications.%s' % sessions[0], mock.ANY)

            payload = json.loads(return_mock.publish.call_args[0][1])

            self.assertEqual(payload, {'created': mock.ANY,
                                       'event_name': 'message',
                                       'message': {'activity_update': {'action_object': {'created': mock.ANY,
                                                                                         'original_name': 'Some Title.pdf',
                                                                                         'owner': {
                                                                                             'avatar': '/static/img/mug.png',
                                                                                             'email': self.DUMMY_EMAIL,
                                                                                             'first_name': None,
                                                                                             'id': mock.ANY,
                                                                                             'last_name': None,
                                                                                             'pending': False,
                                                                                             'job_title': None,
                                                                                             'company': None,
                                                                                             'username': self.DUMMY_USERNAME,
                                                                                             'tags': mock.ANY,
                                                                                             'keywords': mock.ANY,
                                                                                             'settings': mock.ANY,
                                                                                             'is_paid': True,
                                                                                             'had_trial': mock.ANY,
                                                                                             'is_super': False,
                                                                                             'date_joined': mock.ANY,
                                                                                             'last_login': mock.ANY,
                                                                                             'document_upload_count': 1,
                                                                                             'phone': None},
                                                                                         'title': 'Some Title',
                                                                                         'uuid': mock.ANY},
                                                                       'action_object_type': 'document',
                                                                       'actor': {'avatar': '/static/img/mug.png',
                                                                                 'email': self.DUMMY_EMAIL,
                                                                                 'first_name': None,
                                                                                 'id': mock.ANY,
                                                                                 'last_name': None,
                                                                                 'pending': False,
                                                                                 'job_title': None,
                                                                                 'company': None,
                                                                                 'username': self.DUMMY_USERNAME,
                                                                                 'tags': mock.ANY,
                                                                                 'keywords': mock.ANY,
                                                                                 'settings': mock.ANY,
                                                                                 'is_paid': True,
                                                                                 'had_trial': mock.ANY,
                                                                                 'is_super': False,
                                                                                 'date_joined': mock.ANY,
                                                                                 'last_login': mock.ANY,
                                                                                 'document_upload_count': 1,
                                                                                 'phone': None},
                                                                       'actor_type': 'user',
                                                                       'data': {
                                                                           'render_string': '(actor) invited (target) to collaborate on (action_object)',
                                                                           'transient': False},
                                                                       'description': None,
                                                                       'id': mock.ANY,
                                                                       'level': 'info',
                                                                       'read': False,
                                                                       'render_string': '(actor) invited (target) to collaborate on (action_object)',
                                                                       'suggested_display': 'You invited new_username to collaborate on Some Title',
                                                                       'target': {'avatar': '/static/img/mug.png',
                                                                                  'email': 'myemail@hhh.com',
                                                                                  'first_name': None,
                                                                                  'id': mock.ANY,
                                                                                  'last_name': None,
                                                                                  'pending': False,
                                                                                  'job_title': None,
                                                                                  'company': None,
                                                                                  'username': 'new_username',
                                                                                  'is_paid': False,
                                                                                  'had_trial': mock.ANY,
                                                                                  'is_super': False,
                                                                                  'tags': mock.ANY,
                                                                                  'keywords': mock.ANY,
                                                                                  'settings': mock.ANY,
                                                                                  'date_joined': mock.ANY,
                                                                                  'last_login': mock.ANY,
                                                                                  'document_upload_count': 0,
                                                                                  'phone': None},
                                                                       'target_type': 'user',
                                                                       'timestamp': mock.ANY,
                                                                       'verb': ' invited ',
                                                                       'url': reverse('report', kwargs={'uuid': document.uuid})},
                                                   'notif': 'ACTIVITY_UPDATE'}})

        stored_notifications = Notification.objects.all()
        self.assertEqual(len(stored_notifications), 1)


class RenderNotificationTest(BeagleWebTest):

    def test_all(self):
        document = self.create_document('Some Title', self.user, pending=False)
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.action_object = document

        self.assertEqual(render_notification(notif),
                         'You has invited new_username on Some Title')

    def test_missing_action_object(self):
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user

        self.assertEqual(render_notification(notif),
                         'You has invited new_username')

    def test_with_render_string(self):
        document = self.create_document('Some Title', self.user, pending=False)
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.action_object = document
        notif.data = {'render_string': '(actor) just invited (target) to collaborate on "(action_object)"'}

        self.assertEqual(render_notification(notif),
                         'You just invited new_username to collaborate on "Some Title"')

    def test_with_render_string_missing_action_object(self):
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.data = {'render_string': '(actor) just became friends with (target)'}

        self.assertEqual(render_notification(notif),
                         'You just became friends with new_username')

    def test_with_render_string_and_verb(self):
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        notif = Notification()
        notif.actor = self.user
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user
        notif.data = {'render_string': '(actor) (verb) (target)'}

        self.assertEqual(render_notification(notif),
                         'You has invited new_username')

    def test_with_render_string_more_users(self):
        document = self.create_document('Some Title', self.user, pending=False)
        other_user1 = self.create_user('myemail1@hhh.com', 'new_username1', 'p@ss')
        other_user2 = self.create_user('myemail2@hhh.com', 'new_username2', 'p@ss')

        notif = Notification()
        notif.actor = other_user1
        notif.recipient = self.user
        notif.verb = 'has invited'
        notif.target = other_user2
        notif.action_object = document
        notif.data = {'render_string': '(actor) just invited (target) to collaborate on "(action_object)"'}

        self.assertEqual(render_notification(notif),
                         'new_username1 just invited new_username2 to collaborate on "Some Title"')


class AutoMarkAsReadNotificationTest(BeagleWebTest):
    def test_mark_as_read_sentence_related_notifications(self):
        # Britney Spears "Baby One More Time" lyrics. For the full song:
        # http://www.azlyrics.com/lyrics/britneyspears/babyonemoretime.html
        sentences = ['How was I supposed to know',
                     'That something wasn\'t right here',
                     'Oh baby baby',
                     'I shouldn\'t have let you go']

        # Create a document
        document = self.create_analysed_document('Baby One More Time', sentences, self.user)

        # Create another user
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        # Add the new user to the document
        CollaborationInvite(inviter=self.user,
                            invitee=other_user,
                            document=document).save()

        # Get the third sentence
        sentence = Sentence.objects.get(pk=document.sents['sentences'][2])

        # The invited user comments on the sentence
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='mentioned',
            target=self.user,
            action_object=sentence,
            render_string="(actor) mentioned (target) in a comment on (action_object)",
            transient=False)

        # The invited user comments on the sentence again
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='mentioned',
            target=self.user,
            action_object=sentence,
            render_string="(actor) mentioned (target) in a comment on (action_object)",
            transient=False)

        # The invited user likes the sentence
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='liked',
            target=sentence,
            render_string="(actor) liked (target)",
            transient=False)

        notifications = Notification.objects.filter(recipient=self.user)

        # Test that the 3 notifications have been created
        self.assertEqual(len(notifications), 3)

        # Check that all are unread
        self.assertTrue(all([n.unread for n in notifications]))

        # Run the task that marks related sentences as read
        mark_as_read_sentence_related_notifications(self.user.pk, sentence.pk)

        notifications = Notification.objects.filter(recipient=self.user)

        # Check that there still are 3 notifications
        self.assertEqual(len(notifications), 3)

        # Check that all of them are read
        self.assertFalse(any([n.unread for n in notifications]))

    def test_mark_as_read_sentence_related_notifications_for_prev_versions(self):
        # Britney Spears "Baby One More Time" lyrics. For the full song:
        # http://www.azlyrics.com/lyrics/britneyspears/babyonemoretime.html
        sentences = ['How was I supposed to know',
                     'That something wasn\'t right here',
                     'Oh baby baby',
                     'I shouldn\'t have let you go']

        # Create a document
        document = self.create_analysed_document('Baby One More Time', sentences, self.user)

        # Create another user
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        # Add the new user to the document
        CollaborationInvite(inviter=self.user,
                            invitee=other_user,
                            document=document).save()

        # Get the third sentence
        sentence = Sentence.objects.get(pk=document.sents['sentences'][2])

        # The invited user comments on the sentence
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='mentioned',
            target=self.user,
            action_object=sentence,
            render_string="(actor) mentioned (target) in a comment on (action_object)",
            transient=False)

        # The invited user comments on the sentence again
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='mentioned',
            target=self.user,
            action_object=sentence,
            render_string="(actor) mentioned (target) in a comment on (action_object)",
            transient=False)

        # The invited user likes the sentence
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='liked',
            target=sentence,
            render_string="(actor) liked (target)",
            transient=False)

        new_sentence = sentence.edit(other_user, annotations=None, text="A better lyric")

        notifications = Notification.objects.filter(recipient=self.user)

        # Test that the 3 notifications have been created
        self.assertEqual(len(notifications), 3)

        # Check that all are unread
        self.assertTrue(all([n.unread for n in notifications]))

        # Run the task that marks related sentences as read
        mark_as_read_sentence_related_notifications(self.user.pk, new_sentence.pk)

        notifications = Notification.objects.filter(recipient=self.user)

        # Check that there still are 3 notifications
        self.assertEqual(len(notifications), 3)

        # Check that all of them are read
        self.assertFalse(any([n.unread for n in notifications]))

    def test_mark_as_read_sentence_related_notifications_is_called_on_comment(self):
        self.make_paid(self.user)
        # Christina Aguilera "Tough Lover" lyrics. For the full song:
        # http://www.azlyrics.com/lyrics/christinaaguilera/toughlover.html
        sentences = ['When he kisses me, I get that thrill',
                     'When he does that wiggle I won\'t keep still',
                     'I wanna a tough lover (yeah, yeah)',
                     'A tough lover (woo)']

        # Create a document
        document = self.create_analysed_document('Tough Lover', sentences, self.user)

        # Create another user
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        # Add the new user to the document
        CollaborationInvite(inviter=self.user,
                            invitee=other_user,
                            document=document).save()

        # Get the third sentence
        sentence = Sentence.objects.get(pk=document.sents['sentences'][1])

        # The invited user comments on the sentence
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='mentioned',
            target=self.user,
            action_object=sentence,
            render_string="(actor) mentioned (target) in a comment on (action_object)",
            transient=False)

        # The invited user comments on the sentence again
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='mentioned',
            target=self.user,
            action_object=sentence,
            render_string="(actor) mentioned (target) in a comment on (action_object)",
            transient=False)

        # The invited user likes the sentence
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='liked',
            target=sentence,
            render_string="(actor) liked (target)",
            transient=False)

        notifications = Notification.objects.filter(recipient=self.user)

        # Test that the 3 notifications have been created
        self.assertEqual(len(notifications), 3)

        # Check that all are unread
        self.assertTrue(all([n.unread for n in notifications]))

        with mock.patch('api_v1.sentence.endpoints.mark_as_read_sentence_related_notifications.delay') as mock_mark_read:
            self.login()
            url = reverse('sentence_comments_list_view', kwargs={'uuid': document.uuid, 's_idx': 1})
            data = {'message': 'Awesome!'}
            response = self.client.post(url, data=json.dumps(data), content_type='application/json')
            self.assertEqual(response.status_code, 200)

            mock_mark_read.assert_called_once_with(self.user.pk, sentence.pk)

    def test_mark_as_read_sentence_related_notifications_is_called_on_like(self):
        self.make_paid(self.user)
        # Christina Aguilera "Tough Lover" lyrics. For the full song:
        # http://www.azlyrics.com/lyrics/christinaaguilera/toughlover.html
        sentences = ['We gon\' party like it\'s yo birthday',
                     'We gon\' sip Bacardi like it\'s yo birthday',
                     'Cause you know we don\'t give a fuck',
                     'It\'s not your birthday!']

        # Create a document
        document = self.create_analysed_document('In Da Club', sentences, self.user)

        # Create another user
        other_user = self.create_user('myemail@hhh.com', 'new_username', 'p@ss')

        # Add the new user to the document
        CollaborationInvite(inviter=self.user,
                            invitee=other_user,
                            document=document).save()

        # Get the third sentence
        sentence = Sentence.objects.get(pk=document.sents['sentences'][3])

        # The invited user comments on the sentence
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='mentioned',
            target=self.user,
            action_object=sentence,
            render_string="(actor) mentioned (target) in a comment on (action_object)",
            transient=False)

        # The invited user comments on the sentence again
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='mentioned',
            target=self.user,
            action_object=sentence,
            render_string="(actor) mentioned (target) in a comment on (action_object)",
            transient=False)

        # The invited user likes the sentence
        store_activity_notification(
            actor=other_user,
            recipient=self.user,
            verb='liked',
            target=sentence,
            render_string="(actor) liked (target)",
            transient=False)

        notifications = Notification.objects.filter(recipient=self.user)

        # Test that the 3 notifications have been created
        self.assertEqual(len(notifications), 3)

        # Check that all are unread
        self.assertTrue(all([n.unread for n in notifications]))

        with mock.patch('api_v1.sentence.endpoints.mark_as_read_sentence_related_notifications.delay') as mock_mark_read:
            self.login()
            like_url = reverse('sentence_like_view', kwargs={'uuid': document.uuid, 's_idx': 3})
            response = self.client.post(like_url)
            self.assertEqual(response.status_code, 200)

            mock_mark_read.assert_called_once_with(self.user.pk, sentence.pk)
