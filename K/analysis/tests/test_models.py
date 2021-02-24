import json
import re
from model_mommy import mommy

from django.test import TestCase

from analysis.models import Report, RegEx, Keyword, KeywordList, SimModel
from analysis.constants import ReportTypes
from portal.models import Batch, File
from document.models import Document, Sentence


class ReportTest(TestCase):
    def setUp(self):
        self.regex = mommy.make(RegEx, content=re.compile(r'[a-c,1-9]+'))
        self.keywordlist = mommy.make(KeywordList)
        mommy.make(Keyword, content='here', keyword_list=self.keywordlist)
        mommy.make(Keyword, content='9981', keyword_list=self.keywordlist)
        self.batch = mommy.make(Batch)
        self.document = mommy.make(
            Document, source_file=mommy.make(File, batch=self.batch))
        self.report = Report(batch=self.batch)
        self.samples = [
            'shudzzudzzu',
            'here ab34ac',
            '9981 zpxhi',
            'ab acacac66',
        ]
        self.sentences = [
            Sentence.objects.create(
                document=self.document, text=cont
            ) for cont in self.samples]

    def test_apply_regex_fills_json(self):
        """
        apply_regex method should fill json field
        """
        result = self.report.apply_regex(self.regex)
        report = Report.objects.first()
        self.assertEqual(report, self.report)
        self.assertEqual(result.json, report.json)

    def test_apply_keyword_fills_json(self):
        """
        apply_keyword method should fill json field
        """
        result = self.report.apply_keyword(self.keywordlist, [])
        report = Report.objects.first()
        self.assertEqual(report, self.report)
        self.assertEqual(result.json, report.json)

    def test_apply_regex_fills_report_type(self):
        """
        apply_regex method should fill report_type field
        """
        self.report.apply_regex(self.regex)
        report = Report.objects.first()
        self.assertEqual(report.report_type, ReportTypes.RegEx.value)

    def test_apply_keyword_fills_report_type(self):
        """
        apply_keyword method should fill json field
        """
        self.report.apply_keyword(self.keywordlist, [])
        report = Report.objects.first()
        self.assertEqual(report.report_type, ReportTypes.KeyWord.value)

    def test_apply_regex_result(self):
        """
        apply_regex method should apply regex to sentences
        """
        result = self.report.apply_regex(self.regex)

        expected = json.dumps([
            {
                'batch': self.batch.name,
                'regex': self.regex.name,
                'sentence': self.sentences[1].text,
                'found': 'ab34ac'
            }, {
                'batch': self.batch.name,
                'regex': self.regex.name,
                'sentence': self.sentences[2].text,
                'found': '9981'
            }, {
                'batch': self.batch.name,
                'regex': self.regex.name,
                'sentence': self.sentences[3].text,
                'found': 'ab'
            }, {
                'batch': self.batch.name,
                'regex': self.regex.name,
                'sentence': self.sentences[3].text,
                'found': 'acacac66'
            }
        ])
        self.assertEqual(result.json, expected)

    def test_apply_keyword_result(self):
        """
        apply_keyword method should apply regex to sentences
        """
        result = self.report.apply_keyword(self.keywordlist, [])

        expected = json.dumps([
            {
                'batch': self.batch.name,
                'keywordlist': self.keywordlist.name,
                'keyword': 'here',
                'sentence': self.sentences[1].text,
            }, {
                'batch': self.batch.name,
                'keywordlist': self.keywordlist.name,
                'keyword': '9981',
                'sentence': self.sentences[2].text,
            }
        ])
        self.assertEqual(result.json, expected)

    def test_apply_regex_result_none(self):
        """
        If nothing found - return None
        """
        self.regex = mommy.make(RegEx, content=re.compile(r'^ELEXANDINE'))
        result = self.report.apply_regex(self.regex)
        self.assertIsNone(result)

    def test_apply_keyword_result_none(self):
        """
        If nothing found - return None
        """
        kwl = mommy.make(KeywordList)
        mommy.make(Keyword, content='never will find', keyword_list=kwl)
        result = self.report.apply_keyword(kwl, [])
        self.assertIsNone(result)

    def test_apply_regex_unique_values(self):
        """
        json field should contains only unique values
        """
        [Sentence.objects.create(
            document=self.document, text=cont
        ) for cont in self.samples]

        result = self.report.apply_regex(self.regex)

        expected = json.dumps([
            {
                'batch': self.batch.name,
                'regex': self.regex.name,
                'sentence': self.sentences[1].text,
                'found': 'ab34ac'
            }, {
                'batch': self.batch.name,
                'regex': self.regex.name,
                'sentence': self.sentences[2].text,
                'found': '9981'
            }, {
                'batch': self.batch.name,
                'regex': self.regex.name,
                'sentence': self.sentences[3].text,
                'found': 'ab'
            }, {
                'batch': self.batch.name,
                'regex': self.regex.name,
                'sentence': self.sentences[3].text,
                'found': 'acacac66'
            }
        ])
        self.assertEqual(result.json, expected)

    def test_apply_keyword_unique_values(self):
        """
        json field should contains only unique values
        """
        [Sentence.objects.create(
            document=self.document, text=cont
        ) for cont in self.samples]

        result = self.report.apply_keyword(self.keywordlist, [])

        expected = json.dumps([
            {
                'batch': self.batch.name,
                'keywordlist': self.keywordlist.name,
                'keyword': 'here',
                'sentence': self.sentences[1].text,
            }, {
                'batch': self.batch.name,
                'keywordlist': self.keywordlist.name,
                'keyword': '9981',
                'sentence': self.sentences[2].text,
            }
        ])
        self.assertEqual(result.json, expected)


class ReportCsvTest(TestCase):
    def setUp(self):
        self.data = json.dumps([
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
            batch=mommy.make(Batch),
            json=self.data,
            report_type=ReportTypes.RegEx.value)

    def test_get_csv_format_regex(self):
        """
        Returns format for csv according to report_type=RegEx
        """
        report = mommy.make(Report, report_type=ReportTypes.RegEx.value)
        self.assertEqual(
            report.get_csv_format(),
            ['batch', 'regex', 'found', 'sentence']
        )

    def test_get_csv_format_keyword(self):
        """
        Returns format for csv according to report_type=KeywordList
        """
        report = mommy.make(Report, report_type=ReportTypes.KeyWord.value)
        self.assertEqual(
            report.get_csv_format(),
            ['batch', 'keywordlist', 'keyword', 'sentence']
        )

    def test_get_csv_format_none(self):
        """
        Returns format for csv according to report_type=None
        """
        report = Report()
        self.assertEqual(report.get_csv_format(), None)

    def test_generate_csv(self):
        """
        If Report is filled then generate a csv from it
        """
        report = Report.objects.first()
        csv = report.generate_csv()
        self.assertTrue(hasattr(csv, 'read'))
        self.assertIn(csv.read(), 'Bar')

    def test_generate_csv_no_sentences(self):
        """
        Report not filled - no csv
        """
        report = Report.objects.first()
        report.json = ''
        report.save()
        csv = report.generate_csv()
        self.assertIsNone(csv)


class KeywordModel(TestCase):
    def test_keyword_banishing(self):
        """
        Keyword should removed when keywordlist field is None
        """
        mommy.make(Keyword, keyword_list=mommy.make(KeywordList))
        keyword = Keyword.objects.first()
        keyword.keyword_list = None
        keyword.save()
        self.assertFalse(Keyword.objects.exists())


class SimModelModel(TestCase):
    fixtures = ['initial_data.json']

    def test_fixtures_loaded(self):
        """
        Initial data is present
        """
        self.assertTrue(SimModel.objects.exists())


class KeywordListModel(TestCase):
    def test_origin_stores(self):
        """
        KeywordList model can store initial keyword
        """
        kw = mommy.make(KeywordList)
        self.assertTrue(hasattr(kw, 'origin'))
        kw.origin = 'new origin'
        kw.save()
        self.assertTrue(kw.origin, 'new origin')
