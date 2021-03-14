import random
from json import loads

from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from mock import call, patch, ANY

from rest_framework.test import APITestCase

from analysis.constants import ReportTypes
from analysis.models import RegEx, Report, Keyword, KeywordList, SimModel
from document.models import Document, Sentence
from portal.models import Batch, File
from shared.mixins import PatcherMixin


class APIRegExTest(APITestCase):
    def setUp(self):
        self.patchers = {}
        self.user = baker.make(User)
        self.list_url = reverse('regex-list')

        super(APIRegExTest, self).setUp()

    def patch(self, module, name):
        self.patchers[name] = patch('%s.%s' % (module, name))
        setattr(self, name, self.patchers[name].start())
        self.addCleanup(self.patchers[name].stop)

    def create_dataset(self):
        self.regexes = baker.make(RegEx, 3)

    def regex_uri(self, regex):
        return reverse('regex-detail', kwargs={
            'pk': regex.pk,
        })

    def test_convert_api_requires_login(self):
        """
        RegEx API requires login
        """
        resp = self.client.post(self.list_url, {})
        self.assertEqual(resp.status_code, 401)

    def test_regex_api_returns_list(self):
        """
        RegEx API should return regex list
        """
        self.create_dataset()
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        data = loads(response.content)
        self.assertEqual(len(data), 3)
        for i in range(3):
            self.assertEqual(data[i]['name'], self.regexes[i].name)
            self.assertEqual(data[i]['content'], self.regexes[i].content)

    def test_regex_api_create(self):
        """
        RegEx API should create instance
        """
        self.client.force_login(self.user)
        data = {
            'name': 'some name',
            'content': 'some random content'
        }
        self.assertEqual(RegEx.objects.count(), 0)
        response = self.client.post(self.list_url, format='json', data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(RegEx.objects.first().name, data['name'])
        self.assertEqual(RegEx.objects.first().content, data['content'])

    def test_regex_api_create_requires_content(self):
        """
        RegEx API should reqire content field
        """
        self.client.force_login(self.user)
        data = {
            'name': 'some name'
        }
        response = self.client.post(self.list_url, format='json', data=data)
        self.assertEqual(response.status_code, 400)

    def test_regex_api_create_requires_name(self):
        """
        RegEx API should reqire name field
        """
        self.client.force_login(self.user)
        data = {
            'content': 'some random content'
        }
        response = self.client.post(self.list_url, format='json', data=data)
        self.assertEqual(response.status_code, 400)

    def test_regex_api_edit_regex(self):
        """
        RegEx API should allow regex editing
        """
        self.client.force_login(self.user)
        regex = baker.make(RegEx)
        data = {
            'name': 'some name',
            'content': 'some random content'
        }
        for i in data.keys():
            self.assertNotEqual(data[i], getattr(regex, i))
        response = self.client.patch(
            self.regex_uri(regex), format='json', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RegEx.objects.count(), 1)
        regex.refresh_from_db()
        for i in data.keys():
            self.assertEqual(data[i], getattr(regex, i))

    def test_regex_api_delete_regex(self):
        """
        RegEx API should allow regex to be deleted
        """
        self.client.force_login(self.user)
        regex = baker.make(RegEx)
        response = self.client.delete(
            self.regex_uri(regex), format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(RegEx.objects.count(), 0)


class APIRegExApplyTest(APITestCase):
    def setUp(self):
        self.patchers = {}
        self.user = baker.make(User)
        self.list_url = reverse('regex-apply-list')
        self.patch('analysis.tasks.regex_apply', 'delay')
        super(APIRegExApplyTest, self).setUp()

    def patch(self, module, name):
        self.patchers[name] = patch('%s.%s' % (module, name))
        setattr(self, name, self.patchers[name].start())
        self.addCleanup(self.patchers[name].stop)

    def create_dataset(self):
        self.regex = baker.make(RegEx)
        self.batch = baker.make(Batch)
        self.file = baker.make(File, batch=self.batch)
        self.document = baker.make(Document, source_file=self.file)
        self.sentences = baker.make(Sentence, 4, document=self.document)

    def test_regexapply_api_requires_login(self):
        """
        RegExApply API requires login
        """
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    def test_regexapply_call(self):
        """
        RegExApply call should initiate processing
        """
        self.create_dataset()
        self.client.force_login(self.user)
        data = {
            'batch': self.batch.id,
            'regex': self.regex.id
        }
        response = self.client.post(self.list_url, format='json', data=data)
        self.assertEqual(response.status_code, 201)
        ra_call = call(self.regex.id, self.batch.id, ANY)
        self.delay.assert_has_calls([ra_call])
        self.assertEqual(self.delay.call_count, 1)


class APIReportTest(APITestCase, PatcherMixin):
    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('report-list')

        self.create_dataset()
        self.client.force_login(self.user)

        super(APIReportTest, self).setUp()

    def create_dataset(self):
        self.batch = baker.make(Batch, 2)
        self.reports = baker.make(Report, 2)
        self.report_1 = baker.make(
            Report, 4, batch=self.batch[0], report_type=ReportTypes.RegEx.value)
        self.report_2 = baker.make(
            Report, 4, batch=self.batch[1],
            report_type=ReportTypes.KeyWord.value)

    def test_report_api_requires_login(self):
        """
        Report API requires login
        """
        self.client.logout()
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    def test_report_api_returns_report(self):
        """
        Report API should return reports for specified batch
        """
        response = self.client.get(self.list_url, data={
            'batch': self.batch[0].id,
            'report_type': ReportTypes.RegEx.value
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted([d['name'] for d in loads(response.content)]),
            sorted([r.name for r in self.report_1])
        )

    def test_report_api_returns_report_with_json(self):
        """
        Report API should return reports for specified batch with json filled
        """
        response = self.client.get(self.list_url, data={
            'batch': self.batch[0].id,
            'report_type': ReportTypes.RegEx.value
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted([d['json'] for d in loads(response.content)]),
            sorted([r.json for r in self.report_1])
        )


class APISimModelList(APITestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.user = baker.make(User)
        self.list_url = reverse('simmodel-list')

    def test_requires_login(self):
        """
        API requires login on request
        """
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 401)

    def test_simmodels_list(self):
        """
        API should return available simmodel list
        """
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        data = loads(response.content)
        simmodels = SimModel.objects.all()
        self.assertEqual(
            sorted([d['name'] for d in data]),
            sorted([sm.name for sm in simmodels])
        )
        self.assertEqual(
            sorted([d['api_name'] for d in data]),
            sorted([sm.api_name for sm in simmodels])
        )


class APIRecommendation(APITestCase, PatcherMixin):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.user = baker.make(User)
        self.url = reverse('recommend-list')
        self.patch('analysis.tasks.most_similar_recommend', 'delay')

    def test_requires_login(self):
        """
        API requires login on request
        """
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_recommendation(self):
        """
        API should call task
        """
        self.client.force_login(self.user)
        model = random.choice(SimModel.objects.all())
        data = {
            'word': 'abyss',
            'model': model.api_name
        }
        response = self.client.post(self.url, format='json', data=data)
        self.assertEqual(response.status_code, 201)
        self.delay.assert_called_once_with('abyss', model.api_name, ANY)


class APIKeywordListTest(APITestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.url = reverse('keywordlist-list')

        self.create_dataset()
        self.client.force_login(self.user)
        super(APIKeywordListTest, self).setUp()

    def create_dataset(self):
        self.kw_lists = baker.make(KeywordList, 3)
        baker.make(Keyword, 2, keyword_list=self.kw_lists[0])
        baker.make(Keyword, 3, keyword_list=self.kw_lists[1])

    def kwlist_uri(self, kwl):
        return reverse('keywordlist-detail', kwargs={
            'pk': kwl.pk,
        })

    def test_requires_login(self):
        """
        API requires login on request
        """
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_get_kwlist(self):
        """
        API should returns kw lists
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = loads(response.content)
        self.assertEqual(
            sorted([(d['id'], d['name']) for d in data]),
            sorted([(kwl.id, kwl.name) for kwl in self.kw_lists])
        )

    def test_kwlist_with_keywords(self):
        """
        API should returns kw lists with keywords
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = loads(response.content)
        recieved = [sorted([
            k['content'] for k in d['keywords']]) for d in data]
        expected = [sorted([
            kw.content for kw in kwl.keywords.all()
        ]) for kwl in self.kw_lists]
        self.assertEqual(
            sorted(recieved),
            sorted(expected)
        )

    def test_delete_kwlist(self):
        """
        API should allow delete kw list
        """
        kw_list = self.kw_lists[0]
        before = KeywordList.objects.count()
        response = self.client.delete(
            self.kwlist_uri(kw_list), format='json')
        after = KeywordList.objects.count()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(after + 1, before)
        self.assertFalse(KeywordList.objects.filter(pk=kw_list.pk).exists())

    def test_create_kwlist(self):
        """
        API should create kwlist with name and origin keyword
        """
        data = {
            'name': 'some name',
            'origin': 'abyss of endless agony'
        }

        before = KeywordList.objects.count()
        response = self.client.post(self.url, format='json', data=data)
        after = KeywordList.objects.count()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(before, after - 1)
        kwlist = KeywordList.objects.filter(name='some name').last()
        self.assertTrue(kwlist not in self.kw_lists)
        self.assertEqual(kwlist.origin, 'abyss of endless agony')

    def test_create_kwlist_with_keywords(self):
        """
        API should create kwlist with initial keywords
        """
        data = {
            'name': 'some name',
            'origin': 'abyss of endless agony',
            'keywords': [{'content': 'aaa'}, {'content': 'bbb'}]
        }

        before = KeywordList.objects.count()
        response = self.client.post(self.url, format='json', data=data)
        after = KeywordList.objects.count()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(before, after - 1)
        kwlist = KeywordList.objects.filter(name='some name').last()
        self.assertTrue(kwlist not in self.kw_lists)
        keywords = Keyword.objects.filter(keyword_list=kwlist)
        self.assertEqual(kwlist.origin, 'abyss of endless agony')
        self.assertEqual(
            sorted([k.content for k in keywords]),
            sorted(['aaa', 'bbb'])
        )

    def test_edit_kwlist(self):
        """
        API should allow edit kw list
        """
        kw_list = self.kw_lists[2]
        baker.make(Keyword, 2, keyword_list=kw_list)
        data = {
            'name': 'some name',
            'keywords': []
        }
        self.assertNotEqual(kw_list.name, 'some name')
        self.assertEqual(kw_list.keywords.count(), 2)
        before = KeywordList.objects.count()
        response = self.client.patch(
            self.kwlist_uri(kw_list), format='json', data=data)
        after = KeywordList.objects.count()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(before, after)
        kw_list.refresh_from_db()
        self.assertEqual(kw_list.name, 'some name')
        self.assertEqual(kw_list.keywords.count(), 0)

    def test_edit_kwlist_with_keywords(self):
        """
        API should create brave new keywords on edit
        """
        kw_list = self.kw_lists[2]
        baker.make(Keyword, 3, keyword_list=kw_list)
        kws = [{
            'uuid': str(kw.uuid),
            'content': kw.content
        } for kw in baker.make(Keyword, 2, keyword_list=kw_list)]
        data = {
            'name': 'some name',
            'keywords': kws + [
                {'content': 'brave new one'}, {'content': 'brave new two'}
            ]
        }
        before = KeywordList.objects.count()
        self.assertFalse(
            kw_list.keywords.filter(content='brave new one').exists())
        self.assertFalse(
            kw_list.keywords.filter(content='brave new two').exists())
        response = self.client.patch(
            self.kwlist_uri(kw_list), format='json', data=data)
        after = KeywordList.objects.count()
        self.assertEqual(response.status_code, 200)
        # two deleted, two added total should be the same
        self.assertEqual(before, after)
        kw_list.refresh_from_db()
        self.assertEqual(
            kw_list.keywords.filter(content='brave new one').count(), 1)
        self.assertEqual(
            kw_list.keywords.filter(content='brave new two').count(), 1)


class APIKeywordTest(APITestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.url = reverse('keyword-list')

        self.create_dataset()
        self.client.force_login(self.user)
        super(APIKeywordTest, self).setUp()

    def create_dataset(self):
        self.kwlists = baker.make(KeywordList, 3)
        baker.make(Keyword, 3, keyword_list=self.kwlists[0])
        baker.make(Keyword, 2, keyword_list=self.kwlists[1])

    def test_requires_login(self):
        """
        API requires login on request
        """
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_get_keywords(self):
        """
        API should returns keywords for specific list
        """
        response = self.client.get(self.url, data={
            'keyword_list': self.kwlists[0].id})
        self.assertEqual(response.status_code, 200)
        data = loads(response.content)
        self.assertEqual(
            sorted([d['content'] for d in data]),
            sorted([kw.content for kw in self.kwlists[0].keywords.all()])
        )


class APIKeywordListSearchTest(APITestCase, PatcherMixin):
    def setUp(self):
        self.user = baker.make(User)
        self.url = reverse('keywordlist-search-list')
        self.patch('analysis.tasks.keywordlist_search', 'delay')
        super(APIKeywordListSearchTest, self).setUp()

    def create_dataset(self):
        self.keywordlist = baker.make(KeywordList)
        self.batch = baker.make(Batch)
        self.file = baker.make(File, batch=self.batch)
        self.document = baker.make(Document, source_file=self.file)
        self.sentences = baker.make(Sentence, 4, document=self.document)

    def test_api_requires_login(self):
        """
        API requires login
        """
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)

    def test_call_task(self):
        """
        API should initiate processing via call proper task
        """
        self.create_dataset()
        self.client.force_login(self.user)
        data = {
            'batch': self.batch.id,
            'keywordlist': self.keywordlist.id,
            'obfuscate': False
        }
        response = self.client.post(self.url, format='json', data=data)
        self.assertEqual(response.status_code, 201)
        ra_call = call(self.keywordlist.id, self.batch.id, False, ANY)
        self.delay.assert_has_calls([ra_call])
        self.assertEqual(self.delay.call_count, 1)
