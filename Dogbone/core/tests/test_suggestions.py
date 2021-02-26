from core.models import CollaborationInvite
from dogbone.testing.base import BeagleWebTest


class SuggestionModelTest(BeagleWebTest):
    NEED_DEFAULT_USER = False

    def setUp(self):
        super(SuggestionModelTest, self).setUp()
        self.user = self.create_user()

    def test_no_collaborator(self):
        """
        Test that a user has a collaboration aggregate
        """

        self.assertEqual(self.user.collaborator_aggregate.get_suggestions(), [])

    def test_one_collaborator(self):
        """
        Test that a user that has a collaborator, finds that collaborator in the suggestion list
        """
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', self.user, pending=False)
        invite = CollaborationInvite(inviter=self.user, invitee=other_user, document=document)
        invite.save()

        self.assertEqual(self.user.collaborator_aggregate.get_suggestions(), [{'email': 'some@email.com'}])

    def test_one_collaborator_then_delete(self):
        """
        Test that if the user is no longer collaborating on a document with someone, it is still a suggestion
        """
        other_user = self.create_user('some@email.com', 'someusername', 'somepass')
        document = self.create_document('Title', self.user, pending=False)
        invite = CollaborationInvite(inviter=self.user, invitee=other_user, document=document)
        invite.save()
        self.assertEqual(self.user.collaborator_aggregate.get_suggestions(), [{'email': 'some@email.com'}])
        invite.delete()
        self.assertEqual(self.user.collaborator_aggregate.get_suggestions(), [{'email': 'some@email.com'}])

    def test_more_collaborators(self):
        other_user1 = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        other_user2 = self.create_user('some2@email.com', 'someusername2', 'somepass2')
        document1 = self.create_document('Title', self.user, pending=False)
        document2 = self.create_document('Title1', other_user2, pending=False)

        invite1 = CollaborationInvite(inviter=self.user, invitee=other_user1, document=document1)
        invite1.save()

        invite2 = CollaborationInvite(inviter=other_user2, invitee=self.user, document=document2)
        invite2.save()

        self.assertEqual({s['email'] for s in self.user.collaborator_aggregate.get_suggestions()},
                         {'some1@email.com', 'some2@email.com'})

    def test_same_collaborator(self):
        other_user = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        document1 = self.create_document('Title', self.user, pending=False)
        document2 = self.create_document('Title1', other_user, pending=False)

        invite1 = CollaborationInvite(inviter=self.user, invitee=other_user, document=document1)
        invite1.save()

        invite2 = CollaborationInvite(inviter=other_user, invitee=self.user, document=document2)
        invite2.save()

        self.assertEqual(self.user.collaborator_aggregate.get_suggestions(), [{'email': 'some1@email.com'}])

    def test_add_collaborator(self):
        other_user = self.create_user('some1@email.com', 'someusername1', 'somepass1')
        document = self.create_document('Title', self.user, pending=False)

        invite = CollaborationInvite(inviter=self.user, invitee=other_user, document=document)
        invite.save()

        self.user.collaborator_aggregate.add_collaborator('another@gmail.com')

        self.assertEqual(self.user.collaborator_aggregate.get_suggestions(), [{'email': 'some1@email.com'},
                                                                              {'email': 'another@gmail.com'}])
