import tempfile

import mock

from dogbone.testing.base import BeagleWebTest
from ml.capsules import Capsule
from ml.clfs import LearnerAttributeClassifier
from ml.facade import LearnerFacade
from ml.models import PretrainedLearner, LearnerAttribute


class LearnerFacadeTestCase(BeagleWebTest):

    @classmethod
    def setUpClass(cls):
        super(LearnerFacadeTestCase, cls).setUpClass()

        cls.data = [
            'The quick brown fox jumps over the lazy dog',
            'Lorem ipsum dolor sit amet',
            'Some more samples',
            'Even more dummy text to process',
            'If there only was an infinite source of text called the web',
            'This is the last sample, pinky promise',
        ]

        # Don't even try to make real calls to S3 or local FS for loading
        # online or pretrained (i.e. offline) learners respectively
        cls.load_models_patcher = mock.patch(
            'ml.facade.TagLearner.load_models'
        )

        cls.load_models_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.load_models_patcher.stop()

        super(LearnerFacadeTestCase, cls).tearDownClass()

    def test_create_and_prefit_learner(self):
        LearnerFacade.get_or_create(tag='tagidy')
        fcd = LearnerFacade.get_or_create('tagidy', self.user)
        labels = [True] * 3 + [False] * 3
        fcd.ml_model.prefit(self.data, [[]] * 6, labels)
        self.assertEqual(type(fcd.get_pretrained_component()), PretrainedLearner)
        self.assertEqual(fcd.get_pretrained_component().tag, 'tagidy')

    def test_cant_get_pretrained(self):
        fcd = LearnerFacade.get_or_create('tagidy', self.user)
        self.assertEqual(fcd.get_pretrained_component(), None)

    def test_create_learner_and_predict(self):
        LearnerFacade.get_or_create(tag='tagidy')
        fcd = LearnerFacade.get_or_create('tagidy', self.user)
        labels = [True] * 3 + [False] * 3
        fcd.ml_model.prefit(self.data, [[]] * 6, labels)
        self.assertFalse(fcd.predict([Capsule('This is the last sample, now I swear')]))

    def test_create_getall_mature(self):
        LearnerFacade.get_or_create('immature_1', self.user)
        LearnerFacade.get_or_create('immature_2', self.user)
        LearnerFacade.get_or_create('mature')
        fcd = LearnerFacade.get_or_create('mature', self.user)
        labels = [True] * 3 + [False] * 3
        fcd.ml_model.prefit(self.data, [[]] * 6, labels)
        self.assertEqual([l.db_model.tag
                          for l in LearnerFacade.get_all(self.user,
                                                         mature_only=True)],
                         ['mature'])

    def test_create_learner_with_attrs(self):
        LearnerFacade.get_or_create(tag='tagidy')
        fcd = LearnerFacade.get_or_create('tagidy', self.user)
        labels = [True] * 3 + [False] * 3
        fcd.ml_model.prefit(self.data, [[]] * 6, labels)

        # Perform all read/write operations related to models/vectorizers
        # in the system directory for temporary files
        with mock.patch('ml.models.LearnerAttribute.OFFLINE_MODELS_PATH',
                        tempfile.gettempdir()):
            ptcomp = fcd.get_pretrained_component()
            attr1_range = ['val1', 'val2', 'val3']
            attr1 = LearnerAttribute(name='attr1', parent_learner=ptcomp, output_range=attr1_range)
            attr1.save()
            attr1_clf = LearnerAttributeClassifier(attr1)
            attr1_clf.prefit(self.data * 2, [[]] * 12, attr1_range * 4)
            attr1_clf.save_models()
            attr2 = LearnerAttribute(name='attr2', parent_learner=ptcomp, output_range=[True, False])
            attr2.save()
            result = fcd.predict([Capsule('This is the last sample, now I swear'),
                                  Capsule('That other thing that I forgot really is the last sample, really really')],
                                 include_attributes=True)
        self.assertEqual(result,
                         [{'attrs': [
                                   {'name': u'attr2', 'label': 0.0},
                                   {'name': u'attr1', 'label': 'val3'}
                               ],
                               'label': False
                           },
                           {'attrs': [
                                   {'name': u'attr2', 'label': 0.0},
                                   {'name': u'attr1', 'label': 'val2'}
                                ],
                                'label': False
                           }])
