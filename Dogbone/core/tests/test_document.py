import mock

from django.contrib.auth.models import User
from django.utils.timezone import now
from notifications.models import Notification

from core.models import (
    Document, CollaborationInvite, ExternalInvite,
    Sentence, SentenceAnnotations, UserLastViewDate
)
from dogbone.testing.base import BeagleWebTest


class DocumentTest(BeagleWebTest):

    def test_save(self):
        d = self.create_document(title='Some Document', owner=self.user)

        d = Document.objects.get(pk=d.pk)

        self.assertEqual(d.original_name, 'Some Document.pdf')
        self.assertEqual(d.title, 'Some Document')
        self.assertEqual(d.raw_text, 'Some Document Some Document')
        self.assertEqual(d.agreement_type, Document.GENERIC)
        self.assertIsNotNone(d.created)
        self.assertIsNotNone(d.modified)

        # Check if it has been processed
        self.assertEqual(d.pending, True)
        self.assertEqual(d.is_pending, True)
        self.assertEqual(d.is_ready, False)

        # Check that the UUID has been generated
        self.assertIsNotNone(d.uuid)

        # Check the owner
        self.assertEqual(d.owner, self.user)

    def test_to_dict(self):
        u = User(username='user', email='email@gmail.com')
        u.set_password('mypass')
        u.save()

        d = self.create_document(title='Some Document', owner=u)

        data = {
            'created': mock.ANY,
            'original_name': 'Some Document.pdf',
            'owner': {
                'avatar': mock.ANY,
                'email': u.email,
                'id': u.pk,
                'username': u.username,
                'job_title': mock.ANY,
                'company': mock.ANY,
                'first_name': mock.ANY,
                'last_name': mock.ANY,
                'tags': mock.ANY,
                'keywords': mock.ANY,
                'settings': mock.ANY,
                'pending': False,
                'is_paid': False,
                'had_trial': mock.ANY,
                'is_super': False,
                'date_joined': mock.ANY,
                'last_login': mock.ANY,
                'document_upload_count': 1,
                'phone': None,
            },
            'collaborators': [],
            'report_url': '/report/%s' % d.uuid,
            'title': 'Some Document',
            'url': '/api/v1/document/%s' % d.uuid,
            'is_initsample': False,
            'agreement_type': mock.ANY,
            'agreement_type_confidence': mock.ANY,
            'uuid': d.uuid,
            'status': 0,  # is still pending
            'failed': False,
            'document_id': d.id,
            'processing_begin_timestamp': mock.ANY,
            'processing_end_timestamp': mock.ANY,
        }

        self.assertEqual(d.to_dict(), data)

    def test_query_manager(self):
        d = self.create_document(title='Some Document', owner=self.user)

        self.assertEqual(list(Document.ready_objects.all()), [])
        self.assertEqual(list(Document.pending_objects.all()), [d])

    def test_lightweight_manager(self):
        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document(
            'My beautiful document', sentences, self.user
        )

        document.cached_analysis = {'aaaa': 'bbbb'}
        document.save()

        qs = Document.lightweight.all()

        self.assertNotIn('cached_analysis', str(qs.query))
        self.assertNotIn('sents', str(qs.query))
        self.assertEqual(len(qs), 1)
        self.assertEqual(qs[0].pk, document.pk)
        lightweight = qs[0]

        # Test that the cached_analysis field is loaded on request
        self.assertIsNotNone(lightweight.cached_analysis)

        # Check that it is loaded when we use the normal manager
        qs = Document.objects.all()
        self.assertIn('cached_analysis', str(qs.query))
        heavyweight = qs[0]
        self.assertIsNotNone(heavyweight.cached_analysis)

        # Test that the cached_analysis field is loaded on request
        self.assertIsNotNone(lightweight.sents)

        # Check that it is loaded when we use the normal manager
        qs = Document.objects.all()
        self.assertIn('sents', str(qs.query))
        heavyweight = qs[0]
        self.assertIsNotNone(heavyweight.sents)

    def test_aggregated_query_simple(self):
        """
        Test the documents owned by the user are retrieved
        """
        d1 = self.create_document(title='Some Document1', owner=self.user, pending=False)
        d2 = self.create_document(title='Some Document2', owner=self.user, pending=False)
        docs = Document.get_aggregated_documents(self.user)
        self.assertEqual([d2, d1], list(docs))

    def test_aggregated_query_invited(self):
        """
        Test that the documents on which the user is invited are retrieved
        """
        u = User(username='other', email='other@gmail.com')
        u.set_password('otherpass')
        u.save()

        d1 = self.create_document(title='Some Document1', owner=u, pending=False)
        d2 = self.create_document(title='Some Document2', owner=u, pending=False)

        CollaborationInvite(inviter=u, invitee=self.user, document=d1).save()
        CollaborationInvite(inviter=u, invitee=self.user, document=d2).save()

        docs = Document.get_aggregated_documents(self.user)
        self.assertEqual([d2, d1], list(docs))

    def test_aggregated_query_mixed(self):
        """
        Test that all the documents the user has access to are retrieved
        """
        u = User(username='other', email='other@gmail.com')
        u.set_password('otherpass')
        u.save()

        d1 = self.create_document(title='Some Document1', owner=u, pending=False)
        d2 = self.create_document(title='Some Document2', owner=self.user, pending=False)

        CollaborationInvite(inviter=u, invitee=self.user, document=d1).save()

        docs = Document.get_aggregated_documents(self.user)
        self.assertEqual([d2, d1], list(docs))

    def test_aggregated_query_mixed_not_trash(self):
        """
        Test that all the documents the user has access to are retrieved
        """
        u = User(username='other', email='other@gmail.com')
        u.set_password('otherpass')
        u.save()

        d1 = self.create_document(title='Some Document1', owner=u, pending=False)
        d2 = self.create_document(title='Some Document2', owner=self.user, pending=False)
        d3 = self.create_document(title='Some Document3', owner=self.user, pending=False)

        CollaborationInvite(inviter=u, invitee=self.user, document=d1).save()

        docs = Document.get_aggregated_documents(self.user)
        self.assertEqual([d3, d2, d1], list(docs))

        d3.delete()

        docs = Document.get_aggregated_documents(self.user)
        self.assertEqual([d2, d1], list(docs))

        d2.delete()

        docs = Document.get_aggregated_documents(self.user)
        self.assertEqual([d1], list(docs))

        d1.delete()

        docs = Document.get_aggregated_documents(self.user)
        self.assertEqual([], list(docs))

    def test_delete(self):
        u1 = User(username='other1', email='other1@gmail.com')
        u1.set_password('other1pass')
        u1.save()

        u2 = User(username='other2', email='other2@gmail.com')
        u2.set_password('other2pass')
        u2.save()

        d = self.create_document(title='Some Document', owner=self.user, pending=False)
        CollaborationInvite(invitee=u1, inviter=self.user, document=d).save()
        CollaborationInvite(invitee=u2, inviter=self.user, document=d).save()

        self.assertEqual(len(CollaborationInvite.objects.all()), 2)
        self.assertEqual(len(Document.objects.all()), 1)

        d.delete()
        self.assertEqual(d.trash, True)

        self.assertEqual(len(CollaborationInvite.objects.all()), 0)
        self.assertEqual(len(Document.objects.all()), 0)

    def test_delete_notifications(self):
        d = self.create_document(title='Some Document', owner=self.user, pending=False)

        Notification(actor=self.user, recipient=self.user, verb='uploaded', target=d).save()
        Notification(actor=self.user, recipient=self.user, verb='invited', target=self.user, action_object=d).save()

        self.assertEqual(len(Notification.objects.filter(recipient=self.user)), 2)
        d.delete()
        self.assertEqual(len(Notification.objects.filter(recipient=self.user)), 0)

    def test_delete_with_external(self):
        d = self.create_document(title='Some Document', owner=self.user, pending=False)
        ExternalInvite(email='aaaa@bbb.com', inviter=self.user, document=d).save()
        ExternalInvite(email='bbbb@aaa.com', inviter=self.user, document=d).save()

        self.assertEqual(len(ExternalInvite.objects.all()), 2)
        self.assertEqual(len(Document.objects.all()), 1)

        d.delete()
        self.assertEqual(d.trash, True)

        self.assertEqual(len(ExternalInvite.objects.all()), 0)
        self.assertEqual(len(Document.objects.all()), 0)

    @mock.patch('core.signals.document_owner_changed.send')
    def test_change_owner(self, mock_send):
        document = self.create_document(title='Some Document', owner=self.user, pending=False)
        other = User.objects.create(username='other1', email='other1@gmail.com', password='P@ss')

        old_owner = document.change_owner(other)

        mock_send.assert_called_once_with(after_owner=other, document=document, sender=Document, before_owner=self.user)
        self.assertEqual(old_owner, self.user)
        self.assertEqual(document.owner, other)

    def test_check_batch_owner(self):
        u1 = User(username='user1', email='email1@gmail.com')
        u1.set_password('mypass1')
        u1.save()

        batch = self.create_batch('Test documents batch', u1)
        d1 = self.create_document(title='Some Document #1', owner=u1, batch=batch)
        d2 = self.create_document(title='Some Document #2', owner=u1, batch=batch)

        u2 = User(username='user2', email='email2@gmail.com')
        u2.set_password('mypass2')
        u2.save()

        self.assertEqual(batch.owner.username, 'user1')

        d1.owner = u2
        d1.save()
        # Not all documents in batch have 'user2' owner
        self.assertEqual(batch.owner.username, 'user1')

        d2.owner = u2
        d2.save()
        # All documents in batch have 'user2' owner
        self.assertEqual(batch.owner.username, 'user2')


class DocumentDigestTestCase(BeagleWebTest):

    def test_simple_digest(self):
        sentences = ["I like flowers.", "I don't like butter."]
        document = self.create_analysed_document('My beautiful document',
                                                 sentences, self.user)

        s1model = Sentence.objects.get(pk=document.sentences_pks[0])

        s1model.add_tag(user=None, label='RESPONSIBILITY', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s1model.add_tag(user=None, label='TERMINATION', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s1model.add_tag(user=None, label='LIABILITY', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s1model.add_tag(user=self.user, label='wtf1', annotation_type=SentenceAnnotations.MANUAL_TAG_TYPE)

        s2model = Sentence.objects.get(pk=document.sentences_pks[1])

        s2model.add_tag(user=None, label='TERMINATION', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s2model.add_tag(user=None, label='LIABILITY', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s2model.add_tag(user=self.user, label='ol2', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        classifier_id=2)

        document = Document.objects.get(pk=document.pk)

        digest = document.digest()

        self.assertEqual(digest,
            {
                'annotations': [
                    {
                        'by_party': {'none': 2, 'them': 0, 'you': 0},
                        'display_plural': u'Liabilities',
                        'display_singular': u'Liability',
                        'label': u'LIABILITY',
                        'total': 2,
                        'clauses': [u"I like flowers.", u"I don't like butter."]
                    },

                    {
                        'by_party': {'none': 1, 'them': 0, 'you': 0},
                        'display_plural': u'Responsibilities',
                        'display_singular': u'Responsibility',
                        'label': u'RESPONSIBILITY',
                        'total': 1,
                        'clauses': [u"I like flowers."]
                    },

                    {
                        'by_party': {'none': 2, 'them': 0, 'you': 0},
                        'display_plural': u'Terminations',
                        'display_singular': u'Termination',
                        'label': u'TERMINATION',
                        'total': 2,
                        'clauses': [u"I like flowers.", u"I don't like butter."]
                    }

                ],
                'keywords': [],
                'learners': [
                    {
                        'classifier_id': 2,
                        'label': 'ol2',
                        'total': 1,
                        'clauses': [u"I don't like butter."]
                    }
                ],
                'experiments': [],
                'parties': {'you': u'', 'them': u''}
            }
        )

    def test_unicode_digest(self):
        sentences = [u"I like \u2013 flowers.", u"I don't like butter."]
        document = self.create_analysed_document(u'My \u2013 beautiful document',
                                                 sentences, self.user)

        s1model = Sentence.objects.get(pk=document.sentences_pks[0])

        s1model.add_tag(user=None, label='RESPONSIBILITY', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s1model.add_tag(user=None, label='TERMINATION', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s1model.add_tag(user=self.user, label='kw1', annotation_type=SentenceAnnotations.KEYWORD_TAG_TYPE)
        s1model.add_tag(user=self.user, label='wtf1', annotation_type=SentenceAnnotations.MANUAL_TAG_TYPE)
        s1model.add_tag(user=self.user, label='ol1', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        classifier_id=1)
        s1model.add_tag(user=self.user, label='ol3', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        classifier_id=3)
        s1model.add_tag(user=self.user, label='se1', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        experiment_uuid='qwerty1')
        s1model.add_tag(user=self.user, label='se3', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        experiment_uuid='qwerty3')

        s2model = Sentence.objects.get(pk=document.sentences_pks[1])

        s2model.add_tag(user=None, label='TERMINATION', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s2model.add_tag(user=None, label='LIABILITY', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s2model.add_tag(user=self.user, label='kw2', annotation_type=SentenceAnnotations.KEYWORD_TAG_TYPE)
        s2model.add_tag(user=self.user, label='wtf2', annotation_type=SentenceAnnotations.MANUAL_TAG_TYPE)
        s2model.add_tag(user=self.user, label='ol2', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        classifier_id=2)
        s2model.add_tag(user=self.user, label='ol3', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        classifier_id=3)
        s2model.add_tag(user=self.user, label='se2', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        experiment_uuid='qwerty2')
        s2model.add_tag(user=self.user, label='se3', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        experiment_uuid='qwerty3')

        document = Document.objects.get(pk=document.pk)

        digest = document.digest()

        self.assertEqual(digest,
            {
                'annotations': [
                    {
                        'by_party': {'none': 1, 'them': 0, 'you': 0},
                        'display_plural': u'Liabilities',
                        'display_singular': u'Liability',
                        'label': u'LIABILITY',
                        'total': 1,
                        'clauses': [u"I don't like butter."]
                    },

                    {
                        'by_party': {'none': 1, 'them': 0, 'you': 0},
                        'display_plural': u'Responsibilities',
                        'display_singular': u'Responsibility',
                        'label': u'RESPONSIBILITY',
                        'total': 1,
                        'clauses': [u"I like \u2013 flowers."]
                    },

                    {
                        'by_party': {'none': 2, 'them': 0, 'you': 0},
                        'display_plural': u'Terminations',
                        'display_singular': u'Termination',
                        'label': u'TERMINATION',
                        'total': 2,
                        'clauses': [u"I like \u2013 flowers.", u"I don't like butter."]
                    }
                ],
                'keywords': [
                     {
                        'label': u'kw1',
                        'total': 1,
                        'clauses': [u'I like \u2013 flowers.']
                     },

                    {
                        'label': u'kw2',
                        'total': 1,
                        'clauses': [u"I don't like butter."]
                    }
                 ],
                'learners': [
                    {
                        'classifier_id': 3,
                        'label': 'ol3',
                        'total': 2,
                        'clauses': [u"I like \u2013 flowers.", u"I don't like butter."]
                    },

                    {
                        'classifier_id': 1,
                        'label': 'ol1',
                        'total': 1,
                        'clauses': [u"I like \u2013 flowers."]
                    },

                    {
                        'classifier_id': 2,
                        'label': 'ol2',
                        'total': 1,
                        'clauses': [u"I don't like butter."]
                    }
                ],
                'experiments': [
                    {
                        'experiment_uuid': 'qwerty3',
                        'label': 'se3',
                        'total': 2,
                        'clauses': [u"I like \u2013 flowers.", u"I don't like butter."]
                    },

                    {
                        'experiment_uuid': 'qwerty1',
                        'label': 'se1',
                        'total': 1,
                        'clauses': [u"I like \u2013 flowers."]
                    },

                    {
                        'experiment_uuid': 'qwerty2',
                        'label': 'se2',
                        'total': 1,
                        'clauses': [u"I don't like butter."]
                    }
                ],
                'parties': {'you': u'', 'them': u''}
            }
        )

    def test_digest_with_parties(self):
        sentences = ["I like flowers.", "I don't like butter."]
        document = self.create_analysed_document('My beautiful document',
                                                 sentences, self.user)

        s1model = Sentence.objects.get(pk=document.sentences_pks[0])

        s1model.add_tag(user=None, label='RESPONSIBILITY', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE,
                        party='them')
        s1model.add_tag(user=None, label='TERMINATION', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE,
                        party='them')
        s1model.add_tag(user=None, label='LIABILITY', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE,
                        party='you')
        s1model.add_tag(user=self.user, label='se1', annotation_type=SentenceAnnotations.SUGGESTED_TAG_TYPE,
                        experiment_uuid='qwerty1')

        s2model = Sentence.objects.get(pk=document.sentences_pks[1])

        s2model.add_tag(user=None, label='TERMINATION', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE,
                        party='them')
        s2model.add_tag(user=None, label='LIABILITY', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE,
                        party='them')
        s2model.add_tag(user=self.user, label='wtf2', annotation_type=SentenceAnnotations.MANUAL_TAG_TYPE)

        document = Document.objects.get(pk=document.pk)
        digest = document.digest()

        self.assertEqual(digest,
            {
                'annotations': [
                    {
                        'by_party': {'none': 0, 'them': 1, 'you': 1},
                        'display_plural': u'Liabilities',
                        'display_singular': u'Liability',
                        'label': u'LIABILITY',
                        'total': 2,
                        'clauses': [u"I like flowers.", u"I don't like butter."]
                    },

                    {
                        'by_party': {'none': 0, 'them': 1, 'you': 0},
                        'display_plural': u'Responsibilities',
                        'display_singular': u'Responsibility',
                        'label': u'RESPONSIBILITY',
                        'total': 1,
                        'clauses': [u"I like flowers."]
                    },

                    {
                        'by_party': {'none': 0, 'them': 2, 'you': 0},
                        'display_plural': u'Terminations',
                        'display_singular': u'Termination',
                        'label': u'TERMINATION',
                        'total': 2,
                        'clauses': [u"I like flowers.", u"I don't like butter."]
                    }
                ],
                'keywords': [],
                'learners': [],
                'experiments': [
                    {
                        'experiment_uuid': 'qwerty1',
                        'label': 'se1',
                        'total': 1,
                        'clauses': [u"I like flowers."]
                    }
                ],
                'parties': {'you': u'', 'them': u''}
            }
        )

    def test_simple_digest_with_keywords(self):
        sentences = ["I like flowers.", "I don't like butter."]
        document = self.create_analysed_document('My beautiful document',
                                                 sentences, self.user)

        s1model = Sentence.objects.get(pk=document.sentences_pks[0])

        s1model.add_tag(user=None, label='RESPONSIBILITY', annotation_type=SentenceAnnotations.ANNOTATION_TAG_TYPE)
        s1model.add_tag(user=self.user, label='kw3', annotation_type=SentenceAnnotations.KEYWORD_TAG_TYPE)

        s2model = Sentence.objects.get(pk=document.sentences_pks[1])
        s2model.add_tag(user=self.user, label='kw2', annotation_type=SentenceAnnotations.KEYWORD_TAG_TYPE)
        s2model.add_tag(user=self.user, label='kw3', annotation_type=SentenceAnnotations.KEYWORD_TAG_TYPE)

        document = Document.objects.get(pk=document.pk)

        digest = document.digest()

        self.assertEqual(digest,
            {
                'annotations': [
                    {
                        'by_party': {'none': 0, 'them': 0, 'you': 0},
                        'display_plural': u'Liabilities',
                        'display_singular': u'Liability',
                        'label': u'LIABILITY',
                        'total': 0,
                        'clauses': []
                    },

                    {
                        'by_party': {'none': 1, 'them': 0, 'you': 0},
                        'display_plural': u'Responsibilities',
                        'display_singular': u'Responsibility',
                        'label': u'RESPONSIBILITY',
                        'total': 1,
                        'clauses': [u"I like flowers."]
                    },

                    {
                        'by_party': {'none': 0, 'them': 0, 'you': 0},
                        'display_plural': u'Terminations',
                        'display_singular': u'Termination',
                        'label': u'TERMINATION',
                        'total': 0,
                        'clauses': []
                    }
                ],
                'keywords': [
                     {
                        'label': u'kw3',
                        'total': 2,
                        'clauses': [u"I like flowers.", u"I don't like butter."]
                     },

                    {
                        'label': u'kw2',
                        'total': 1,
                        'clauses': [u"I don't like butter."]
                    }
                ],
                'learners': [],
                'experiments': [],
                'parties': {'you': u'', 'them': u''}
            }
        )


class UserLastViewDateTest(BeagleWebTest):

    def test_create_or_update(self):
        d = self.create_document('Title', self.user)
        time1 = now()
        time2 = now()

        UserLastViewDate.create_or_update(d, self.user, time1)
        viewdate = UserLastViewDate.objects.get(document = d, user = self.user)
        self.assertEqual(viewdate.date, time1)

        UserLastViewDate.create_or_update(d, self.user, time2)
        viewdate = UserLastViewDate.objects.get(document = d, user = self.user)
        self.assertEqual(viewdate.date, time2)
