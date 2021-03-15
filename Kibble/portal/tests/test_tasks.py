from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from mock import patch, ANY
from model_bakery import baker

from portal.models import Project, Batch, File
from portal.tasks import compress_project


class CompressProjectTaskTest(TestCase):
    def make_file(self):
        self.id += 1
        return SimpleUploadedFile('test%d.docx' % self.id, b'Test Content')

    def make_dataset(self):
        self.project = baker.make(Project, name='project')
        self.batch1 = baker.make(
            Batch, name='cmtt_batch1', project=[self.project])
        self.batch2 = baker.make(
            Batch, name='cmtt_batch2', project=[self.project])
        self.id = 0
        self.files1 = [
            baker.make(File, batch=self.batch1, content=self.make_file())
            for i in range(3)
        ]
        self.files2 = [
            baker.make(File, batch=self.batch2, content=self.make_file())
            for i in range(3)
        ]

    @patch('portal.tasks.NotificationManager.notify_client')
    def test_compress_task(self, notify_client):
        """
        Create archive
        """
        self.make_dataset()
        compress_project.run(self.project.id, 'session')
        notify_client.assert_called_once_with('session', {
            'action': 'compress_project',
            'notify': {'message': 'Archive is ready.', 'level': 'info'},
            'project_id': self.project.id,
            'archive': {
                'content_file': ANY,
                'created_at': ANY
            }
        })
        notify_client.return_value.send.assert_called_once()

    @patch('portal.tasks.NotificationManager.notify_client')
    def test_empty_project_compress(self, notify_client):
        """
        In case if project has no batches inside
        """
        empty_project = baker.make(Project, name='empty')
        compress_project.run(empty_project.id, 'session')
        notify_client.assert_called_once_with('session', {
            'action': 'compress_project',
            'notify': {'message': 'Archive is ready.', 'level': 'info'},
            'project_id': empty_project.id,
            'archive': {
                'content_file': False,
                'created_at': ANY
            },
        })
        notify_client.return_value.send.assert_called_once()
