import json

from django.urls import reverse
import mock

from authentication.models import AuthToken
from dogbone.testing.base import BeagleWebTest
from ml.models import PretrainedLearner


class VWLearnerBaseTestCase(BeagleWebTest):

    @classmethod
    def setUpClass(cls):
        super(VWLearnerBaseTestCase, cls).setUpClass()

        # Don't even try to make real calls to S3 or local FS for loading/saving
        # online or pretrained (i.e. offline) learners respectively
        cls.load_models_patcher = mock.patch(
            'ml.facade.TagLearner.load_models'
        )
        cls.save_online_model_patcher = mock.patch(
            'ml.facade.TagLearner.save_online_model'
        )
        cls.save_models_patcher = mock.patch(
            'ml.facade.TagLearner.save_models'
        )

        cls.load_models_patcher.start()
        cls.save_online_model_patcher.start()
        cls.save_models_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.save_models_patcher.stop()
        cls.save_online_model_patcher.stop()
        cls.load_models_patcher.stop()

        super(VWLearnerBaseTestCase, cls).tearDownClass()


class VWLearnersListViewTestCase(VWLearnerBaseTestCase):

    def test_loggedin(self):
        self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='0001_en', description="has descr", exclusivity='vw')
        pl.save()
        pl = PretrainedLearner(tag='0001_de', exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learners_list_view')
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {u'objects': [{u'description': u'has descr', u'name': u'0001_en'},
                                             {u'description': u'', u'name': u'0001_de'}]})

    def test_predict_token_auth(self):
        user = self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='0001_en', description="has descr", exclusivity='vw')
        pl.save()
        pl = PretrainedLearner(tag='0001_de', exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learners_list_view')
        token = AuthToken.objects.get(user=user).token

        response = self.client.get(api_url + '?token=' + token)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {u'objects': [{u'description': u'has descr', u'name': u'0001_en'},
                                             {u'description': u'', u'name': u'0001_de'}]})

    def test_not_authenticated(self):
        api_url = reverse('vw_learners_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

    def test_not_vw_user(self):
        self.login()
        api_url = reverse('vw_learners_list_view')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)


class VWLearnerDetailViewTestCase(VWLearnerBaseTestCase):

    def test_loggedin(self):
        self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='0001_en', description="has descr", exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learner_detail_view', kwargs={'tag': '0001_en'})
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {u'description': u'has descr', u'name': u'0001_en'})

    def test_put(self):
        self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='0001_en', description="has descr", exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learner_detail_view', kwargs={'tag': '0001_en'})
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        # Initial check
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        respdata = json.loads(response.content)
        self.assertEqual(respdata, {u'description': u'has descr', u'name': u'0001_en'})

        # Do the change and check response
        data = json.dumps({"description": "The new description"})
        response = self.client.put(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        respdata = json.loads(response.content)
        self.assertEqual(respdata, {u'description': u'The new description', u'name': u'0001_en'})

        # Check for the change
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        respdata = json.loads(response.content)
        self.assertEqual(respdata, {u'description': u'The new description', u'name': u'0001_en'})


    def test_predict_token_auth(self):
        user = self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='0001_en', description="has descr", exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learner_detail_view', kwargs={'tag': '0001_en'})
        token = AuthToken.objects.get(user=user).token

        response = self.client.get(api_url + '?token=' + token)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {u'description': u'has descr', u'name': u'0001_en'})

    def test_not_authenticated(self):
        pl = PretrainedLearner(tag='0001_en', description="has descr", exclusivity='vw')
        pl.save()
        api_url = reverse('vw_learner_detail_view', kwargs={'tag': '0001_en'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

    def test_not_vw_user(self):
        pl = PretrainedLearner(tag='0001_en', description="has descr", exclusivity='vw')
        pl.save()
        self.login()
        api_url = reverse('vw_learner_detail_view', kwargs={'tag': '0001_en'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)


class VWLearnerResetViewTestCase(VWLearnerBaseTestCase):
    NEED_DEFAULT_USER = False

    @classmethod
    def setUpClass(cls):
        super(VWLearnerResetViewTestCase, cls).setUpClass()

        cls.user = cls.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')

    def setUp(self):
        super(VWLearnerResetViewTestCase, self).setUp()

        pl = PretrainedLearner(tag='00099_en', description="has descr", exclusivity='vw')
        pl.save()
        api_url = reverse('vw_learner_train_view', kwargs={'tag': '00099_en'})
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        data = json.dumps([{'supplier_comment': 'Here\'s some text 3', 'label': True},
                           {'supplier_comment': 'Some more text in addition', 'label': False}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_loggedin(self):
        api_url = reverse('vw_learner_reset_view', kwargs={'tag': '00099_en'})
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {u'fresh': False})

    def test_put(self):
        api_url = reverse('vw_learner_reset_view', kwargs={'tag': '00099_en'})
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        # Initial check
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        respdata = json.loads(response.content)
        self.assertEqual(respdata, {u'fresh': False})

        # Do the change and check response
        response = self.client.put(api_url, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        respdata = json.loads(response.content)
        self.assertEqual(respdata, {u'fresh': True})

        # Check for the change
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        respdata = json.loads(response.content)
        self.assertEqual(respdata, {u'fresh': True})

    def test_token_auth(self):
        api_url = reverse('vw_learner_reset_view', kwargs={'tag': '00099_en'})
        token = AuthToken.objects.get(user=self.user).token

        response = self.client.get(api_url + '?token=' + token)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {u'fresh': False})

    def test_not_authenticated(self):
        api_url = reverse('vw_learner_reset_view', kwargs={'tag': '00099_en'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

    def test_not_vw_user(self):
        self.login()
        api_url = reverse('vw_learner_reset_view', kwargs={'tag': '00099_en'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)


class VWLearnerPredictViewTestCase(VWLearnerBaseTestCase):

    def test_predict(self):
        self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='0001_en', exclusivity='vw')
        pl.save()
        pl = PretrainedLearner(tag='0001_de', exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learner_predict_view', kwargs={'tag': '0001'})
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        data = json.dumps([{'supplier_comment': 'Here\'s some text 3'}, {'supplier_comment': 'Some more text in addition'}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['status'], 1)

    def test_predict_token_auth(self):
        user = self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='0001_en', exclusivity='vw')
        pl.save()
        pl = PretrainedLearner(tag='0001_de', exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learner_predict_view', kwargs={'tag': '0001'})
        token = AuthToken.objects.get(user=user).token

        data = json.dumps([{'supplier_comment': 'Here\'s some text 3'},
                           {'supplier_comment': 'Some more text in addition'}])
        response = self.client.post(api_url + '?token=' + token,
                                    data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['status'], 1)

    def test_not_authenticated(self):
        api_url = reverse('vw_learner_predict_view', kwargs={'tag': 'taggy'})

        data = json.dumps([{'supplier_comment': 'text 3'}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_not_vw_user(self):
        self.login()
        api_url = reverse('vw_learner_predict_view', kwargs={'tag': 'taggy'})

        data = json.dumps([{'supplier_comment': 'text 3'}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test404(self):
        self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        api_url = reverse('vw_learner_predict_view', kwargs={'tag': 'taggy_nonexistent'})

        data = json.dumps([{'supplier_comment': 'text 3'}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        data = json.loads(response.content)
        self.assertEqual(data['answer'][0]['confidence'], None)


class VWLearnerTrainViewTestCase(VWLearnerBaseTestCase):

    def test_train(self):
        self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='0001_en', exclusivity='vw')
        pl.save()
        pl = PretrainedLearner(tag='0001_de', exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learner_train_view', kwargs={'tag': '0001'})
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        data = json.dumps([{'supplier_comment': 'Here\'s some text 3', 'label': True},
                           {'supplier_comment': 'Some more text in addition', 'label': False}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['status'], 1)

    def test_train_token_auth(self):
        user = self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='0001_en', exclusivity='vw')
        pl.save()
        pl = PretrainedLearner(tag='0001_de', exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learner_train_view', kwargs={'tag': '0001'})
        token = AuthToken.objects.get(user=user).token

        data = json.dumps([{'supplier_comment': 'Here\'s some text 3', 'label': True},
                           {'supplier_comment': 'Some more text in addition', 'label': False}])
        response = self.client.post(api_url + '?token=' + token,
                                    data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['status'], 1)

    def test_not_authenticated(self):
        api_url = reverse('vw_learner_train_view', kwargs={'tag': 'taggy'})

        data = json.dumps([{'supplier_comment': 'text 3', 'label': True}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_not_vw_user(self):
        self.login()
        api_url = reverse('vw_learner_train_view', kwargs={'tag': 'taggy'})

        data = json.dumps([{'supplier_comment': 'text 3', 'label': True}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test404(self):
        self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        api_url = reverse('vw_learner_train_view', kwargs={'tag': 'taggy_nonexistent'})

        data = json.dumps([{'supplier_comment': 'text 3', 'label': True}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        data = json.loads(response.content)
        self.assertEqual(data['status'], 0)


class VWLearnerInitViewTestCase(VWLearnerBaseTestCase):

    def setUp(self):
        super(VWLearnerInitViewTestCase, self).setUp()

        self.data = json.dumps([
            {'supplier_comment': 'Here\'s some text 1', 'label': True},
            {'supplier_comment': 'Here\'s some text 2', 'label': True},
            {'supplier_comment': 'Here\'s some text 3', 'label': True},
            {'supplier_comment': 'Some more stuff in addition', 'label': False},
            {'supplier_comment': 'Some more text in addition', 'label': False},
            {'supplier_comment': 'Some more content in addition', 'label': False},
        ])

    def test_init(self):
        self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')

        api_url = reverse('vw_learner_init_view', kwargs={'tag': 'newtag', 'lang': 'en'})
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        response = self.client.post(api_url, data=self.data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['status'], 1)

    def test_already_existing(self):
        self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')
        pl = PretrainedLearner(tag='existing_en', exclusivity='vw')
        pl.save()

        api_url = reverse('vw_learner_init_view', kwargs={'tag': 'existing', 'lang': 'en'})
        self.client.login(username='vw', password='DUMMY_PASSWORD')

        response = self.client.post(api_url, data=self.data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        # Already existing message
        self.assertEqual(data['status'], 0)

    def test_train_token_auth(self):
        user = self.create_user('email@vw.com', 'vw', 'DUMMY_PASSWORD')

        api_url = reverse('vw_learner_init_view', kwargs={'tag': 'newtag', 'lang': 'en'})
        token = AuthToken.objects.get(user=user).token

        response = self.client.post(api_url + '?token=' + token, data=self.data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['status'], 1)

    def test_not_authenticated(self):
        api_url = reverse('vw_learner_init_view', kwargs={'tag': 'newtag', 'lang': 'en'})

        response = self.client.post(api_url, data=self.data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_not_vw_user(self):
        self.login()
        api_url = reverse('vw_learner_init_view', kwargs={'tag': 'newtag', 'lang': 'en'})

        response = self.client.post(api_url, data=self.data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
