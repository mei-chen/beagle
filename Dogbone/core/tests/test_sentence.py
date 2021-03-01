import mock

from core.models import Document, Sentence
from dogbone.testing.base import BeagleWebTest


class DocSentencesTest(BeagleWebTest):

    def setUp(self):
        super(DocSentencesTest, self).setUp()

        self.sents = ['Neither party will be responsible.',
                      'The roses are red between Company and You.',
                      'The violets are blue between Company and You.',
                      '']  # analyser also adds an empty sent at the end. Why?
        self.repl_sent = 'Either party will be responsible.'
        self.d = Document.objects.create(original_name='Magic Doc',
                                         title='Title',
                                         owner=self.user)
        self.d.init(self.sents, None, None)
        self.d.analyse()
        self.d.save()

    def test_doc_sents_creation(self):
        """ Checks that sentences are properly created on doc init """
        for i, sid in enumerate(self.d.sentences_ids):
            s = Sentence.objects.get(id=sid)
            self.assertEqual(s.text, self.sents[i])

    def test_sent_labels_extract(self):
        """ Checks an obvious sentence for labels """
        sid = self.d.sentences_ids[0]
        self.assertTrue(Sentence.objects.get(id=sid).annotations is not None)

    def test_sent_change_labels(self):
        """ Checks if sentence annotations manual change works properly """
        sid = self.d.sentences_ids[0]
        s = Sentence.objects.get(id=sid)
        dummy_annots = {'annotations': [{'label': 'UHUUU'}]}
        s2 = s.new_revision(self.user, annotations=dummy_annots)

        self.assertNotEqual(s.pk, s2.pk)
        self.assertEqual(s2.annotations, dummy_annots)

    def test_sent_change_text(self):
        """ Checks if sentence text manual change works properly """
        sid = self.d.sentences_ids[0]
        s = Sentence.objects.get(id=sid)
        s2 = s.new_revision(self.user, text=self.repl_sent)

        self.assertNotEqual(s.pk, s2.pk)
        self.assertEqual(s.annotations, s2.annotations)

    def test_sent_reject(self):
        """ Checks if rejected sentence behaves itself """
        sid = self.d.sentences_ids[0]
        s = Sentence.objects.get(id=sid)
        s2 = s.new_revision(self.user, text=self.repl_sent)
        self.assertNotEqual(s.pk, s2.pk)

        # Update the doc with the new revision
        self.d.update_sentence(s, s2)
        self.assertNotEqual(self.d.sentences_pks[0], s.pk)
        self.assertEqual(self.d.sentences_pks[0], s2.pk)

        # Reject the new revision
        s3 = s2.reject(self.user)
        self.d.update_sentence(s2, s3)
        self.assertNotEqual(self.d.sentences_pks[0], s2.pk)
        self.assertEqual(self.d.sentences_pks[0], s3.pk)
        self.assertEqual(s3.text, Sentence.objects.get(pk=self.d.sentences_pks[0]).text)
        self.assertEqual(s3.text, s.text)
        self.assertNotEqual(s3.text, s2.text)

    def test_sent_change_persists_in_document(self):
        """ Checks to ensure that when a sentence is changed, the document
        `sentences` property returns the latest sentence revision """
        sid = self.d.sentences_ids[0]
        s = Sentence.objects.get(id=sid)
        s2 = s.new_revision(self.user, text="cool new words")
        self.d.update_sentence(s, s2)
        ds_pk = self.d.sentences_pks[0]  # Document sentence primary key
        doc_sent = Sentence.objects.get(pk=ds_pk)

        # Sanity check: the new revision has the new text
        self.assertEqual(s2.text, "cool new words")
        # The test: does the document actually keep the new text
        self.assertEqual(doc_sent.text, "cool new words")

    def test_sent_change_text_reanalyze(self):
        """ Checks if sentence text manual change works properly """
        sid = self.d.sentences_ids[0]
        s = Sentence.objects.get(id=sid)
        s2 = s.new_revision(self.user, text=self.repl_sent, reanalyze=True)

        self.assertNotEqual(s.pk, s2.pk)
        self.assertNotEqual(s.annotations, s2.annotations)

    def test_sent_change_doc_cache_invalidation(self):
        """ Checks if sentence text manual change updates in the document """
        sid = self.d.sentences_ids[0]
        # Trigger cache creation
        self.d.analysis_result
        s = Sentence.objects.get(id=sid)
        s2 = s.new_revision(self.user, text=self.repl_sent)
        self.d.update_sentence(s, s2)

        self.assertNotEqual(s.pk, s2.pk)
        self.assertEqual(self.d.analysis_result['sentences'][0]['form'],
                         s2.text)

    def test_sent_history_walk(self):
        """ Checks if sentence history is properly created and persisted """
        sid = self.d.sentences_ids[0]
        s = Sentence.objects.get(id=sid)
        s2 = s.new_revision(self.user, text=self.repl_sent)

        self.assertEqual(s.pk, s2.prev_revision.pk)
        self.assertEqual(s.next_revision.pk, s2.pk)

    def test_online_learner(self):
        """ Testing that training online learner doesn't throw errors """
        from ml.facade import LearnerFacade
        from ml.capsules import Capsule
        sid = self.d.sentences_ids[0]
        s = Sentence.objects.get(id=sid)
        ps = self.d.get_parties()
        with mock.patch('ml.facade.TagLearner.load_models'):
            olearner = LearnerFacade.get_or_create('tagggg', self.user)
        with mock.patch('ml.facade.TagLearner.save_online_model'):
            olearner.train([Capsule(s.text, 0, parties=ps)], [True])

    def test_tags_persist_on_reject(self):
        """ Edit sentence, add tag, reject change, tag should persist """
        sid = self.d.sentences_ids[0]
        s = Sentence.objects.get(id=sid)
        s2 = s.new_revision(self.user, text=self.repl_sent)

        s2.add_tag(self.user, 'xxx')
        self.assertTrue('xxx' in [a['label'] for a in s2.annotations['annotations']])

        # Reject the new revision
        s3 = s2.reject(self.user)
        self.assertTrue('xxx' in [a['label'] for a in s3.annotations['annotations']])


class SentenceOperationsTest(BeagleWebTest):

    def setUp(self):
        super(SentenceOperationsTest, self).setUp()

        d = Document.objects.create(original_name='Magic Doc',
                                    title='Title',
                                    owner=self.user)
        d.init([' '], None, None)
        d.save()

        self.s = Sentence.objects.create(text='Sentence sentence sentence.',
                                         deleted=False,
                                         accepted=True,
                                         rejected=False,
                                         doc=d,
                                         modified_by=self.user)

    def test_clone(self):
        """ Checks the clone operation """
        o = self.s.clone()
        self.assertEqual(self.s.rejected, o.rejected)
        self.assertEqual(self.s.accepted, o.accepted)
        self.assertEqual(self.s.deleted, o.deleted)
        self.assertEqual(self.s.text, o.text)
        self.assertEqual(self.s.modified_by, o.modified_by)
        self.assertEqual(self.s.uuid, o.uuid)

    def test_gets_rejected(self):
        s = self.s.new_revision(self.user, text='New text')
        s = s.accept(self.user)
        s_chg = s.new_revision(self.user, text='Newest text')
        self.assertEqual(s_chg.reject(self.user).text, 'New text')

    def test_gets_accepted(self):
        self.assertTrue(self.s.accept(self.user).accepted)

    def test_gets_deleted(self):
        self.assertTrue(self.s.delete(self.user).deleted)

    def test_gets_undone(self):
        s = self.s.new_revision(self.user, text='New text')
        s_chg = s.new_revision(self.user, text='Newest text')
        s_undone = s_chg.undo(self.user)
        self.assertEqual(s_undone.text, 'New text')
        self.assertEqual(s_undone.undo(self.user).text, 'Newest text')

    def test_gets_liked(self):
        self.s.like(self.user)
        self.assertTrue(self.user.pk in self.s.likes['likes'])

    def test_gets_disliked(self):
        self.s.dislike(self.user)
        self.assertTrue(self.user.pk in self.s.likes['dislikes'])

    def test_muliple_likes_dislikes(self):
        self.s.like(self.user)
        self.assertTrue(self.user.pk in self.s.likes['likes'])
        self.s.dislike(self.user)
        self.assertFalse(self.user.pk in self.s.likes['likes'])
        self.assertTrue(self.user.pk in self.s.likes['dislikes'])
        self.s.like(self.user)
        self.s.like(self.user)
        self.s.like(self.user)
        self.s.dislike(self.user)
        self.assertFalse(self.user.pk in self.s.likes['likes'])
        self.assertTrue(self.user.pk in self.s.likes['dislikes'])

    def test_annotations(self):
        """ Add, remove, get annotations """
        def _get_labels(lst):
            return [a['label'] for a in lst]
        self.assertFalse(self.s.annotations)
        self.s.add_tag(self.user, 'tag1')
        self.s.add_tag(self.user, 'tag2')
        self.assertEqual(_get_labels(self.s.annotations['annotations']),
                         ['tag1', 'tag2'])
        self.s.remove_tag(self.user, 'tag2')
        self.assertEqual(_get_labels(self.s.annotations['annotations']),
                         ['tag1'])

    def test_comments(self):
        """ Add, remove, get comments """
        self.assertFalse(self.s.comments)
        self.s.add_comment(self.user, 'comment1')
        self.s.add_comment(self.user, 'comment2')
        comments = self.s.comments['comments']
        get_comm_msg = lambda c: c['message']
        self.assertEqual(map(get_comm_msg, comments), ['comment2', 'comment1'])
        self.s.remove_comment(self.user, comments[1]['uuid'])
        self.assertEqual(map(get_comm_msg, self.s.comments['comments']), ['comment2'])

    def test_new_version(self):
        """ Checks how many versions are present after a few operations """
        s = self.s
        uuid = s.uuid
        s = s.new_revision(self.user, text='New sentence sentence.')
        s = s.new_revision(self.user, text='New sentence sentence sentence.')
        s = s.new_revision(self.user, text='New sentence sentence sentence sentence.')
        s.reject(self.user)
        self.assertEqual(len(Sentence.objects.filter(uuid=uuid)), 5)
