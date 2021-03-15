from django.contrib.auth.models import User
from django.urls import reverse
from json import loads
from model_bakery import baker, recipe
from mock import call, ANY

from rest_framework.test import APITestCase

from document.models import Document, DocumentTag
from portal.models import File, Batch
from portal.models import Project
from shared.mixins import PatcherMixin


filerecipe = recipe.Recipe(
    File,
    content=recipe.seq('mock', suffix='.file'),
    _create_files=True
)


class APIConvertTest(APITestCase, PatcherMixin):
    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('convertfile-list')
        self.files = baker.make(File, 3)
        self.patch('document.tasks.convert_file', 'delay')
        super(APIConvertTest, self).setUp()

    def test_convert_api_requires_login(self):
        """
        Convert API requires login
        """
        resp = self.client.post(self.list_url, {})
        self.assertEqual(resp.status_code, 401)

    def test_convert_call(self):
        """
        Convert call should initiate file conversion
        """
        self.client.force_login(self.user)
        files = [
            self.files[0].id,
            self.files[1].id,
        ]
        data = {
            'files': files
        }
        response = self.client.post(self.list_url, format='json', data=data)
        self.assertEqual(response.status_code, 201)
        calls = [call(self.files[0].id, ANY), call(self.files[1].id, ANY)]
        self.delay.assert_has_calls(calls, any_order=True)
        self.assertEqual(self.delay.call_count, 2)

class APIDocumentTest(APITestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('document-list')
        super(APIDocumentTest, self).setUp()

    def create_dataset(self):
        self.batches = baker.make(Batch, 2)
        recipe = filerecipe.extend(batch=self.batches[0])
        self.b1_files = [recipe.make(), recipe.make(), recipe.make()]
        recipe = filerecipe.extend(batch=self.batches[1])
        self.b2_files = [recipe.make(), recipe.make(), recipe.make()]
        self.b1_documents = [
            baker.make(Document, source_file=f) for f in self.b1_files]
        self.b2_documents = [
            baker.make(Document, source_file=f) for f in self.b2_files]
        self.d1_tags = [baker.make(
            DocumentTag, 3, document=d) for d in self.b1_documents]

    def test_document_api_requires_login(self):
        """
        Document API requires login
        """
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    def test_get_documents_list_for_batch(self):
        """
        API should return documents for specified batch
        """
        self.create_dataset()
        self.client.force_login(self.user)
        response = self.client.get(self.list_url, data={
            'source_file__batch': self.batches[0].id
        })
        self.assertEqual(response.status_code, 200)
        data = loads(response.content)
        self.assertEqual(len(data), 3)
        # sort data
        self.assertEqual(
            sorted([t['name'] for t in data]),
            sorted([t.name for t in self.b1_documents])
        )

    def test_document_api_return_tags(self):
        """
        API should return document with tags
        """
        self.create_dataset()
        self.client.force_login(self.user)
        response = self.client.get(self.list_url, data={
            'source_file__batch': self.batches[0].id
        })
        self.assertEqual(response.status_code, 200)
        data = loads(response.content)
        self.assertEqual(len(data), 3)
        for doc in data:
            self.assertEqual(len(doc['tags']), 3)
            dtags = [t.name for t in DocumentTag.objects.filter(
                document__name=doc['name'])]
            self.assertEqual(
                sorted(doc['tags']),
                sorted(dtags)
            )


class APICleanupDocumentTest(APITestCase, PatcherMixin):
    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('cleanup-doc-list')
        self.docs = baker.make(Document, 3)
        self.patch('document.tasks.cleanup_document', 'delay')
        super(APICleanupDocumentTest, self).setUp()

    def doc_uri(self, doc):
        return reverse('document-detail', kwargs={
            'pk': doc.pk,
        })

    def test_cleanupdocs_api_requires_login(self):
        """
        CleanupDocument API requires login
        """
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    def test_cleanup_tool_call(self):
        """
        CleanupDocument call should initiate cleanup tool processing
        with selected tool
        """
        self.client.force_login(self.user)
        target = self.docs[:2]
        docs = [doc.id for doc in target]
        seq = ['tables', 'linebreakers', 'table of contents']
        data = {
            'documents': docs,
            'sequence': ['tables', 'linebreakers', 'table of contents']
        }
        response = self.client.post(self.list_url, format='json', data=data)
        self.assertEqual(response.status_code, 201)
        calls = [call(seq, doc.id, ANY) for doc in target]
        self.delay.assert_has_calls(calls, any_order=True)
        self.assertEqual(self.delay.call_count, len(target))


class APICleanupDocumentToolListTest(APITestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('cleanup-doc-tool-list')
        super(APICleanupDocumentToolListTest, self).setUp()

    def test_api_requires_login(self):
        """
        CleanupDocumentToolList API requires login
        """
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    def test_api_returns_tool_list(self):
        """
        CleanupDocumentToolList API should return tool list
        for document cleanup
        """
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)

        data = loads(response.content)
        self.assertEqual(
            sorted(Document.get_tool().keys()),
            sorted(d['tool'] for d in data)
        )


class APISentenceSplittingTest(APITestCase, PatcherMixin):
    def setUp(self):
        self.patch('document.tasks.sentence_splitting', 'delay')
        self.user = baker.make(User)
        self.url = reverse('sentence-splitting-list')
        self.documents = baker.make(Document, 3)
        super(APISentenceSplittingTest, self).setUp()

    def test_api_requires_login(self):
        """
        To use this future login required
        """
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_api_call_starts_sen_splitting_process(self):
        """
        API call starts sentence splitting
        """
        self.client.force_login(self.user)
        documents = [self.documents[0].id, self.documents[1].id]
        data = {
            'documents': documents
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 201)
        calls = [call(d, ANY) for d in documents]
        self.delay.assert_has_calls(calls, any_order=True)
        self.assertEqual(self.delay.call_count, 2)
