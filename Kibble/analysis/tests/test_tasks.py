import os
import json

from django.test import TestCase
from django.conf import settings
from mock import call
from model_mommy import mommy

from analysis.tasks import (
    zip_reports, regex_apply, most_similar_recommend, synonyms_recommend,
    keywordlist_search
)

from portal.models import Batch
from analysis.models import Report, RegEx, KeywordList
from analysis.constants import ReportTypes
from shared.mixins import PatcherMixin


class RegexApplyTest(TestCase, PatcherMixin):
    def setUp(self):
        self.regex = RegEx.objects.create(content='[0-9]{2}', name='lapcharai')
        self.batch = mommy.make(Batch)

    def test_success_apply(self):
        """
        apply_regex task should notify
        """
        self.patch('document.tasks.NotificationManager', 'notify_client')
        self.patch('analysis.models.Report', 'apply_regex')
        self.apply_regex.return_value = Report.objects.create(
            batch=self.batch, report_type=ReportTypes.RegEx.value)

        regex_apply.run(self.regex.id, self.batch.id, 'fizz')
        report = Report.objects.first()

        messages = [
            {
                'notify': {
                    'level': 'info',
                    'message': "Applying {} to {}".format(
                        self.regex.name, self.batch.name)
                },
            },
            {
                'action': 'apply_regex',
                'batch': self.batch.id,
                'notify': {
                    'level': 'success',
                    'message': "{} is applied to {}".format(
                        self.regex.name, self.batch.name)
                },
                'report': {
                    'id': report.id,
                    'name': report.name,
                    'json': report.json,
                    'uuid': str(report.uuid)
                }
            }
        ]
        calls = [call('fizz', msg) for msg in messages]
        self.notify_client.assert_has_calls(calls, any_order=True)

    def test_unsuccess_apply(self):
        """
        Apply task should notify on empty report
        """
        self.patch('document.tasks.NotificationManager', 'notify_client')
        self.patch('analysis.models.Report', 'apply_regex')
        self.apply_regex.return_value = None

        regex_apply.run(self.regex.id, self.batch.id, 'fizz')

        messages = [
            {
                'notify': {
                    'level': 'info',
                    'message': "Applying {} to {}".format(
                        self.regex.name, self.batch.name)
                },
            },
            {
                'notify': {
                    'level': 'warning',
                    'message': "{} nothing found in {}".format(
                        self.regex.name, self.batch.name)
                },
            }
        ]
        calls = [call('fizz', msg) for msg in messages]
        self.notify_client.assert_has_calls(calls, any_order=True)


class BulkZipReportTest(TestCase, PatcherMixin):
    def setUp(self):
        self.patchers = {}
        self.batch = mommy.make(Batch)
        data = json.dumps([
            {
                'batch': 'hiy',
                'regex': 'last',
                'sentence': '542',
                'found': 'ab34ac'
            }, {
                'batch': 'hoy',
                'regex': 'first',
                'sentence': '432',
                'found': '9881'
            }, {
                'batch': 'hey',
                'regex': 'some',
                'sentence': '123',
                'found': 'ab'
            }, {
                'batch': 'hay',
                'regex': 'agony',
                'sentence': '765',
                'found': 'acacac66'
            }
        ])
        Report.objects.create(
            batch=self.batch, json=data, report_type=ReportTypes.RegEx.value)

    def test_csv_saving(self):
        """
        Task creates temp directory under upload root and puts here csv files
        """
        self.patch('document.tasks.NotificationManager', 'notify_client')
        zip_reports.run(self.batch, 'csv', ReportTypes.RegEx.value, session='foo')
        self.notify_client.assert_called_once_with('foo', {
            'action': 'download_reports',
            'url': settings.MEDIA_URL + 'reports_%s.zip' % self.batch.name,
            'notify': {'message': 'Ready to download', 'level': 'success'},
            'success': True,
        })
        self.notify_client.return_value.send.assert_called_once()
        self.assertTrue(
            os.path.exists(os.path.join(
                settings.MEDIA_ROOT,
                'reports_%s.zip' % self.batch.name
            ))
        )

    def test_json_saving(self):
        """
        Task creates temp directory under upload root and puts here json files
        """
        self.patch('document.tasks.NotificationManager', 'notify_client')
        zip_reports.run(self.batch, 'json', ReportTypes.RegEx.value, session='foo')
        self.notify_client.assert_called_once_with('foo', {
            'action': 'download_reports',
            'url': settings.MEDIA_URL + 'reports_%s.zip' % self.batch.name,
            'notify': {'message': 'Ready to download', 'level': 'success'},
            'success': True,
            'notify': {
                'level': 'success',
                'message': "Ready to download"
            }
        })
        self.notify_client.return_value.send.assert_called_once()
        self.assertTrue(
            os.path.exists(os.path.join(
                settings.MEDIA_ROOT,
                'reports_%s.zip' % self.batch.name
            ))
        )


class MostSimilarTasksTest(TestCase, PatcherMixin):
    def setUp(self):
        self.patch('utils.most_similar.api.MostSimmilarModelAPI', 'process')
        self.patch('document.tasks.NotificationManager', 'notify_client')

    def test_calls_api(self):
        """
        task should call api
        """
        self.process.return_value = (True, 'msg', {})
        most_similar_recommend.run('word', 'default', '123')
        self.process.assert_called_once()

    def test_send_notifications_success(self):
        """
        task should send notifications with successful result from most similar
        """
        word = 'someword'
        message = 'Successfuly acquired recommendations for {}'.format(word)
        result = {'results': [
            {'text': 'otherword', 'score': 1},
            {'text': 'oncemore', 'score': 0}]
        }
        self.process.return_value = (True, message, result)
        most_similar_recommend.run(word, 'default', '123')
        messages = [
            {
                'notify': {
                    'level': 'info',
                    'message': "Start suggesting keywords for {}".format(word)
                },
            },
            {
                'action': 'recommend',
                'notify': {
                    'level': 'success',
                    'message': message
                },
                'keywords': ['otherword', 'oncemore']
            }
        ]
        calls = [call('123', msg) for msg in messages]
        self.notify_client.assert_has_calls(calls, any_order=True)

    def test_send_notifications_fail(self):
        """
        task should send notifications with fail result from most similar
        """
        word = 'someword'
        message = 'An error occurred. Status: {} '.format(666)
        result = {}
        self.process.return_value = (False, message, result)
        most_similar_recommend.run(word, 'default', '123')
        messages = [
            {
                'notify': {
                    'level': 'info',
                    'message': "Start suggesting keywords for {}".format(word)
                },
            },
            {
                'action': 'recommend',
                'notify': {
                    'level': 'error',
                    'message': message
                },
                'keywords': []
            }
        ]
        calls = [call('123', msg) for msg in messages]
        self.notify_client.assert_has_calls(calls, any_order=True)


class RecommendSynonymsTasksTest(TestCase, PatcherMixin):
    def setUp(self):
        self.patch('utils.synonyms.api.SynonymsAPI', 'process')
        self.patch('document.tasks.NotificationManager', 'notify_client')

    def test_calls_api(self):
        """
        task should call api
        """
        self.process.return_value = (True, 'msg', {})
        synonyms_recommend.run('word', '123')
        self.process.assert_called_once()

    def test_send_notifications_success(self):
        """
        task should send notifications with successful result
        """
        word = 'someword'
        message = 'Successfully acquired recommendations for {}'.format(word)
        result = {'synonyms': [
            'one', 'two'
        ]
        }
        self.process.return_value = (True, message, result)
        synonyms_recommend.run(word, '123')
        messages = [
            {
                'notify': {
                    'level': 'info',
                    'message': "Start suggesting synonyms for {}".format(word)
                },
            },
            {
                'action': 'synonyms',
                'notify': {
                    'level': 'success',
                    'message': message
                },
                'keywords': ['one', 'two']
            }
        ]
        calls = [call('123', msg) for msg in messages]
        self.notify_client.assert_has_calls(calls, any_order=True)

    def test_send_notifications_fail(self):
        """
        task should send notifications with fail result
        """
        word = 'someword'
        message = 'An error occurred. Status: {} '.format(666)
        result = {}
        self.process.return_value = (False, message, result)
        synonyms_recommend.run(word, '123')
        messages = [
            {
                'notify': {
                    'level': 'info',
                    'message': "Start suggesting synonyms for {}".format(word)
                },
            },
            {
                'action': 'synonyms',
                'notify': {
                    'level': 'error',
                    'message': message
                },
                'keywords': []
            }
        ]
        calls = [call('123', msg) for msg in messages]
        self.notify_client.assert_has_calls(calls, any_order=True)


class KeywordSearchTaskTest(TestCase, PatcherMixin):
    def setUp(self):
        self.keywordlist = KeywordList.objects.create(name='lapcharai')
        self.batch = mommy.make(Batch)

    def test_success_search(self):
        """
        apply_regex task should notify
        """
        self.patch('document.tasks.NotificationManager', 'notify_client')
        self.patch('analysis.models.Report', 'apply_keyword')
        self.apply_keyword.return_value = Report.objects.create(
            batch=self.batch, report_type=ReportTypes.KeyWord.value)

        keywordlist_search.run(self.keywordlist.id, self.batch.id, False, 'fizz')
        report = Report.objects.first()

        messages = [
            {
                'notify': {
                    'level': 'info',
                    'message': "Searching the {} in {}".format(
                        self.keywordlist.name, self.batch.name)
                },
            },
            {
                'action': 'keywordlist_search',
                'batch': self.batch.id,
                'notify': {
                    'level': 'success',
                    'message': "{} is applied to {}".format(
                        self.keywordlist.name, self.batch.name)
                },
                'report': {
                    'id': report.id,
                    'name': report.name,
                    'json': report.json,
                    'uuid': str(report.uuid)
                }
            }
        ]
        calls = [call('fizz', msg) for msg in messages]
        self.notify_client.assert_has_calls(calls, any_order=True)

    def test_unsuccess_apply(self):
        """
        Apply task should notify on empty report
        """
        self.patch('document.tasks.NotificationManager', 'notify_client')
        self.patch('analysis.models.Report', 'apply_keyword')
        self.apply_keyword.return_value = None

        keywordlist_search.run(self.keywordlist.id, self.batch.id, False, 'fizz')

        messages = [
            {
                'notify': {
                    'level': 'info',
                    'message': "Searching the {} in {}".format(
                        self.keywordlist.name, self.batch.name)
                },
            },
            {
                'notify': {
                    'level': 'warning',
                    'message': "{} nothing found in {}".format(
                        self.keywordlist.name, self.batch.name)
                },
            }
        ]
        calls = [call('fizz', msg) for msg in messages]
        self.notify_client.assert_has_calls(calls, any_order=True)
