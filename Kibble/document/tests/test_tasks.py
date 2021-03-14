import json
import numpy as np
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from mock import call, patch
from model_mommy import mommy, recipe

from document.models import Document, DocumentTag, Sentence
from document.tasks import (
    convert_file, cleanup_document, sentence_splitting, zip_sentences,
    auto_process_file
)
from document.tests.helpers import side_effect_tmpfile, TempCleanupTestCase
from portal.models import File, Batch
from shared.mixins import PatcherMixin

filerecipe = recipe.Recipe(
    File,
    content=recipe.seq('mock.file')
)


class ConvertTaskTest(TempCleanupTestCase, PatcherMixin):
    def setUp(self):
        self.files = baker.make(File, 3)
        self.patch('document.tasks.File.objects', 'get')
        self.patch('document.tasks.NotificationManager', 'notify_client')
        self.patch('document.models', 'docx_to_txt')
        self.docx_to_txt.side_effect = side_effect_tmpfile
        super(ConvertTaskTest, self).setUp()

    def test_convert_task_conversion(self):
        """
        Convert task should fetch object and call convert() on it
        """
        convert_file.run(self.files[1].id, 'foo')
        self.get.assert_called_once_with(id=self.files[1].id)
        self.get.return_value.convert.assert_called_once()

    def test_convert_task_notify(self):
        """
        Convert task should notify about success conversion
        """
        doc = baker.make(Document, content_file=self.files[0].content.path)
        self.get.return_value.convert.return_value = doc
        self.get.return_value.id = '12345'
        self.get.return_value.file_name = 'foobar.txt'
        convert_file.run(self.files[1].id, 'foo')
        self.notify_client.assert_called_with('foo', {
            'action': 'convert_file',
            'file': '12345',
            'document': {
                'name': doc.name,
                'id': doc.id,
                'content_file': doc.content_file.url,
                'text_file': doc.text_file.url
            },
            'notify': {
                'message': 'File foobar.txt is converted',
                'level': 'success'
            },
        })
        self.notify_client.return_value.send.assert_called()

    def test_convert_task_notify_error(self):
        """
        Convert task should notify about failed conversion
        """
        self.get.return_value.convert.return_value = None
        self.get.return_value.file_name = 'foobar.txt'
        convert_file.run(self.files[1].id, 'foo')
        self.notify_client.assert_called_with('foo', {
            'notify': {
                'message': "File foobar.txt can't be converted!",
                'level': 'error'
            },
        })
        self.notify_client.return_value.send.assert_called()


class CleanupDocumentToolsTest(TestCase, PatcherMixin):
    def setUp(self):
        self.docs = baker.make(Document, 3)
        self.patch('document.models.Document.objects', 'get')
        self.patch('document.models.Document', 'cleanup')
        self.patch('document.tasks.NotificationManager', 'notify_client')
        super(CleanupDocumentToolsTest, self).setUp()

    def test_cleanup_document_get(self):
        """
        cleanup_document should call selected tool with id
        """
        cleanup_document.run(['title'], self.docs[0].id, 'endless')
        self.get.assert_called_once_with(id=self.docs[0].id)
        self.get.return_value.cleanup.assert_called_once_with(
            ['title'], 'endless')

    def test_cleanup_task_notify(self):
        """
        Cleanup task should notify about success conversion
        """
        doc = baker.make(Document, name='abrakadabra')
        seq = [
            {'order': 4, 'tool': 'title'},
            {'order': 2, 'tool': 'tables'},
            {'order': 3, 'tool': 'table of contents'},
            {'order': 1, 'tool': 'linebreakers'}]
        for pos in seq:
            baker.make(
                DocumentTag, document=doc, order=pos['order'], name=pos['tool']
            )
        self.get.return_value = doc
        self.cleanup.return_value = doc

        ordered_tools = map(
            lambda x: x['tool'], sorted(seq, key=lambda x: x['order']))
        cleanup_document.run(ordered_tools, self.docs[0].id, 'fizz')
        messages = [
            {
                'notify': {
                    'level': 'info',
                    'message': "Start cleanup for {}".format(doc.name)
                },
            },
            {
                'action': 'cleanup_document',
                'notify': {
                    'level': 'success',
                    'message': "{} is cleaned".format(doc.name)
                },
                'doc': {
                    'name': doc.name,
                    'id': doc.id,
                    'tags': ordered_tools,
                    'cleaned_txt': doc.cleaned_txt_url,
                    'cleaned_docx': doc.cleaned_docx_url
                }
            }
        ]
        calls = [call('fizz', msg) for msg in messages]
        self.notify_client.assert_has_calls(calls, any_order=True)


class SentenceMock(object):

    def __init__(self, document, text, vectorization=None):
        self.document = document
        self.text = text
        self.vectorization = vectorization

    def __eq__(self, other):
        return (self.document == other.document and self.text == other.text and
                self.vectorization == other.vectorization)


class SentenceSplittingTaskTest(TestCase, PatcherMixin):
    def setUp(self):
        suf = SimpleUploadedFile('foo.txt', 'CONTENT')
        self.document = baker.make(Document, text_file=suf)
        self.document.source_file = baker.make(File)
        self.document.source_file.batch = baker.make(Batch)
        self.document.source_file.batch.owner = baker.make(User)
        self.document.source_file.batch.owner.profile.sentence_word_threshold = 0
        self.bad_document = baker.make(Document)
        self.patch('document.tasks.NotificationManager', 'notify_client')
        self.patch('document.tasks.SentenceSplittingRemoteAPI', 'process')
        self.patch('document.tasks.SentenceVectorAPI', 'vectorize')
        self.patch('document.tasks.Sentence.objects', 'bulk_create')
        self.patch('document.tasks.Document.objects', 'get')
        super(SentenceSplittingTaskTest, self).setUp()

    def get_path(self, fname):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'data',
            'sentence_splitting', fname
        )

    def test_success_splitting_without_vectorization(self):
        """
        Remote server says ok
        """
        with open(self.get_path('split.json')) as f:
            sentences = json.loads(f.read())

        self.get.return_value = self.document
        self.get.return_value.name = self.document.name
        self.get.return_value.id = self.document.id
        self.get.return_value.cleaned = self.document
        self.process.return_value = (
            True,
            'Success split for %s' % self.document.text_file.name,
            sentences
        )
        self.vectorize.return_value = None

        sentence_splitting.run(self.document.id, 'foo')

        self.bulk_create.assert_called_once_with([
            SentenceMock(document=self.document, text=sentence)
            for sentence in sentences
        ])
        self.notify_client.assert_called_with('foo', {
            'action': 'sentence_splitting',
            'notify': {
                'level': 'success',
                'message': 'Success split for %s' %
                self.document.text_file.name,
            },
            'success': True,
            'doc': {
                'name': self.document.name,
                'id': self.document.id,
            }
        })
        self.notify_client.return_value.send.assert_called()

    def test_success_splitting_with_vectorization(self):
        """
        Remote server says ok
        """
        with open(self.get_path('split.json')) as f:
            sentences = json.loads(f.read())

        # Some random vectors from [-1,1)^10
        vectors = [np.random.uniform(-1, 1, 10) for _ in enumerate(sentences)]

        self.get.return_value = self.document
        self.get.return_value.name = self.document.name
        self.get.return_value.id = self.document.id
        self.get.return_value.cleaned = self.document
        self.process.return_value = (
            True,
            'Success split for %s' % self.document.text_file.name,
            sentences
        )
        self.vectorize.return_value = vectors

        sentence_splitting.run(self.document.id, 'foo')

        self.bulk_create.assert_called_once_with([
            SentenceMock(document=self.document, text=sentence,
                         vectorization=list(vector))
            for sentence, vector in zip(sentences, vectors)
        ])
        self.notify_client.assert_called_with('foo', {
            'action': 'sentence_splitting',
            'notify': {
                'level': 'success',
                'message': 'Success split for %s' %
                self.document.text_file.name,
            },
            'success': True,
            'doc': {
                'name': self.document.name,
                'id': self.document.id,
            }
        })
        self.notify_client.return_value.send.assert_called()

    def test_fail_spit(self):
        """
        Remote server says no
        """
        self.process.return_value = (False, 'Some error occurred', [])
        self.get.return_value.name = self.document.name
        self.get.return_value.id = self.document.id

        sentence_splitting.run(self.document.id, 'foo')

        self.bulk_create.assert_not_called()
        self.notify_client.assert_called_with('foo', {
            'action': 'sentence_splitting',
            'notify': {
                'level': 'error',
                'message': 'Some error occurred'
            },
            'success': False,
            'doc': {
                'name': self.document.name,
                'id': self.document.id,
            }
        })
        self.notify_client.return_value.send.assert_called()

    def test_fail_split_if_txt_does_not_exists(self):
        """
        IF document has no txt version then push in socket message about it
        """
        self.process.return_value = (
            False, 'foo', []
        )
        self.get.return_value.name = self.bad_document.name
        self.get.return_value.id = self.bad_document.id
        self.get.return_value.cleaned = self.bad_document

        sentence_splitting.run(self.bad_document.id, 'foo')

        self.bulk_create.assert_not_called()
        self.process.assert_not_called()
        self.notify_client.assert_called_once_with('foo', {
            'action': 'sentence_splitting',
            'notify': {
                'level': 'error',
                'message': 'Document %s has no associated text version.' %
                self.bad_document.name,
            },
            'success': False,
            'doc': {
                'name': self.bad_document.name,
                'id': self.bad_document.id,
            }
        })
        self.notify_client.return_value.send.assert_called_once()


class DownloadSentencesForDocumentsTaskTest(TestCase, PatcherMixin):
    def setUp(self):
        self.batch = baker.make(Batch)
        recipe = filerecipe.extend(batch=self.batch)
        self.document0 = baker.make(Document, source_file=recipe.make())
        self.document1 = baker.make(Document, source_file=recipe.make())
        self.document2 = baker.make(Document)
        for i in range(0, 10):
            baker.make(Sentence, document=self.document0, text='Bar')
            baker.make(Sentence, document=self.document1, text='Bar')

    def test_csv_saving(self):
        """
        Task creates temp directory under upload root and puts here csv files
        """
        self.patch('document.tasks.NotificationManager', 'notify_client')
        file = 'sentences_%s_csv.zip' % self.batch.name
        zip_sentences.run(self.batch, session='foo', ziptype='csv')
        self.notify_client.assert_called_with('foo', {
            'action': 'download_sentences',
            'url': settings.MEDIA_URL + file,
            'success': True,
        })
        self.notify_client.return_value.send.assert_called()
        self.assertTrue(
            os.path.exists(os.path.join(
                settings.MEDIA_ROOT, file
            ))
        )

    def test_json_saving(self):
        """
        Task creates temp directory under upload root and puts here json files
        """
        self.patch('document.tasks.NotificationManager', 'notify_client')
        file = 'sentences_%s_json.zip' % self.batch.name
        zip_sentences.run(self.batch, session='foo', ziptype='json')
        self.notify_client.assert_called_with('foo', {
            'action': 'download_sentences',
            'url': settings.MEDIA_URL + file,
            'success': True,
        })
        self.notify_client.return_value.send.assert_called()
        self.assertTrue(
            os.path.exists(os.path.join(
                settings.MEDIA_ROOT, file
            ))
        )


class AutoProcessFileTest(TestCase, PatcherMixin):
    def setUp(self):
        self.file = baker.make(File, batch=baker.make(Batch))
        self.user = baker.make(User)
        super(AutoProcessFileTest, self).setUp()

    @patch('document.tasks.SentenceSplittingRemoteAPI.process')
    @patch('document.models.Document.cleanup')
    @patch('document.models.Document.objects.get')
    @patch('document.tasks.File.objects.get')
    def test_auto_process_workflow(
            self, file_get, doc_get, cleanup, process):
        """
        Checks that whole auto_process workflow executes
        and ends with success message.
        """

        self.file.need_ocr = True
        self.file.save()
        process.return_value = (
            True,
            'Success split for doc',
            []
        )

        auto_process_file.run(self.file.pk, self.user.pk, 'foo')

        file_get.return_value.convert.assert_called_once()
        doc_get.return_value.cleanup.assert_called_once_with(
            self.user.profile.auto_cleanup_tools, 'foo')
        process.assert_called_once()


    @patch('document.tasks.NotificationManager.notify_client')
    def test_auto_process_not_needed(
            self, notify):
        """
        If user.profile.file_auto_process is set to False,
        auto processing must be skipped silently.
        """

        self.user.profile.file_auto_process = False
        self.user.save()

        auto_process_file.run(self.file.pk, self.user.pk, 'foo')

        notify.assert_not_called()
