# -*- coding: utf-8 -*-
import json
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import urlquote
from model_bakery import baker, recipe

from django.test import TestCase

from portal.models import Batch, File
from document.models import Document, Sentence
from shared.mixins import PatcherMixin


filerecipe = recipe.Recipe(
    File,
    content=recipe.seq('mock', suffix='.file'),
    _create_files=True
)


class DownloadViewTest(TestCase, PatcherMixin):
    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('document:batch_download')
        self.patch('portal.models.Batch', 'get_converted_documents')
        self.get_converted_documents.return_value\
            .getvalue.return_value = 'ZipFileContent'
        self.batch = baker.make(Batch)

    def test_batch_download_requires_login(self):
        """
        Batch download requires login
        """
        resp = self.client.get(self.list_url, data={'batch': self.batch.id})
        self.assertRedirects(resp, '{}?next={}%3Fbatch%3D{}'.format(
            reverse('account_login'), self.list_url, self.batch.id))

    def test_batch_download_wrong_id(self):
        """
        Batch downloads handles bad/missing bach id
        """
        self.client.force_login(self.user)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get(self.list_url, data={'batch': 123456})
        self.assertEqual(resp.status_code, 404)
        resp = self.client.get(self.list_url, data={'batch': 'foo'})
        self.assertEqual(resp.status_code, 404)

    def test_batch_download_docx(self):
        """
        Batch downloads docx archive by default
        """
        self.client.force_login(self.user)
        resp = self.client.get(self.list_url, data={'batch': self.batch.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), 'ZipFileContent')
        self.get_converted_documents.assert_called_with(False)

    def test_batch_download_text(self):
        """
        Batch downloads txt archive if 'plaintext' specified
        """
        self.client.force_login(self.user)
        resp = self.client.get(
            self.list_url, data={'batch': self.batch.id, 'plaintext': 1})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode('utf-8'), 'ZipFileContent')
        self.get_converted_documents.assert_called_with(True)

    def test_batch_download_handle_utf8_name(self):
        """
        Batch downloads handles unicode and quotes
        """
        self.batch.name = 'Юникод "test"'
        self.batch.save()
        self.client.force_login(self.user)
        resp = self.client.get(self.list_url, data={'batch': self.batch.id})
        self.assertEqual(resp.status_code, 200)
        converted_name = urlquote(self.batch.name + '.zip')
        content_disposition = resp.get('Content-Disposition')
        self.assertIn(converted_name, content_disposition)


class SentenceDownloadTest(TestCase, PatcherMixin):
    def setUp(self):
        self.download_url = reverse('document:download_sentences')
        self.user = baker.make(User)
        self.batch = baker.make(Batch, name='Batch')
        recipe = filerecipe.extend(batch=self.batch)
        self.document0 = baker.make(Document, source_file=recipe.make())
        self.document1 = baker.make(Document, source_file=recipe.make())
        self.document2 = baker.make(Document)
        for i in range(0, 10):
            baker.make(Sentence, document=self.document0, text='Bar')
            baker.make(Sentence, document=self.document1, text='Bar')

    def test_sentences_download_requires_login(self):
        """
        For this download login required
        """
        response = self.client.get(self.download_url)
        self.assertRedirects(
            response,
            '%s?next=%s' % (reverse('account_login'), self.download_url))

    def test_error_if_document_id_not_present(self):
        """
        Document id should be sent
        """
        self.client.force_login(self.user)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 400)

    def test_error_if_document_not_found(self):
        """
        If document not found or this document has no sentences
        """
        self.client.force_login(self.user)
        response = self.client.get(
            self.download_url,
            {'document': 99999999}
        )
        self.assertEqual(response.status_code, 404)

    def test_return_sentences(self):
        """
        If view gets only one document id then return csv
        """
        self.client.force_login(self.user)
        response = self.client.get(
            self.download_url,
            {'document': self.document0.id}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Disposition'),
            'attachment; filename="{}.csv"; filename*="utf-8\'\'{}.csv"'.format(
                self.document0.name, self.document0.name
            )
        )

    def test_download_csv_for_batch(self):
        """
        Sentences download view triggers zip creation if batch id specified
        """
        self.patch('document.views.zip_sentences', 'delay')
        self.client.force_login(self.user)
        response = self.client.get(
            self.download_url,
            {'batch': self.batch.id}
        )
        self.assertEqual(response.status_code, 201)
        self.delay.called_once_with(
            batch_id=self.batch.id,
            session=self.client.session.session_key,
            json=None
        )

    def test_return_sentences_json(self):
        """
        If view gets only one document id and 'json=1' param then return json
        """
        self.client.force_login(self.user)
        response = self.client.get(
            self.download_url,
            {'document': self.document0.id, 'json': 1}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Disposition'),
            'attachment; filename="{0}.json"; filename*="utf-8\'\'{0}.json"'
            .format(self.document0.name)
        )
        data = json.loads(response.content)
        self.assertEqual(
            data,
            list(self.document0.sentences.all().values_list('text', flat=True))
        )

    def test_download_json_for_batch(self):
        """
        Sentences download view triggers zip creation if batch id specified
        """
        self.patch('document.views.zip_sentences', 'delay')
        self.client.force_login(self.user)
        response = self.client.get(
            self.download_url,
            {'batch': self.batch.id, 'json': 1}
        )
        self.assertEqual(response.status_code, 201)
        self.delay.called_once_with(
            batch_id=self.batch.id,
            session=self.client.session.session_key,
            json='1'
        )
