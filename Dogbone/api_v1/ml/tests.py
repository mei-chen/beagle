import json

from django.urls import reverse
import mock

from dogbone.testing.base import BeagleWebTest
from ml.capsules import Capsule
from ml.facade import LearnerFacade


class OnlineLearnerBaseTestCase(BeagleWebTest):

    @classmethod
    def setUpClass(cls):
        super(OnlineLearnerBaseTestCase, cls).setUpClass()

        # Don't even try to make real calls to S3 or local FS for loading/saving
        # online or pretrained (i.e. offline) learners respectively
        cls.load_models_patcher = mock.patch(
            'ml.facade.TagLearner.load_models'
        )
        cls.save_online_model_patcher = mock.patch(
            'ml.facade.TagLearner.save_online_model'
        )

        cls.load_models_patcher.start()
        cls.save_online_model_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.save_online_model_patcher.stop()
        cls.load_models_patcher.stop()

        super(OnlineLearnerBaseTestCase, cls).tearDownClass()


class OnlineLearnerViewTestCase(OnlineLearnerBaseTestCase):

    def test_200(self):
        learner = LearnerFacade.get_or_create('taggy', self.user)
        api_url = reverse('online_learner_detail_view', kwargs={'tag': 'taggy'})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data,
                         {'name': 'taggy',
                          'deleted': False,
                          'positive_set_size': 0,
                          'noninfered_set_size': 0,
                          'active': True,
                          'pretrained': False,
                          'total_set_size': 0,
                          'id': learner.db_model.id,
                          'color_code': "#f9f6fb"})

    def test_delete(self):
        LearnerFacade.get_or_create('taggy', self.user)
        api_url = reverse('online_learner_detail_view', kwargs={'tag': 'taggy'})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertFalse(data['deleted'])

        response = self.client.delete(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['deleted'])

    def test_not_authenticated(self):
        LearnerFacade.get_or_create('taggy', self.user)
        api_url = reverse('online_learner_detail_view', kwargs={'tag': 'taggy'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

    def test404(self):
        self.login()
        api_url = reverse('online_learner_detail_view', kwargs={'tag': 'taggy_nonexistent'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)


class OnlineLearnerSamplesViewTestCase(OnlineLearnerBaseTestCase):

    def test_200(self):
        ol = LearnerFacade.get_or_create('taggy', self.user)  # Should create

        api_url = reverse('online_learner_samples_detail_view', kwargs={'tag': 'taggy'})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data,
                         {'samples': []})

        ol.train([Capsule('text 1')], [True])
        ol.train([Capsule('text 2')], [True])

        api_url = reverse('online_learner_samples_detail_view', kwargs={'tag': 'taggy'})
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data,
                         {'samples': [['text 1', True], ['text 2', True]]})

    def test_not_authenticated(self):
        LearnerFacade.get_or_create('taggy', self.user)
        api_url = reverse('online_learner_samples_detail_view', kwargs={'tag': 'taggy'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

    def test404(self):
        self.login()
        api_url = reverse('online_learner_samples_detail_view', kwargs={'tag': 'taggy_nonexistent'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)


class OnlineLearnerActiveViewTestCase(OnlineLearnerBaseTestCase):

    def test_200(self):
        learner = LearnerFacade.get_or_create('taggy', self.user)
        api_url = reverse('online_learner_active_view', kwargs={'tag': 'taggy'})
        self.login()

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data, {'active': True, 'id': learner.db_model.id})

    def test_deactivate(self):
        LearnerFacade.get_or_create('taggy', self.user)
        api_url = reverse('online_learner_active_view', kwargs={'tag': 'taggy'})
        self.login()

        response = self.client.delete(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertFalse(data['active'])

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertFalse(data['active'])

    def test_activate(self):
        ol = LearnerFacade.get_or_create('taggy', self.user)
        ol.db_model.active = False
        ol.db_model.save()
        api_url = reverse('online_learner_active_view', kwargs={'tag': 'taggy'})
        self.login()

        response = self.client.put(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['active'])

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['active'])

    def test_not_authenticated(self):
        LearnerFacade.get_or_create('taggy', self.user)
        api_url = reverse('online_learner_active_view', kwargs={'tag': 'taggy'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

    def test404(self):
        self.login()
        api_url = reverse('online_learner_active_view', kwargs={'tag': 'taggy_nonexistent'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)


class OnlineLearnerResetViewTestCase(OnlineLearnerBaseTestCase):

    def test_reset(self):
        ol = LearnerFacade.get_or_create('taggy', self.user)
        ol.db_model.add_sample('text 1', [], 'taggy')
        ol.db_model.add_sample('text 2', [], 'taggy')

        api_url = reverse('online_learner_reset_view', kwargs={'tag': 'taggy'})
        self.login()

        response = self.client.put(api_url)
        self.assertEqual(response.status_code, 200)

        api_url = reverse('online_learner_detail_view', kwargs={'tag': 'taggy'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data)

    def test_not_authenticated(self):
        LearnerFacade.get_or_create('taggy', self.user)
        api_url = reverse('online_learner_reset_view', kwargs={'tag': 'taggy'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 403)

    def test404(self):
        self.login()
        api_url = reverse('online_learner_reset_view', kwargs={'tag': 'taggy_nonexistent'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 404)


class OnlineLearnerTrainViewTestCase(OnlineLearnerBaseTestCase):

    def test_train(self):
        ol = LearnerFacade.get_or_create('taggy', self.user)  # Should create
        ol.train([Capsule('text 1')], [True])
        ol.train([Capsule('text 2')], [True])

        api_url = reverse('online_learner_train_view', kwargs={'tag': 'taggy'})
        self.login()

        data = json.dumps([{'content': 'text 3', 'polarity': True}, {'content': 'text 2', 'polarity': False}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        api_url = reverse('online_learner_samples_detail_view', kwargs={'tag': 'taggy'})

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        # TODO: maybe change the lists inside the list to dicts
        self.assertEqual(data, {'samples': [['text 1', True],
                                            ['text 3', True],
                                            ['text 2', False]]})

    def test_not_authenticated(self):
        LearnerFacade.get_or_create('taggy', self.user)
        api_url = reverse('online_learner_train_view', kwargs={'tag': 'taggy'})

        data = json.dumps([{'content': 'text 3', 'polarity': True}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test404(self):
        self.login()
        api_url = reverse('online_learner_train_view', kwargs={'tag': 'taggy_nonexistent'})

        data = json.dumps([{'content': 'text 3', 'polarity': True}])
        response = self.client.post(api_url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 404)
