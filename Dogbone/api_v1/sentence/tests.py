import json
import mock
from django.urls import reverse
from dogbone.testing.base import BeagleWebTest, MultiUserBeagleWebTest
from core.models import Sentence, Document, CollaborationInvite
from api_v1.sentence.endpoints import SentenceAnnotations


class SentenceDetailViewTest(BeagleWebTest):

    def test_get(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        for s_idx in range(len(sentences)):
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx],
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'lock': None,
                                    'accepted': True})

    def test_put(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        uuid = document.uuid
        for s_idx in range(len(sentences)):
            document = Document.objects.get(uuid=uuid)
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx],
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'lock': None,
                                    'accepted': True})

            response = self.client.put(url, data=json.dumps({
                'text': sentences[s_idx] + ' TESTING123'
            }), content_type='application/json')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.content)
            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx] + ' TESTING123',
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'lock': None,
                                    'accepted': False,
                                    'latestRevision': mock.ANY})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx] + ' TESTING123',
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'lock': None,
                                    'accepted': False,
                                    'latestRevision': mock.ANY})

        self.assertEqual(len(Sentence.objects.all()), 4)

    def test_multiple_fields_put(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        uuid = document.uuid
        for s_idx in range(len(sentences)):
            document = Document.objects.get(uuid=uuid)
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx],
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'lock': None,
                                    'accepted': True})

            response = self.client.put(url, data=json.dumps({
                'annotations': {'annotations': [{'label': 'A LABEL'}]}
            }), content_type='application/json')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.content)

            self.assertEqual([a['label'] for a in data['annotations']],
                             ['A LABEL'])

            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual([a['label'] for a in data['annotations']],
                             ['A LABEL'])

        self.assertEqual(len(Sentence.objects.all()), 4)

    def test_empty_put(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        uuid = document.uuid
        for s_idx in range(len(sentences)):
            document = Document.objects.get(uuid=uuid)
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx],
                                    'likes': None,
                                    'lock': None,
                                    'style': None,
                                    'newlines': 0,
                                    'comments': None,
                                    'comments_count': 0,
                                    'accepted': True})

            response = self.client.put(url, data=json.dumps({}), content_type='application/json')
            self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Sentence.objects.all()), 2)

    def test_forbidden_fields_put(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        uuid = document.uuid
        for s_idx in range(len(sentences)):
            document = Document.objects.get(uuid=uuid)
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx],
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'lock': None,
                                    'accepted': True})

            response = self.client.put(url, data=json.dumps({'rejected': True}), content_type='application/json')
            self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Sentence.objects.all()), 2)

    def test_delete(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['Anna has apples.', 'Mary has melons!']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        for s_idx in range(len(sentences)):
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': True,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx],
                                    'lock': None,
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'accepted': False,
                                    'latestRevision': mock.ANY})

    def test_not_access(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences,
                                                 self.create_user('some@email.com', 'someusername', 'somepass'))

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_document_404(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('sentence_detail_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_sentence_404(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_not_access(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences,
                                                 self.create_user('some@email.com', 'someusername', 'somepass'))

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_document_404(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('sentence_detail_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_sentence_404(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)


class SentenceAcceptViewTest(BeagleWebTest):

    def test_post(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        # Now reject the sentences
        for sentence_pk in document.sentences_pks:
            sentence = Sentence.objects.get(pk=sentence_pk)
            sentence.accepted = False
            sentence.save()

        for s_idx in range(len(sentences)):
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx],
                                    'lock': None,
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'accepted': False})
            # don't expect `latestRevision` since the sentence was rejected by
            # manually flipping the `accepted` flag. There is no revision prior
            # to this initial one, so `latestRevision` is not a field.

            url = reverse('sentence_accept_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.post(url)
            data = json.loads(response.content)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx],
                                    'lock': None,
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'accepted': True})

    def test_not_access(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences,
                                                 self.create_user('some@email.com', 'someusername', 'somepass'))

        url = reverse('sentence_accept_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_document_404(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('sentence_accept_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_sentence_404(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        url = reverse('sentence_accept_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class SentenceUndoViewTest(BeagleWebTest):

    def test_post(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        # Init the sentences as not accepted
        for sentence_pk in document.sentences_pks:
            sentence = Sentence.objects.get(pk=sentence_pk)
            sentence.accepted = False
            sentence.save()
        # Modify the sentences
        for s_idx in range(len(sentences)):
            url = reverse('sentence_accept_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.post(url)
            data = json.loads(response.content)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data, {'modified_by': self.DUMMY_USERNAME,
                                    'uuid': mock.ANY,
                                    'deleted': False,
                                    'doc': document.uuid,
                                    'annotations': None,
                                    'rejected': False,
                                    'external_refs': [],
                                    'form': sentences[s_idx],
                                    'lock': None,
                                    'likes': None,
                                    'comments': None,
                                    'comments_count': 0,
                                    'style': None,
                                    'newlines': 0,
                                    'accepted': True})

            # Try to undo all
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['accepted'])

            url = reverse('sentence_undo_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.post(url)
            data = json.loads(response.content)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(data['accepted'])

            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertFalse(data['accepted'])

    def test_not_access(self):
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences,
                                                 self.create_user('some@email.com', 'someusername', 'somepass'))

        url = reverse('sentence_undo_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_document_404(self):
        self.login()
        url = reverse('sentence_undo_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_sentence_404(self):
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        url = reverse('sentence_undo_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class SentenceTagsViewTest(BeagleWebTest):

    def _get_labels(self, lst):
        return [a['label'] for a in lst]

    def test_post(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        # Set of tags initially void
        for s_idx in range(len(sentences)):
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertFalse(data['annotations'])

        # Add tag1
        url = reverse('sentence_tags_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        data = json.dumps({'tag': 'tag1'})
        response = self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Add tag2
        data = json.dumps({'tag': 'tag2'})
        response = self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._get_labels(data['annotations']), ['tag1', 'tag2'])

        # Delete tag1
        url = reverse('sentence_tags_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        data = json.dumps({'tag': 'tag1'})
        response = self.client.delete(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._get_labels(data['annotations']), ['tag2'])

        url = reverse('document_detail_view', kwargs={'uuid': document.uuid})
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._get_labels(data['analysis']['sentences'][1]['annotations']),
                         ['tag2'])

    def test_not_access(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences,
                                                 self.create_user('some@email.com', 'someusername', 'somepass'))

        url = reverse('sentence_tags_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_document_404(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('sentence_tags_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_sentence_404(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        url = reverse('sentence_tags_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class SentenceSuggestedTagsViewTest(BeagleWebTest):

    def _get_labels(self, lst):
        return [a['label'] for a in lst]

    def test_post(self):
        self.make_paid(self.user)
        self.login()
        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        # Set of suggested tags initially void
        for s_idx in range(len(sentences)):
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertFalse(data['annotations'])

        # Add tag1
        url = reverse('sentence_sugg_tags_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        data = json.dumps({'tag': 'tag1'})
        response = self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Add tag2
        data = json.dumps({'tag': 'tag2'})
        response = self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._get_labels(data['annotations']), ['tag1', 'tag2'])

        # Delete tag1
        url = reverse('sentence_sugg_tags_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        data = json.dumps({'tag': 'tag1'})
        response = self.client.delete(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._get_labels(data['annotations']), ['tag2'])

        url = reverse('document_detail_view', kwargs={'uuid': document.uuid})
        response = self.client.get(url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._get_labels(data['analysis']['sentences'][1]['annotations']), ['tag2'])

    def test_put(self):
        self.make_paid(self.user)
        self.login()
        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        # Set of suggested tags initially void
        for s_idx in range(len(sentences)):
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertFalse(data['annotations'])

        # Add tag1
        url = reverse('sentence_sugg_tags_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        data = json.dumps({'tag': 'our suggested tag'})
        response = self.client.post(url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Assert sentence 1 has suggested tag
        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse([a for a in data['annotations'] if a['approved']])
        self.assertIn('our suggested tag', self._get_labels(data['annotations']))

        # Perform the PUT (approve suggested tag as a real tag)
        url = reverse('sentence_sugg_tags_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        put_data = json.dumps({'tag': 'our suggested tag'})
        response = self.client.put(url, data=put_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Verify the sentence tags are as they should be
        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # the suggested tag is now an approved tag
        self.assertIn('our suggested tag', [a['label'] for a in data['annotations'] if a['approved']])
        # there are no suggested tags
        self.assertFalse([a['label'] for a in data['annotations'] if not a['approved']])

    def test_not_access(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences,
                                                 self.create_user('some@email.com', 'someusername', 'somepass'))

        url = reverse('sentence_sugg_tags_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_document_404(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('sentence_sugg_tags_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_sentence_404(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        url = reverse('sentence_sugg_tags_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class SentenceBulkTagsViewTest(BeagleWebTest):

    def test_post(self):
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        url = reverse('sentence_bulk_tags_view', kwargs={'uuid': document.uuid})

        get_labels_fn = lambda lst: [x['label'] for x in lst]

        data = {'sentences': [
            {'sentenceIdx': 1, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
            {'sentenceIdx': 5, 'annotations': [{'label': 'cheesy'}]},
            {'sentenceIdx': 7, 'annotations': [{'label': 'desperate'}, {'label': 'cry_baby'}]},
        ]}

        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(json.loads(response.content), data)

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(get_labels_fn(data['annotations']), ['childhood', 'cry_baby'])

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 5})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(get_labels_fn(data['annotations']), ['cheesy'])

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 7})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(get_labels_fn(data['annotations']), ['desperate', 'cry_baby'])

    def test_post_out_of_range(self):
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        url = reverse('sentence_bulk_tags_view', kwargs={'uuid': document.uuid})

        data = {'sentences': [
            {'sentenceIdx': 8, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
            {'sentenceIdx': 10, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
            {'sentenceIdx': 100, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
        ]}

        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(json.loads(response.content), {'sentences': []})

    def test_delete(self):
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        url = reverse('sentence_bulk_tags_view', kwargs={'uuid': document.uuid})

        data = {'sentences': [
            {'sentenceIdx': 3, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
            {'sentenceIdx': 2, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
            {'sentenceIdx': 5, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
        ]}

        self.client.post(url, json.dumps(data), content_type='application/json')

        data = {'sentences': [
            {'sentenceIdx': 3, 'annotations': [{'label': 'childhood'}]},
            {'sentenceIdx': 2, 'annotations': [{'label': 'cry_baby'}]},
            {'sentenceIdx': 5, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
        ]}

        response = self.client.delete(url, json.dumps(data), content_type='application/json')

        self.assertEqual(json.loads(response.content), data)

    def test_put(self):
        """ i.e. approve suggested tags """
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        url = reverse('sentence_bulk_tags_view', kwargs={'uuid': document.uuid})

        data = {'sentences': [
            {'sentenceIdx': 3,
             'annotations': [
                 {
                     'label': 'childhood',
                     'type': SentenceAnnotations.SUGGESTED_TAG_TYPE,
                     'approved': False
                 },
                 {
                     'label': 'cry_baby',
                     'type': SentenceAnnotations.SUGGESTED_TAG_TYPE,
                     'approved': False
                 }]
            },
            {'sentenceIdx': 2,
             'annotations': [
                 {
                     'label': 'childhood',
                     'type': SentenceAnnotations.SUGGESTED_TAG_TYPE,
                     'approved': False
                 },
                 {
                     'label': 'cry_baby',
                     'type': SentenceAnnotations.SUGGESTED_TAG_TYPE,
                     'approved': False
                 }]
            },
            {'sentenceIdx': 5,
             'annotations': [
                 {
                     'label': 'childhood',
                     'type': SentenceAnnotations.SUGGESTED_TAG_TYPE,
                     'approved': False
                 },
                 {
                     'label': 'cry_baby',
                     'type': SentenceAnnotations.SUGGESTED_TAG_TYPE,
                     'approved': False
                 }]
            },
        ]}

        self.client.post(url, json.dumps(data), content_type='application/json')

        data = {'sentences': [
            {'sentenceIdx': 3, 'annotations': [{'label': 'childhood'}]},
            {'sentenceIdx': 2, 'annotations': [{'label': 'cry_baby'}]},
            {'sentenceIdx': 5, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
        ]}

        response = self.client.put(url, json.dumps(data), content_type='application/json')
        self.assertEqual(json.loads(response.content), data)

        label_approval_filter = lambda lst: [(x['label'], x['approved']) for x in lst]

        # Now check the details (approval status of tags)

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 3})
        response = self.client.get(url)
        data = json.loads(response.content)
        result1 = [
            ('cry_baby', False),
            ('childhood', True)
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(label_approval_filter(data['annotations']), result1)

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.get(url)
        data = json.loads(response.content)
        result2 = [
            ('childhood', False),
            ('cry_baby', True)
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(label_approval_filter(data['annotations']), result2)

        url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 5})
        response = self.client.get(url)
        data = json.loads(response.content)
        result3 = [
            ('childhood', True),
            ('cry_baby', True)
        ]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(label_approval_filter(data['annotations']), result3)

    def test_delete_inexistent_tags(self):
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        url = reverse('sentence_bulk_tags_view', kwargs={'uuid': document.uuid})

        data = {'sentences': [
            {'sentenceIdx': 3, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
            {'sentenceIdx': 2, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
            {'sentenceIdx': 5, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
        ]}

        self.client.post(url, json.dumps(data), content_type='application/json')

        data = {'sentences': [
            {'sentenceIdx': 3, 'annotations': [{'label': 'childhood'}]},
            {'sentenceIdx': 2, 'annotations': [{'label': 'xxx'}]},
            {'sentenceIdx': 5, 'annotations': [{'label': 'childhood'}, {'label': 'xxx'}]},
        ]}

        response = self.client.delete(url, json.dumps(data), content_type='application/json')

        self.assertEqual(json.loads(response.content), {'sentences': [
            {'sentenceIdx': 3, 'annotations': [{'label': 'childhood'}]},
            {'sentenceIdx': 2, 'annotations': []},
            {'sentenceIdx': 5, 'annotations': [{'label': 'childhood'}]},
        ]})

    def test_delete_out_of_range(self):
        self.login()

        sentences = ["She's got a smile it seems to me",
                     "Reminds me of childhood memories",
                     "Where everything",
                     "Was as fresh as the bright blue sky",
                     "Now and then when I see her face",
                     "She takes me away to that special place",
                     "And if I'd stare too long",
                     "I'd probably break down and cry"]

        document = self.create_analysed_document('Sweet Child O Mine', sentences, self.user)

        url = reverse('sentence_bulk_tags_view', kwargs={'uuid': document.uuid})

        data = {'sentences': [
            {'sentenceIdx': 3, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
            {'sentenceIdx': 2, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
            {'sentenceIdx': 5, 'annotations': [{'label': 'childhood'}, {'label': 'cry_baby'}]},
        ]}

        self.client.post(url, json.dumps(data), content_type='application/json')

        data = {'sentences': [
            {'sentenceIdx': 3, 'annotations': [{'label': 'childhood'}]},
            {'sentenceIdx': 13, 'annotations': [{'label': 'childhood'}]},
            {'sentenceIdx': 2, 'annotations': [{'label': 'xxx'}]},
            {'sentenceIdx': 8, 'annotations': [{'label': 'xxx'}]},
            {'sentenceIdx': 5, 'annotations': [{'label': 'childhood'}, {'label': 'xxx'}]},
        ]}

        response = self.client.delete(url, json.dumps(data), content_type='application/json')

        self.assertEqual(json.loads(response.content), {'sentences': [
            {'sentenceIdx': 3, 'annotations': [{'label': 'childhood'}]},
            {'sentenceIdx': 2, 'annotations': []},
            {'sentenceIdx': 5, 'annotations': [{'label': 'childhood'}]},
        ]})


class SentenceLikeViewTest(BeagleWebTest):

    def test_post(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        document_upload_count = self.user.details.document_upload_count

        # First check no likes are present
        for s_idx in range(len(sentences)):
            sentence = Sentence.objects.get(pk=document.sentences_pks[s_idx])
            self.assertFalse(sentence.likes)

        # Like the first sentence
        like_url = reverse('sentence_like_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(like_url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['likes'], {'likes': [{'username': self.DUMMY_USERNAME,
                                                    'first_name': None,
                                                    'last_name': None,
                                                    'is_super': False,
                                                    'is_paid': True,
                                                    'had_trial': mock.ANY,
                                                    'company': None,
                                                    'tags': [],
                                                    'keywords': [],
                                                    'settings': mock.ANY,
                                                    'email': self.DUMMY_EMAIL,
                                                    'last_login': mock.ANY,
                                                    'avatar': '/static/img/mug.png',
                                                    'job_title': None,
                                                    'id': mock.ANY,
                                                    'pending': False,
                                                    'date_joined': mock.ANY,
                                                    'document_upload_count': document_upload_count,
                                                    'phone': None}], 'dislikes': []})

        # Check the like persisted
        check_url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.get(check_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['likes'], {'likes': [{'username': self.DUMMY_USERNAME,
                                                    'first_name': None,
                                                    'last_name': None,
                                                    'is_super': False,
                                                    'is_paid': True,
                                                    'had_trial': mock.ANY,
                                                    'company': None,
                                                    'tags': mock.ANY,
                                                    'keywords': [],
                                                    'settings': mock.ANY,
                                                    'email': self.DUMMY_EMAIL,
                                                    'last_login': mock.ANY,
                                                    'avatar': '/static/img/mug.png',
                                                    'job_title': None,
                                                    'id': mock.ANY,
                                                    'pending': False,
                                                    'date_joined': mock.ANY,
                                                    'document_upload_count': document_upload_count,
                                                    'phone': None}], 'dislikes': []})

        # Check the second sentence is pristine
        check_url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        response = self.client.get(check_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['likes'])

    def test_toggle_like(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        document_upload_count = self.user.details.document_upload_count

        # First check no likes are present
        for s_idx in range(len(sentences)):
            sentence = Sentence.objects.get(pk=document.sentences_pks[s_idx])
            self.assertFalse(sentence.likes)

        # Like the first sentence
        like_url = reverse('sentence_like_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(like_url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['likes'], {'likes': [{'username': self.DUMMY_USERNAME,
                                                    'first_name': None,
                                                    'last_name': None,
                                                    'is_super': False,
                                                    'is_paid': True,
                                                    'had_trial': mock.ANY,
                                                    'company': None,
                                                    'email': self.DUMMY_EMAIL,
                                                    'last_login': mock.ANY,
                                                    'tags': mock.ANY,
                                                    'keywords': [],
                                                    'settings': mock.ANY,
                                                    'avatar': '/static/img/mug.png',
                                                    'job_title': None,
                                                    'id': mock.ANY,
                                                    'pending': False,
                                                    'date_joined': mock.ANY,
                                                    'document_upload_count': document_upload_count,
                                                    'phone': None}], 'dislikes': []})

        # Undo the like
        check_url = reverse('sentence_like_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.delete(check_url)
        self.assertEqual(response.status_code, 200)

        # Check the like went away
        check_url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.get(check_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['likes']['likes'])

    def test_not_access(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences,
                                                 self.create_user('some@email.com', 'someusername', 'somepass'))

        url = reverse('sentence_like_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_document_404(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('sentence_like_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_sentence_404(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        url = reverse('sentence_like_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class SentenceDislikeViewTest(BeagleWebTest):

    def test_post(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        document_upload_count = self.user.details.document_upload_count

        # First check no likes are present
        for s_idx in range(len(sentences)):
            sentence = Sentence.objects.get(pk=document.sentences_pks[s_idx])
            self.assertFalse(sentence.likes)

        # Dislike the first sentence
        dislike_url = reverse('sentence_dislike_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(dislike_url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['likes'], {
            'dislikes': [
                {'username': self.DUMMY_USERNAME,
                 'first_name': None,
                 'last_name': None,
                 'is_super': False,
                 'is_paid': True,
                 'had_trial': mock.ANY,
                 'company': None,
                 'tags': [],
                 'keywords': [],
                 'settings': mock.ANY,
                 'email': self.DUMMY_EMAIL,
                 'last_login': mock.ANY,
                 'avatar': '/static/img/mug.png',
                 'job_title': None,
                 'id': mock.ANY,
                 'pending': False,
                 'date_joined': mock.ANY,
                 'document_upload_count': document_upload_count,
                 'phone': None}
            ],
            'likes': []})

        # Check the dislike persisted
        check_url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.get(check_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['likes'], {
            'dislikes': [
                {'username': self.DUMMY_USERNAME,
                 'first_name': None,
                 'last_name': None,
                 'is_super': False,
                 'is_paid': True,
                 'had_trial': mock.ANY,
                 'company': None,
                 'tags': mock.ANY,
                 'keywords': [],
                 'settings': mock.ANY,
                 'email': self.DUMMY_EMAIL,
                 'last_login': mock.ANY,
                 'avatar': '/static/img/mug.png',
                 'job_title': None,
                 'id': mock.ANY,
                 'pending': False,
                 'date_joined': mock.ANY,
                 'document_upload_count': document_upload_count,
                 'phone': None}],
            'likes': []})

        # Check the second sentence is pristine
        check_url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 1})
        response = self.client.get(check_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['likes'])

    def test_toggle_dislike(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        document_upload_count = self.user.details.document_upload_count

        # First check no dislikes are present
        for s_idx in range(len(sentences)):
            sentence = Sentence.objects.get(pk=document.sentences_pks[s_idx])
            self.assertFalse(sentence.likes)

        # Dislike the first sentence
        like_url = reverse('sentence_dislike_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(like_url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['likes'], {
            'likes': [],
            'dislikes': [
                {'username': self.DUMMY_USERNAME,
                 'first_name': None,
                 'last_name': None,
                 'is_super': False,
                 'is_paid': True,
                 'had_trial': mock.ANY,
                 'company': None,
                 'tags': [],
                 'keywords': [],
                 'settings': mock.ANY,
                 'email': self.DUMMY_EMAIL,
                 'last_login': mock.ANY,
                 'avatar': '/static/img/mug.png',
                 'job_title': None,
                 'id': mock.ANY,
                 'pending': False,
                 'date_joined': mock.ANY,
                 'document_upload_count': document_upload_count,
                 'phone': None}]})

        # Undo the dislike
        check_url = reverse('sentence_dislike_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.delete(check_url)
        self.assertEqual(response.status_code, 200)

        # Check the dislike went away
        check_url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.get(check_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['likes']['dislikes'])

    def test_toggle(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        document_upload_count = self.user.details.document_upload_count

        # First check no likes are present
        sentence = Sentence.objects.get(pk=document.sentences_pks[0])
        self.assertFalse(sentence.likes)

        # Like the sentence
        like_url = reverse('sentence_like_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(like_url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['likes'], {
            'likes': [
                {'username': self.DUMMY_USERNAME,
                 'first_name': None,
                 'last_name': None,
                 'is_super': False,
                 'is_paid': True,
                 'had_trial': mock.ANY,
                 'company': None,
                 'tags': [],
                 'keywords': [],
                 'settings': mock.ANY,
                 'email': self.DUMMY_EMAIL,
                 'last_login': mock.ANY,
                 'avatar': '/static/img/mug.png',
                 'job_title': None,
                 'id': mock.ANY,
                 'pending': False,
                 'date_joined': mock.ANY,
                 'document_upload_count': document_upload_count,
                 'phone': None}],
            'dislikes': []})

        # Toggle liked sentence to dislike
        dislike_url = reverse('sentence_dislike_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(dislike_url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['likes'], {
            'dislikes': [
                {'username': self.DUMMY_USERNAME,
                 'first_name': None,
                 'last_name': None,
                 'is_super': False,
                 'is_paid': True,
                 'had_trial': mock.ANY,
                 'company': None,
                 'tags': mock.ANY,
                 'keywords': mock.ANY,
                 'settings': mock.ANY,
                 'email': self.DUMMY_EMAIL,
                 'last_login': mock.ANY,
                 'avatar': '/static/img/mug.png',
                 'job_title': None,
                 'id': mock.ANY,
                 'pending': False,
                 'date_joined': mock.ANY,
                 'document_upload_count': document_upload_count,
                 'phone': None}],
            'likes': []})

    def test_not_access(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences,
                                                 self.create_user('some@email.com', 'someusername', 'somepass'))

        url = reverse('sentence_dislike_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_document_404(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('sentence_dislike_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_sentence_404(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        url = reverse('sentence_dislike_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class SentenceRejectViewTest(BeagleWebTest):

    def test_post(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        for s_idx in range(len(sentences)):
            url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            self.assertEqual(data, {
                'form': sentences[s_idx],
                'annotations': None,
                'doc': document.uuid,
                'uuid': mock.ANY,
                'external_refs': [],
                'accepted': True,
                'deleted': False,
                'rejected': False,
                'modified_by': self.DUMMY_USERNAME,
                'likes': None,
                'comments': None,
                'comments_count': 0,
                'style': None,
                'newlines': 0,
                'lock': None,
            })

            # Save this data to compare
            original_sentence_data = data

            # Make a change
            response = self.client.put(url, data=json.dumps({'text': sentences[s_idx] + ' TESTING123'}),
                                       content_type='application/json')

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertNotEqual(data['form'], sentences[s_idx])

            # Reject the change
            url = reverse('sentence_reject_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
            response = self.client.post(url)
            data = json.loads(response.content)
            self.assertEqual(response.status_code, 200)

            # Because we have rejected this revision, we get back the previous version back
            self.assertEqual(data, original_sentence_data)

    def test_not_access(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences,
                                                 self.create_user('some@email.com', 'someusername', 'somepass'))

        url = reverse('sentence_reject_view', kwargs={'uuid': document.uuid, 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_document_404(self):
        self.make_paid(self.user)
        self.login()
        url = reverse('sentence_reject_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_sentence_404(self):
        self.make_paid(self.user)
        self.login()

        sentences = ['I like flowers.', 'I don\'t like butter.']
        document = self.create_analysed_document('My beautiful document', sentences, self.user)
        url = reverse('sentence_reject_view', kwargs={'uuid': document.uuid, 's_idx': 2})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class SentenceModifyAcceptRejectTest(BeagleWebTest):

    def get_url(self, view, document, sentence_idx):
        return reverse(view, kwargs={
            'uuid': document.uuid,
            's_idx': sentence_idx
        })

    def url_detail(self, document, sentence_idx):
        view = 'sentence_detail_view'
        return self.get_url(view, document, sentence_idx)

    def url_accept(self, document, sentence_idx):
        view = 'sentence_accept_view'
        return self.get_url(view, document, sentence_idx)

    def url_reject(self, document, sentence_idx):
        view = 'sentence_reject_view'
        return self.get_url(view, document, sentence_idx)

    def test_works_as_expected(self):
        self.make_paid(self.user)
        self.login()
        the_sentences = ["Je suis francais.", "J'aime baguettes."]
        document = self.create_analysed_document("About the french", the_sentences, self.user)
        idx = 0

        # initially the sentence is as expected
        url = self.url_detail(document, idx)
        resp = self.client.get(url)
        data = json.loads(resp.content)
        self.assertTrue(data['accepted'])
        self.assertEqual(data['form'], "Je suis francais.")

        # change the sentence
        url = self.url_detail(document, idx)
        req_data = {'text': "Je ne parle pas francais."}
        resp = self.client.put(url, json.dumps(req_data))
        data = json.loads(resp.content)
        self.assertFalse(data['accepted'])
        self.assertEqual(data['form'], "Je ne parle pas francais.")
        self.assertIsNotNone(data.get('latestRevision'))

        # reject the sentence
        url = self.url_reject(document, idx)
        resp = self.client.post(url)
        data = json.loads(resp.content)
        self.assertTrue(data['accepted'])
        self.assertEqual(data['form'], "Je suis francais.")


class SentenceLockDetailViewTest(MultiUserBeagleWebTest):

    @classmethod
    def setUpClass(cls):
        super(SentenceLockDetailViewTest, cls).setUpClass()

        cls.sentences = ["I like flowers.", "I don't like butter."]
        cls.document = cls.create_analysed_document(
            'My beautiful document', cls.sentences, cls.user
        )
        CollaborationInvite(
            document=cls.document, inviter=cls.user, invitee=cls.user2
        ).save()

    def get_url(self, s_idx):
        return reverse('sentence_lock_detail_view', kwargs={
            'uuid': self.document.uuid,
            's_idx': s_idx
        })

    def test_get(self):
        self.make_paid(self.user)
        self.login()
        document = self.document
        sentences = self.sentences

        for s_idx in range(len(sentences)):
            url = self.get_url(s_idx)
            # test that the GET response looks ok
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {
                'isLocked': False,
                'docUUID': document.uuid,
                'sentence': mock.ANY,
                'owner': None,
                'sentenceIdx': s_idx
            })

    def test_put(self):
        self.make_paid(self.user)
        self.login()
        document = self.document
        sentences = self.sentences
        for s_idx in range(len(sentences)):
            url = self.get_url(s_idx)

            # test that GET shows us that no lock is held
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {
                'docUUID': document.uuid,
                'isLocked': False,
                'sentence': mock.ANY,
                'sentenceIdx': s_idx,
                'owner': None
            })

            # test that PUT gets us a lock if it is not held
            put_response = self.client.put(url)
            self.assertEqual(put_response.status_code, 200)
            data = json.loads(put_response.content)
            self.assertIsNotNone(data['owner'])
            self.assertEqual(data['owner']['email'], self.user.email)
            self.assertEqual(data, {
                'success': True, # isLocked is for the GET
                'docUUID': document.uuid,
                'sentence': mock.ANY,
                'sentenceIdx': s_idx,
                'owner': mock.ANY
            })

            # test that GET shows the lock is held by us
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertIsNotNone(data['owner'])
            self.assertEqual(data['owner']['email'], self.user.email)
            self.assertEqual(data, {
                'docUUID': document.uuid,
                'isLocked': True,
                'sentence': mock.ANY,
                'sentenceIdx': s_idx,
                'owner': mock.ANY
            })

    def test_delete(self):
        self.make_paid(self.user)
        self.login()
        document = self.document
        sentences = self.sentences
        for s_idx in range(len(sentences)):
            url = self.get_url(s_idx)

            # acquiring a lock (PUT) succeeds
            response = self.client.put(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {
                'success': True,
                'docUUID': document.uuid,
                'sentence': mock.ANY,
                'sentenceIdx': s_idx,
                'owner': mock.ANY
            })
            self.assertEqual(data['owner']['email'], self.user.email)

            # DELETE the lock succeeds
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {
                'success': True,
                'docUUID': document.uuid,
                'sentence': mock.ANY,
                'sentenceIdx': s_idx,
                'owner': None
            })

    def test_reacquire_success_returns_lock(self):
        self.make_paid(self.user)
        self.login()
        document = self.document
        sentences = self.sentences
        for s_idx in range(len(sentences)):
            url = self.get_url(s_idx)

            # PUT the lock succeeds
            response = self.client.put(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {
                'docUUID': document.uuid,
                'success': True,
                'sentence': mock.ANY,
                'sentenceIdx': s_idx,
                'owner': mock.ANY
            })
            self.assertEqual(data['owner']['email'], self.user.email)

            # trying to PUT again will fail with an informative response
            response = self.client.put(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
            self.assertEqual(data['docUUID'], document.uuid)
            self.assertEqual(data['sentenceIdx'], s_idx)
            self.assertIsNotNone(data['owner'])
            self.assertEqual(data['owner']['email'], self.user.email)

    def test_release_when_not_held_fails(self):
        self.make_paid(self.user)
        self.login()
        document = self.document
        sentences = self.sentences
        for s_idx in range(len(sentences)):
            url = self.get_url(s_idx)

            # GET the lock demonstrates it is not held
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data, {
                'isLocked': False,
                'docUUID': document.uuid,
                'sentence': mock.ANY,
                'sentenceIdx': s_idx,
                'owner': None
            })

            # trying to DELETE will fail with an informative response
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 403)
            data = json.loads(response.content)
            self.assertFalse(data['success'])
            self.assertIsNotNone(data['error'])
            self.assertEqual(data['http_status'], response.status_code) # 403
            self.assertIsNone(data['owner'])
            self.assertEqual(data['docUUID'], document.uuid)
            self.assertEqual(data['sentenceIdx'], s_idx)

    def test_one_put_at_a_time(self):
        self.make_paid(self.user)
        self.login()
        self.login_user2()

        user1 = self.user
        client1 = self.client
        client2 = self.client2

        # try locks on sentence idx = 0
        url = self.get_url(0)

        # no lock is initially held
        resp = client1.get(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['isLocked'], False)

        # user 1 PUTs a lock
        resp = client1.put(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['owner']['email'], user1.email)

        # user 2 PUTs the same lock
        resp = client2.put(url)
        self.assertEqual(resp.status_code, 403)
        data = json.loads(resp.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['owner']['email'], user1.email)

    def test_delete_works_only_for_own_locks(self):
        self.make_paid(self.user)
        self.login()
        self.login_user2()

        user1 = self.user
        client1 = self.client
        client2 = self.client2

        url = self.get_url(0)

        # no lock is initially held
        resp = client1.get(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['isLocked'], False)

        # user 1 PUTs a lock
        resp = client1.put(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['success'], True)

        # user 2 fails to DELETE the lock
        resp = client2.delete(url)
        self.assertEqual(resp.status_code, 403)
        data = json.loads(resp.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['owner']['email'], user1.email)

        # user 1 can successfully DELETE the lock
        resp = client1.delete(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['owner'], None)


class SentenceCommentsListViewTest(BeagleWebTest):
    def test_200(self):
        self.make_paid(self.user)
        self.sentences = ['I like flowers.', 'I don\'t like butter.']
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )

        self.login()

        url = reverse('sentence_comments_list_view', kwargs={'uuid': self.document.uuid, 's_idx': 0})
        result = self.client.get(url)
        data = json.loads(result.content)
        self.assertEqual(data, {"objects": []})

        sentence_pk = self.document.sentences_pks[0]
        sentence = Sentence.objects.get(pk=sentence_pk)
        sentence.add_comment(self.user, "Ana are mere mari")
        sentence.add_comment(self.user, "Ala bala portocala")
        sentence.add_comment(self.user, "123 cine striga hey!")

        result = self.client.get(url)
        data = json.loads(result.content)

        self.assertEqual(data, {
            'objects': [
                {
                    'author': mock.ANY,
                    'message': u'Ana are mere mari',
                    'timestamp': mock.ANY,
                    'uuid': mock.ANY
                },
                {
                    'author': mock.ANY,
                    'message': u'Ala bala portocala',
                    'timestamp': mock.ANY,
                    'uuid': mock.ANY
                },
                {
                    'author': mock.ANY,
                    'message': u'123 cine striga hey!',
                    'timestamp': mock.ANY,
                    'uuid': mock.ANY
                }
            ]
        })

    def test_paginated(self):
        self.make_paid(self.user)
        self.sentences = ["I like flowers.", "I don't like butter."]
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )

        self.login()

        url = reverse('sentence_comments_list_view', kwargs={'uuid': self.document.uuid, 's_idx': 0})
        result = self.client.get(url)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.content)
        self.assertEqual(data, {"objects": []})

        sentence_pk = self.document.sentences_pks[0]
        sentence = Sentence.objects.get(pk=sentence_pk)

        for i in range(20):
            sentence.add_comment(self.user, 'comments %s' % i)

        result = self.client.get(url + '?page=0')
        data = json.loads(result.content)
        expected_comments = ['comments 15', 'comments 16', 'comments 17', 'comments 18', 'comments 19']
        self.assertEqual(expected_comments, [c['message'] for c in data['objects']])

        result = self.client.get(url + '?page=1')
        data = json.loads(result.content)
        expected_comments = ['comments 10', 'comments 11', 'comments 12', 'comments 13', 'comments 14']
        self.assertEqual(expected_comments, [c['message'] for c in data['objects']])

        result = self.client.get(url + '?page=20')
        data = json.loads(result.content)
        self.assertEqual(data, {'objects': []})

    def test_initial_page(self):
        """
        The first page of comments should be included as 'comments' in the
        sentence structure returned by sentence_detail_view
        """
        self.make_paid(self.user)
        self.login()

        sentences = ["I like lowers.", "I don't like utter."]
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        s_idx = 0
        get_url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
        response = self.client.get(get_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertFalse(data['comments'])

        # Add 10 comments
        sentence_pk = document.sentences_pks[s_idx]
        sentence = Sentence.objects.get(pk=sentence_pk)

        gen_comms = ['comments %s' % i for i in range(10)]
        for c in gen_comms:
            sentence.add_comment(self.user, c)

        # Check again the sentence structure
        response = self.client.get(get_url)
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        gen_comms.reverse()
        comm_msg = lambda c: c['message']

        # Because we have rejected this revision, we get back the previous version back
        self.assertEqual(list(map(comm_msg, data['comments'])), gen_comms[:5])

    def test_delete(self):
        self.make_paid(self.user)
        self.login()

        sentences = ["Anna has apples.", "Mary has melons!"]
        document = self.create_analysed_document('My beautiful document', sentences, self.user)

        s_idx = 0
        sentence_pk = document.sentences_pks[s_idx]
        sentence = Sentence.objects.get(pk=sentence_pk)

        comm = sentence.add_comment(self.user, "Fane tractoristu")

        url = reverse('sentence_comments_list_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
        data = {'comment_uuid': comm['uuid']}
        response = self.client.delete(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        get_url = reverse('sentence_detail_view', kwargs={'uuid': document.uuid, 's_idx': s_idx})
        response = self.client.get(get_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertFalse(data['comments'])

    def test_403(self):
        self.make_paid(self.user)
        self.sentences = ["I like flowers.", "I don't like butter."]
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )
        url = reverse('sentence_comments_list_view', kwargs={'uuid': self.document.uuid, 's_idx': 0})
        result = self.client.get(url)

        self.assertEqual(result.status_code, 403)

    def test_404_document(self):
        self.make_paid(self.user)
        self.login()
        self.sentences = ["I like flowers.", "I don't like butter."]
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )
        url = reverse('sentence_comments_list_view', kwargs={'uuid': 'aaaaaaa', 's_idx': 0})
        result = self.client.get(url)

        self.assertEqual(result.status_code, 404)

    def test_404_sentence(self):
        self.make_paid(self.user)
        self.login()
        self.sentences = ["I like flowers.", "I don't like butter."]
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )
        url = reverse('sentence_comments_list_view', kwargs={'uuid': self.document.uuid, 's_idx': 10})
        result = self.client.get(url)

        self.assertEqual(result.status_code, 404)

    def test_post_single_comment(self):
        self.make_paid(self.user)
        self.login()
        self.sentences = ["I like flowers.", "I don't like butter."]
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )
        url = reverse('sentence_comments_list_view', kwargs={'uuid': self.document.uuid, 's_idx': 0})
        data = {'message': 'Awesome!'}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'objects': [{'author': mock.ANY,
                                             'message': u'Awesome!',
                                             'timestamp': mock.ANY,
                                             'uuid': mock.ANY}]})

    def test_post_multiple_comments(self):
        self.make_paid(self.user)
        self.login()
        self.sentences = ["I like flowers.", "I don't like butter."]
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )
        url = reverse('sentence_comments_list_view', kwargs={'uuid': self.document.uuid, 's_idx': 1})
        data = [{'message': 'Awesome!'}, {'message': 'Even more awesome?!'}]
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'objects': [{'author': mock.ANY,
                                             'message': 'Awesome!',
                                             'timestamp': mock.ANY,
                                             'uuid': mock.ANY},
                                            {'author': mock.ANY,
                                             'message': 'Even more awesome?!',
                                             'timestamp': mock.ANY,
                                             'uuid': mock.ANY}]})

    def test_post_403(self):
        self.make_paid(self.user)
        self.sentences = ["I like flowers.", "I don't like butter."]
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )
        url = reverse('sentence_comments_list_view', kwargs={'uuid': self.document.uuid, 's_idx': 1})
        data = [{'message': 'Awesome!'}, {'message': 'Even more awesome?!'}]
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_post_document_404(self):
        self.make_paid(self.user)
        self.login()
        self.sentences = ["I like flowers.", "I don't like butter."]
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )
        url = reverse('sentence_comments_list_view', kwargs={'uuid': '1234', 's_idx': 1})
        data = [{'message': 'Awesome!'}, {'message': 'Even more awesome?!'}]
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_post_sentence_404(self):
        self.make_paid(self.user)
        self.login()
        self.sentences = ["I like flowers.", "I don't like butter."]
        self.document = self.create_analysed_document(
            'My beautiful document', self.sentences, self.user
        )
        url = reverse('sentence_comments_list_view', kwargs={'uuid': self.document.uuid, 's_idx': 1111})
        data = [{'message': 'Awesome!'}, {'message': 'Even more awesome?!'}]
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 404)
