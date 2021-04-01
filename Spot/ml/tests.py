import time
import unittest

import mock
import numpy as np
from sklearn import metrics
from sklearn.model_selection import StratifiedShuffleSplit

from django.contrib.auth.models import User
from django.test import TestCase

from ml.capsules import Capsule
from ml.clfs import TagLearner, LearnerAttributeClassifier
from ml.facade import LearnerFacade
from ml.models import OnlineLearner, PretrainedLearner, LearnerAttribute
from ml.vecs import TagLearnerOnlineVectorizer, TagLearnerOfflineVectorizer


class S3BucketManagerMock(object):
    """
    Dummy S3 bucket manager saving/loading data to/from a shared class dict.
    """

    # Our own local S3 :)
    data = {}

    def __init__(self, bucket):
        self.bucket = bucket

    @classmethod
    def save_string(cls, key, string):
        cls.data[key] = string

    @classmethod
    def read_to_string(cls, key):
        return cls.data.get(key)


class MLTestCase(TestCase):

    NEED_DEFAULT_USER = True

    DEFAULT_USER_USERNAME = 'ml'
    DEFAULT_USER_EMAIL = 'ml@test.com'
    DEFAULT_USER_PASSWORD = 'ML-2018'

    @classmethod
    def setUpClass(cls):
        super(MLTestCase, cls).setUpClass()

        if cls.NEED_DEFAULT_USER:
            cls.user = User.objects.create(username=cls.DEFAULT_USER_USERNAME,
                                           email=cls.DEFAULT_USER_EMAIL)
            cls.user.set_password(cls.DEFAULT_USER_PASSWORD)
        else:
            cls.user = None

        # Don't even try to make real calls to S3 for loading/saving any models
        cls.s3_bucket_manager_patcher = mock.patch(
            'ml.models.get_s3_bucket_manager', S3BucketManagerMock
        )

        cls.s3_bucket_manager_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.s3_bucket_manager_patcher.stop()

        if cls.user:
            cls.user.delete()

        super(MLTestCase, cls).tearDownClass()


class LearnerFacadeTestCase(MLTestCase):

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

        ptcomp = fcd.get_pretrained_component()

        attr1_range = ['val1', 'val2', 'val3']
        attr1 = LearnerAttribute(name='attr1', parent_learner=ptcomp, output_range=attr1_range)
        attr1.save()

        attr1_clf = LearnerAttributeClassifier(attr1)
        attr1_clf.prefit(self.data * 2, [[]] * 12, attr1_range * 4)
        attr1_clf.save_models()

        # Don't train this one
        attr2 = LearnerAttribute(name='attr2', parent_learner=ptcomp, output_range=[True, False])
        attr2.save()

        attr3_range = [-1, +1]
        attr3 = LearnerAttribute(name='attr3', parent_learner=ptcomp,
                                 output_range=attr3_range)
        attr3.save()

        attr3_clf = LearnerAttributeClassifier(attr3)
        attr3_clf.prefit(self.data, [[]] * 6, attr3_range * 3)
        attr3_clf.save_models()

        actual = fcd.predict([Capsule('This is the last sample, now I swear'),
                              Capsule('That other thing that I forgot really is the last sample, really really')],
                             include_attributes=True)

        expected = [
            {
                'label': False,
                'attrs': [
                    {'name': u'attr1', 'label': 'val3'},
                    {'name': u'attr2', 'label': None},
                    {'name': u'attr3', 'label': +1},
                ]
            },
            {
                'label': False,
                'attrs': [
                    {'name': u'attr1', 'label': 'val2'},
                    {'name': u'attr2', 'label': None},
                    {'name': u'attr3', 'label': -1},
                ]
            },
        ]

        self.assertEqual(actual, expected)


class PretrainedLearnerTestCase(MLTestCase):

    NEED_DEFAULT_USER = False

    @classmethod
    def setUpClass(cls):
        super(PretrainedLearnerTestCase, cls).setUpClass()

        cls.data   = ['Aaaa Aaaa'] * 20 + ['Bbbb Bbbb'] * 20
        cls.flags  = [[]] * 40
        cls.labels = [True] * 20 + [False] * 20

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
        model = TagLearner(OnlineLearner(tag='tag', uuid='1234'))

        model.prefit(self.data,
                     self.flags,
                     self.labels)

        self.assertTrue(model.predict(['Aaaa Aaaa'], [[]])[0])
        self.assertFalse(model.predict(['Bbbb Bbbb'], [[]])[0])

    def test_attribute_learner_train_predict(self):
        model = LearnerAttributeClassifier(LearnerAttribute(tag='tag', uuid='1234'))

        model.prefit(self.data,
                     self.flags,
                     self.labels)

        self.assertTrue(model.predict(['Aaaa Aaaa'], [[]])[0])
        self.assertFalse(model.predict(['Bbbb Bbbb'], [[]])[0])


class OnlineLearnerTestCase(MLTestCase):

    @unittest.skip('Slow and not assert. Used only for benchmarking.')
    def test_benchmark(self):
        from ml.resources.online import JURISDICTION_DATASET_PARTYMASKED

        dataset = JURISDICTION_DATASET_PARTYMASKED

        N_ITERS = 10
        TEST_SIZE = 0.9

        X = [(txt, flgs) for txt, flgs, lbl in dataset]
        y = [lbl for txt, flgs, lbl in dataset]

        mean_precision = 0
        mean_recall = 0

        start_time = time.time()

        spl = StratifiedShuffleSplit(n_splits=N_ITERS, test_size=TEST_SIZE,
                                     random_state=42)
        # Providing y is sufficient for generating the splits,
        # but API requires some X with n_samples rows
        X_dummy = np.zeros(len(y))
        for train_index, test_index in spl.split(X_dummy, y):
            print('\nSplit: %d, %d' % (len(train_index), len(test_index)))
            model = TagLearner(OnlineLearner(tag='tag', uuid='1234'))

            n_train_pos = 0
            n_train_neg = 0
            # Train sample by sample
            for i in train_index:
                model.fit([X[i][0]], [X[i][1]], [y[i]])
                if y[i]:
                    n_train_pos += 1
                else:
                    n_train_neg += 1

            # Test on the whole test set after training on the whole train set
            correct = 0
            true_pos = 0
            true_neg = 0
            false_pos = 0
            false_neg = 0
            preds = []
            y_test = []

            for i in test_index:
                pred = model.predict([X[i][0]], [X[i][1]])[0]

                preds.append(pred)
                y_test.append(y[i])

                if pred == y[i]:
                    correct += 1
                    if pred:
                        true_pos += 1
                    else:
                        true_neg += 1
                else:
                    if pred:
                        false_pos += 1
                    else:
                        false_neg += 1

            precision = true_pos / float((true_pos + false_pos) or 0.00001)
            recall = true_pos / float((true_pos + false_neg) or 0.00001)
            mean_precision += precision
            mean_recall += recall

            print( '((Train set: %d pos  -  %d neg))' % (n_train_pos, n_train_neg))
            print( '((Test set:  %d pos  -  %d neg))' % (true_pos + false_neg, true_neg + false_pos))
            print( 'Precision: %.2f%% (%d/%d)' % (precision * 100, true_pos, true_pos + false_pos))
            print( 'Recall:    %.2f%% (%d/%d)' % (recall * 100, true_pos, true_pos + false_neg))
            accur = metrics.accuracy_score(y_test, preds)
            print( 'Accuracy: %0.3f' % accur)
            fscore = 2 * precision * recall / (precision + recall)
            print( 'F-Score:   %.2f%%' % (fscore * 100))

            print( 'Confusion matrix:')
            print( metrics.confusion_matrix(list(map(int, y_test)), list(map(int, preds))))

        finish_time = time.time()

        print( '\nElapsed:   %.3f s' % (finish_time - start_time))
        mean_precision /= float(N_ITERS)
        mean_recall /= float(N_ITERS)
        print()
        print( '--- ' * 22)
        print( 'Precision: %.2f%%' % (mean_precision * 100))
        print( 'Recall:    %.2f%%' % (mean_recall * 100))
        print( '--- ' * 22)
        fscore = 2 * mean_precision * mean_recall / (mean_precision + mean_recall)
        print( 'F-Score:   %.2f%%' % (fscore * 100))
        print( '--- ' * 22)
        print()

    @unittest.skip('Slow and not assert. Used only for plotting performance.')
    def test_plot_learning_curve(self):
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            self.skipTest('Plotting not available: matplotlib not installed')

        from ml.resources.online import JURISDICTION_DATASET_PARTYMASKED

        dataset = JURISDICTION_DATASET_PARTYMASKED

        N_ITERS = 5
        TEST_SIZE = 0.5

        X = [(txt, flgs) for txt, flgs, lbl in dataset]
        y = [lbl for txt, flgs, lbl in dataset]

        prec = None
        recl = None
        fscr = None

        spl = StratifiedShuffleSplit(n_splits=N_ITERS, test_size=TEST_SIZE,
                                     random_state=42)
        # Providing y is sufficient for generating the splits,
        # but API requires some X with n_samples rows
        X_dummy = np.zeros(len(y))
        for k, (train_index, test_index) in enumerate(spl.split(X_dummy, y)):
            print( '\nStarted iteration', (k + 1))
            print( 'Split: %d, %d' % (len(train_index), len(test_index)))
            model = TagLearner(OnlineLearner(tag='tag', uuid='1234'))

            n_train, n_test = len(train_index), len(test_index)

            # Train sample by sample
            for i, idx in enumerate(train_index):
                if i and i % 50 == 0:
                    print( '> %d/%d' % (i, n_train))

                model.fit([X[idx][0]], [X[idx][1]], [y[idx]])

                # Test on the whole test set after training on each single train sample
                true_pos = 0
                true_neg = 0
                false_pos = 0
                false_neg = 0

                for j in test_index:
                    pred = model.predict([X[j][0]], [X[j][1]])[0]

                    if pred == y[j]:
                        if pred:
                            true_pos += 1
                        else:
                            true_neg += 1
                    else:
                        if pred:
                            false_pos += 1
                        else:
                            false_neg += 1

                curr_prec = true_pos / float((true_pos + false_pos) or 0.00001)
                curr_recl = true_pos / float((true_pos + false_neg) or 0.00001)

                if not prec:
                    prec = [0.] * n_train
                if not recl:
                    recl = [0.] * n_train
                if not fscr:
                    fscr = [0.] * n_train

                prec[i] += curr_prec
                recl[i] += curr_recl
                fscr[i] += 2 * curr_prec * curr_recl / float((curr_prec + curr_recl) or 0.000001)

        # Plotting

        norm_fn = lambda x: x / float(N_ITERS)
        prec = list(map(norm_fn, prec))
        recl = list(map(norm_fn, recl))
        fscr = list(map(norm_fn, fscr))

        plt.plot(range(1, len(prec) + 1), prec, color='red', alpha=0.25, label='Precision')
        plt.plot(range(1, len(recl) + 1), recl, color='blue', alpha=0.25, label='Recall')
        plt.plot(range(1, len(fscr) + 1), fscr, color='green', label='F1')
        plt.title('OnlineLearner learning curve')
        plt.ylim([-0.1, 1.01])
        plt.xlabel('Number of train samples')
        plt.ylabel('Score')
        plt.legend(loc='lower right')
        plt.savefig('onlinelearner_learning_curve.png')

    def test_online_vectorizer_fit_transform_empty_flags(self):
        vectorizer = TagLearnerOnlineVectorizer('uuid', 'tag')
        vectorizer.fit([])
        featvec_len = vectorizer.transform('placeholder', 'Text', []).shape[1]

        self.assertEqual(featvec_len, vectorizer.SPARSE_FEATS_SIZE + 1)

    def test_offline_vectorizer_fit_transform_empty_flags(self):
        vectorizer = TagLearnerOfflineVectorizer('uuid', 'tag')
        vectorizer.fit(['Text the text', 'The rabbit', 'The text'], [])
        featvec_len = vectorizer.transform('placeholder', 'Text', []).shape[1]

        self.assertEqual(featvec_len, vectorizer.SPARSE_FEATS_SIZE + 1)

    def test_learner_get_all(self):
        initial = list(LearnerFacade.get_all(self.user))
        self.assertTrue(len(initial) == 0)

        LearnerFacade.get_or_create('tag1', self.user)
        all_clfs = list(LearnerFacade.get_all(self.user))
        self.assertTrue(len(all_clfs) == 1)

        # Get the previous tag again, shouldn't create a new one
        LearnerFacade.get_or_create('tag1', self.user)
        all_clfs = list(LearnerFacade.get_all(self.user))
        self.assertTrue(len(all_clfs) == 1)

        # Add another one
        LearnerFacade.get_or_create('tag2', self.user)
        all_clfs = list(LearnerFacade.get_all(self.user))
        self.assertTrue(len(all_clfs) == 2)

    def test_learner_add_samples(self):
        clf = LearnerFacade.get_or_create('tag1', self.user)

        sents = ['Ana.', 'Are.', 'Mere.']

        # Should leave only 1 infered negative sentence out of 2 provided,
        # because the first one already exists in the learner's dataset
        clf.train([Capsule(sents[0])], [True],
                  infered_negative_capsules=[Capsule(s) for s in sents[:2]])
        self.assertTrue(clf.db_model.positive_set_size == 1)
        self.assertTrue(clf.db_model.negative_set_size == 1)
        self.assertTrue(clf.db_model.infered_set_size == 1)

        clf.train([Capsule('Dummy sent.')], [True])
        clf.train([Capsule('Dummy negative sent.')], [False])
        self.assertTrue(clf.db_model.positive_set_size == 2)
        self.assertTrue(clf.db_model.negative_set_size == 2)
        self.assertTrue(clf.db_model.infered_set_size == 1)

    def test_learner_reset(self):
        model = TagLearner(OnlineLearner(tag='tag', uuid='1234'))

        for i in range(20):
            model.fit(['Aaaa Aaaa'], [[]], [True])
            model.fit(['Bbbb Bbbb'], [[]], [False])

        self.assertTrue(model.predict(['Aaaa Aaaa'], [[]])[0])
        self.assertFalse(model.predict(['Bbbb Bbbb'], [[]])[0])

        # Reset and train the other way around
        model.reset()

        for i in range(20):
            model.fit(['Aaaa Aaaa'], [[]], [False])
            model.fit(['Bbbb Bbbb'], [[]], [True])

        self.assertTrue(model.predict(['Bbbb Bbbb'], [[]])[0])
        self.assertFalse(model.predict(['Aaaa Aaaa'], [[]])[0])

    def test_learner_reset_initial_samples(self):
        model = TagLearner(OnlineLearner(tag='tag', uuid='1234'))

        for i in range(20):
            model.fit(['Aaaa Aaaa'], [[]], [True])
            model.fit(['Bbbb Bbbb'], [[]], [False])

        self.assertTrue(model.predict(['Aaaa Aaaa'], [[]])[0])
        self.assertFalse(model.predict(['Bbbb Bbbb'], [[]])[0])

        # Reset and retrain providing initial samples
        init_samples = []
        for i in range(20):
            init_samples.append(['Aaaa Aaaa', [], False])
            init_samples.append(['Bbbb Bbbb', [], True])

        model.reset(initial_samples=init_samples)

        self.assertTrue(model.predict(['Bbbb Bbbb'], [[]])[0])
        self.assertFalse(model.predict(['Aaaa Aaaa'], [[]])[0])

    def test_learner_remove_sample(self):
        clf = LearnerFacade.get_or_create('tag', self.user)

        sents = ['Aaaa Aaaa', 'Bbbb Bbbb', 'Cccc Cccc']

        clf.train([Capsule(sents[2])], [True],
                  infered_negative_capsules=[Capsule(s) for s in sents[:2]])
        self.assertTrue(clf.db_model.positive_set_size == 1)
        self.assertTrue(clf.db_model.negative_set_size == 2)
        self.assertTrue(clf.db_model.infered_set_size == 2)

        clf.remove_sample(Capsule(sents[2]))
        self.assertTrue(clf.db_model.positive_set_size == 0)
        self.assertTrue(clf.db_model.negative_set_size == 3)
        self.assertTrue(clf.db_model.infered_set_size == 2)

    def test_learner_get_active(self):
        all_clfs = [LearnerFacade.get_or_create(tag, self.user) for tag in ['A', 'B', 'C']]

        self.assertEqual(all_clfs, list(LearnerFacade.get_all(self.user)))

        clf = LearnerFacade.get_or_create('D', self.user)
        clf.db_model.active = False
        clf.db_model.save()

        self.assertEqual(all_clfs + [clf], list(LearnerFacade.get_all(self.user)))
        self.assertEqual(all_clfs, list(LearnerFacade.get_all(self.user, active_only=True)))

    def test_learner_get_mature(self):
        from ml.models import LEARNER_MATURITY_THRESHOLD

        all_clfs = [LearnerFacade.get_or_create(tag, self.user) for tag in ['A', 'B', 'C']]

        self.assertEqual(all_clfs, list(LearnerFacade.get_all(self.user)))

        clf = LearnerFacade.get_or_create('D', self.user)
        clf.db_model.pretrained = True
        clf.db_model.save()

        self.assertEqual(all_clfs + [clf], list(LearnerFacade.get_all(self.user)))
        self.assertEqual([clf], list(LearnerFacade.get_all(self.user, mature_only=True)))

        clf.db_model.pretrained = False
        clf.db_model.save()

        self.assertEqual(all_clfs + [clf], list(LearnerFacade.get_all(self.user)))
        self.assertEqual([], list(LearnerFacade.get_all(self.user, mature_only=True)))

        for idx in range(LEARNER_MATURITY_THRESHOLD):
            clf.db_model.add_sample(text='Sample %d' % (idx + 1), flags=[], label=True)

        self.assertEqual(all_clfs + [clf], list(LearnerFacade.get_all(self.user)))
        self.assertEqual([clf], list(LearnerFacade.get_all(self.user, mature_only=True)))

    def test_learner_get_deleted(self):
        all_clfs = [LearnerFacade.get_or_create(tag, self.user) for tag in ['A', 'B', 'C']]

        self.assertEqual(all_clfs, list(LearnerFacade.get_all(self.user)))

        clf = LearnerFacade.get_or_create('D', self.user)
        clf.db_model.deleted = True
        clf.db_model.save()

        self.assertEqual(all_clfs, list(LearnerFacade.get_all(self.user)))
        self.assertEqual(all_clfs + [clf], list(LearnerFacade.get_all(self.user, include_deleted=True)))

    def test_learner_fix_conflicts(self):
        clf = LearnerFacade.get_or_create('tag', self.user)

        sents = ['Aaaa Aaaa', 'Bbbb Bbbb', 'Cccc Cccc']

        clf.train([Capsule(sents[2])], [True],
                  infered_negative_capsules=[Capsule(s) for s in sents])
        self.assertTrue(clf.db_model.positive_set_size == 1)
        self.assertTrue(clf.db_model.negative_set_size == 2)
        self.assertTrue(clf.db_model.infered_set_size == 2)

        clf.train([Capsule(sents[0])], [True],
                  infered_negative_capsules=[Capsule(s) for s in sents])
        self.assertTrue(clf.db_model.positive_set_size == 2)
        self.assertTrue(clf.db_model.negative_set_size == 1)
        self.assertTrue(clf.db_model.infered_set_size == 1)

    def test_learner_samples_add_remove_workflow(self):
        clf = LearnerFacade.get_or_create('tag', self.user)

        sents = ['Aaaa Aaaa', 'Bbbb Bbbb', 'Cccc Cccc', 'Dddd Dddd']
        label_infered = [(False, False), (True, False), (False, False), (False, True)]

        clf.train([Capsule(sents[0])], [False])
        clf.train([Capsule(sents[1])], [True],
                  infered_negative_capsules=[Capsule(s) for s in sents])
        clf.remove_sample(Capsule(sents[1]))
        clf.train([Capsule(sents[2])], [True],
                  infered_negative_capsules=[Capsule(s) for s in sents])
        clf.remove_sample(Capsule(sents[2]))
        clf.train([Capsule(sents[1])], [True])

        samples = clf.db_model.samples
        actual = {txt: (lbl, infr) for txt, lbl, infr in
                  zip(samples['text'], samples['label'], samples['infered'])}
        expected = dict(zip(sents, label_infered))
        self.assertEqual(actual, expected)

    @mock.patch('ml.tests.S3BucketManagerMock.save_string',
                side_effect=S3BucketManagerMock.save_string)
    @mock.patch('ml.tests.S3BucketManagerMock.read_to_string',
                side_effect=S3BucketManagerMock.read_to_string)
    def test_ml_model_save_load_workflow(self, s3_load_mock, s3_save_mock):
        """
        Checks that a classifier's parameters are properly loaded
        (when available) from and saved to S3.
        """
        from django.conf import settings

        db_model = OnlineLearner(tag='beagle', owner=self.user)
        db_model.save()

        model_s3_path = 'online_learners/model_%s.pkl' % db_model.uuid

        self.assertEqual(db_model.model_s3,
                         '%s:%s' % (settings.PREDICTION_MODELS_BUCKET, model_s3_path))

        # The classifier is not trained yet, so no data can be loaded from S3
        clf = LearnerFacade.get_or_create('beagle', self.user)
        s3_load_mock.assert_called_once_with(model_s3_path)
        pickled_data_loaded = s3_load_mock(model_s3_path)
        self.assertIsNone(pickled_data_loaded)
        self.assertFalse(clf.ml_model.loaded_from_pkl)

        sents = ['Aaaa Aaaa', 'Bbbb Bbbb', 'Cccc Cccc']
        capsules = list(map(Capsule, sents))
        labels = [False, True, False]

        # Train the classifier and save its data to S3
        clf.train(capsules, labels)
        pickled_data_saved = s3_load_mock(model_s3_path)
        self.assertIsNotNone(pickled_data_saved)
        s3_save_mock.assert_called_once_with(model_s3_path, pickled_data_saved)

        s3_load_mock.reset_mock()

        # Try to load the classifier's data from S3 again
        clf = LearnerFacade.get_or_create('beagle', self.user)
        s3_load_mock.assert_called_once_with(model_s3_path)
        pickled_data_loaded = s3_load_mock(model_s3_path)
        self.assertIsNotNone(pickled_data_loaded)
        self.assertTrue(clf.ml_model.loaded_from_pkl)

        self.assertEqual(pickled_data_saved, pickled_data_loaded)
