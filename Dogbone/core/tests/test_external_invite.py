import mock
from core.models import CollaborationInvite, ExternalInvite, Sentence
from dogbone.testing.base import BeagleWebTest
from django.contrib.auth.models import User
from core.tasks import parse_comments_on_external_invite_delete


class ExternalInviteTest(BeagleWebTest):
    def test_user_creation(self):
        """
        Test that ExternalInvites transform to CollaborationInvites when the user joins
        """
        EXTERNAL_EMAIL = 'external@email.com'
        document = self.create_document('Some Title', self.user, pending=False)
        external_invite = ExternalInvite(email=EXTERNAL_EMAIL,
                                         document=document,
                                         inviter=self.user,
                                         pending=True)
        external_invite.save()

        self.assertIsNone(external_invite.email_sent_date)
        self.assertEqual(len(CollaborationInvite.objects.all()), 0)
        self.assertEqual(len(ExternalInvite.pending_objects.all()), 1)
        self.assertEqual(len(ExternalInvite.ready_objects.all()), 0)

        user = self.create_user(EXTERNAL_EMAIL, 'new_username', 'p@ss')
        external_invite = ExternalInvite.objects.get(pk=external_invite.pk)
        self.assertIsNotNone(external_invite.email_sent_date)
        self.assertEqual(len(ExternalInvite.pending_objects.all()), 0)
        self.assertEqual(len(ExternalInvite.ready_objects.all()), 1)

        collaboration_invites = CollaborationInvite.objects.all()
        self.assertEqual(len(collaboration_invites), 1)
        collaboration_invite = collaboration_invites[0]
        self.assertEqual(collaboration_invite.inviter, self.user)
        self.assertEqual(collaboration_invite.invitee, user)
        self.assertEqual(collaboration_invite.document, document)

    def test_to_user_dict(self):
        """
        Test the format of ExternalInvite.to_user_dict
        """
        EXTERNAL_EMAIL = 'external@email.com'
        document = self.create_document('Some Title', self.user, pending=False)
        external_invite = ExternalInvite(email=EXTERNAL_EMAIL,
                                         document=document,
                                         inviter=self.user,
                                         pending=True)
        external_invite.save()

        self.assertEqual(external_invite.to_user_dict(), {
            'email': EXTERNAL_EMAIL,
            'username': EXTERNAL_EMAIL,
            'id': None,
            'job_title': None,
            'company': None,
            'avatar': '/static/img/mugpending.png',
            'first_name': None,
            'last_name': None,
            'pending': True,
            'is_paid': False,
            'had_trial': False,
            'is_super': False,
            'last_login': None,
            'date_joined': None,
            'tags': [],
            'keywords': [],
            'settings': mock.ANY
        })

        external_invite.pending = False
        external_invite.save()

        # pending in the user dict has nothing to do with the pending
        # on the external invite model. so it shouldn't be affected
        self.assertEqual(external_invite.to_user_dict(), {
            'email': EXTERNAL_EMAIL,
            'username': EXTERNAL_EMAIL,
            'id': None,
            'job_title': None,
            'company': None,
            'avatar': '/static/img/mugpending.png',
            'first_name': None,
            'last_name': None,
            'pending': True,
            'is_paid': False,
            'had_trial': False,
            'is_super': False,
            'last_login': None,
            'date_joined': None,
            'tags': [],
            'keywords': [],
            'settings': mock.ANY
        })

    def test_comment_parse_flow(self):
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        # Create the external invite
        external_invite = ExternalInvite(email='external@email.com',
                                         document=document,
                                         inviter=self.user,
                                         pending=True)
        external_invite.save()

        sentence = Sentence.objects.get(pk=document.sentences_pks[0])
        sentence.add_comment(self.user, '@[external@email.com](external@email.com) Yellow!!!')

        with mock.patch('core.tasks.parse_comments_on_external_invite_delete.delay') as patched_parse:
            # Create the user for the external invite
            user = User(username='external_guy', email='external@email.com')
            user.set_password('external')
            user.save()
            patched_parse.assert_called_once_with([document], user)

    def test_comment_parse_task(self):
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        # Create the external invite
        external_invite = ExternalInvite(email='external@email.com',
                                         document=document,
                                         inviter=self.user,
                                         pending=True)
        external_invite.save()

        sentence = Sentence.objects.get(pk=document.sentences_pks[0])
        sentence.add_comment(self.user, '@[external@email.com](external@email.com) Yellow!!!')

        with mock.patch('core.tasks.parse_comments_on_external_invite_delete.delay') as _:

            # Create the user for the external invite
            user = User(username='external_guy', email='external@email.com')
            user.set_password('external')
            user.save()

            with mock.patch('core.tasks.store_activity_notification.delay') as mock_activity_notification:
                # Run the actual task
                parse_comments_on_external_invite_delete([document], user)

                sentence = Sentence.objects.get(pk=document.sentences_pks[0])
                self.assertEqual(sentence.comments, {'comments': [
                    {'timestamp': mock.ANY,
                     'message': '@[external_guy](external@email.com) Yellow!!!',
                     'uuid': mock.ANY,
                     'author': self.user.username}]})

                mock_activity_notification.assert_called_once_with(
                    target=user,
                    transient=False,
                    actor=self.user,
                    verb='mentioned',
                    action_object=sentence,
                    recipient=user,
                    render_string='(actor) mentioned (target) in a comment on (action_object)',
                    created=mock.ANY)
