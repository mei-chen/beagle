import mock

from dogbone.testing.base import BeagleWebTest
from ml.clfs import TagLearner, LearnerAttributeClassifier
from ml.facade import LearnerFacade
from ml.models import OnlineLearner, LearnerAttribute


class PretrainedLearnerTest(BeagleWebTest):
    NEED_DEFAULT_USER = False

    @classmethod
    def setUpClass(cls):
        super(PretrainedLearnerTest, cls).setUpClass()

        cls.data   = ['Aaaa Aaaa'] * 20 + ['Bbbb Bbbb'] * 20
        cls.flags  = [[]] * 40
        cls.labels = [True] * 20 + [False] * 20

        # Don't even try to make real calls to S3 or local FS for loading
        # online or pretrained (i.e. offline) learners respectively
        cls.load_models_patcher = mock.patch(
            'ml.facade.TagLearner.load_models'
        )

        cls.load_models_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.load_models_patcher.stop()

        super(PretrainedLearnerTest, cls).tearDownClass()

    def test_component_get_all(self):
        initial = list(LearnerFacade.get_all())
        self.assertTrue(len(initial) == 0)

        LearnerFacade.get_or_create('tag1')
        all_clfs = list(LearnerFacade.get_all())
        self.assertTrue(len(all_clfs) == 1)

        # Get the previous tag again. Shouldn't create a new one
        LearnerFacade.get_or_create('tag1')
        all_clfs = list(LearnerFacade.get_all())
        self.assertTrue(len(all_clfs) == 1)

        # Add another one
        LearnerFacade.get_or_create('tag2')
        all_clfs = list(LearnerFacade.get_all())
        self.assertTrue(len(all_clfs) == 2)

    def test_learner_train_predict(self):
        model = TagLearner(OnlineLearner(tag='tag', model_uuid='1234'))

        model.prefit(self.data,
                     self.flags,
                     self.labels)

        self.assertTrue(model.predict(['Aaaa Aaaa'], [[]])[0])
        self.assertFalse(model.predict(['Bbbb Bbbb'], [[]])[0])

    def test_attribute_learner_train_predict(self):
        model = LearnerAttributeClassifier(LearnerAttribute(tag='tag', model_uuid='1234'))

        model.prefit(self.data,
                     self.flags,
                     self.labels)

        self.assertTrue(model.predict(['Aaaa Aaaa'], [[]])[0])
        self.assertFalse(model.predict(['Bbbb Bbbb'], [[]])[0])
