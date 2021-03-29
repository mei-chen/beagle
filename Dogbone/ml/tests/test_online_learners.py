import mock
import unittest
from time import time

from django.conf import settings
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn import metrics

from core.models import Sentence
from dogbone.testing.base import BeagleWebTest
from ml.capsules import Capsule
from ml.clfs import TagLearner
from ml.exceptions import ModelNotFoundException
from ml.facade import LearnerFacade
from ml.models import OnlineLearner
from ml.resources.online import JURISDICTION_DATASET_PARTYMASKED
from ml.tasks import (
    onlinelearner_train_task,
    onlinelearner_removesample_task,
    onlinelearner_negative_train_task,
)


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
        if key not in cls.data:
            raise ModelNotFoundException
        return cls.data[key]


class OnlineLearnerTest(BeagleWebTest):

    @classmethod
    def setUpClass(cls):
        super(OnlineLearnerTest, cls).setUpClass()

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

        super(OnlineLearnerTest, cls).tearDownClass()

    @unittest.skip("Slow and not assert. Only benchmarking")
    def test_benchmark(self):
        dataset = JURISDICTION_DATASET_PARTYMASKED

        N_ITERS = 10
        TEST_SIZE = 0.9

        X = [(txt, tags) for txt, tags, lbl in dataset]
        y = [lbl for txt, tags, lbl in dataset]

        mean_precision = 0
        mean_recall = 0

        start_time = time()

        spl = StratifiedShuffleSplit(n_splits=N_ITERS, test_size=TEST_SIZE, random_state=42)
        # Providing y is sufficient for generating the splits,
        # but API requires some X with n_samples rows
        X_dummy = np.zeros(len(y))
        for train_index, test_index in spl.split(X_dummy, y):
            print('\nSplit: %d, %d' % (len(train_index), len(test_index)))
            model = TagLearner(OnlineLearner(tag='tag', model_uuid='1234'))

            n_train_pos = 0
            n_train_neg = 0
            # Train sample by sample
            for i in train_index:
                model.fit([X[i][0]], [X[i][1]], [y[i]])
                if y[i]:
                    n_train_pos += 1
                else:
                    n_train_neg += 1

            # Test sample by sample
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

            print('((Train set: %d pos  -  %d neg))' % (n_train_pos, n_train_neg))
            print('((Test set:  %d pos  -  %d neg))' % (true_pos + false_neg, true_neg + false_pos))
            print('Precision: %.2f%% (%d/%d)' % (precision * 100, true_pos, true_pos + false_pos))
            print('Recall:    %.2f%% (%d/%d)' % (recall * 100, true_pos, true_pos + false_neg))
            accur = metrics.accuracy_score(y_test, preds)
            print('Accuracy: %0.3f' % accur)
            fscore = 2 * precision * recall / (precision + recall)
            print('F-Score:   %.2f%%' % (fscore * 100))

            print("Confusion matrix:")
            print(metrics.confusion_matrix(list(map(int, y_test)), list(map(int, preds))))

        print('\nElapsed:   %.3f s' % (time() - start_time ))
        mean_precision /= float(N_ITERS)
        mean_recall /= float(N_ITERS)
        print()
        print('--- ' * 22)
        print('Precision: %.2f%%' % (mean_precision * 100))
        print('Recall:    %.2f%%' % (mean_recall * 100))
        print('--- ' * 22)
        fscore = 2 * mean_precision * mean_recall / (mean_precision + mean_recall)
        print('F-Score:   %.2f%%' % (fscore * 100))

    @unittest.skip("Slow and not assert. Use just for plotting clf's performance")
    def test_plot_learncurve(self):
        dataset = JURISDICTION_DATASET_PARTYMASKED

        N_ITERS = 5
        TEST_SIZE = 0.5

        X = [(txt, tags) for txt, tags, lbl in dataset]
        y = [lbl for txt, tags, lbl in dataset]

        prec = None
        recl = None
        fscr = None

        # Plot learning curve
        spl = StratifiedShuffleSplit(n_splits=N_ITERS, test_size=TEST_SIZE, random_state=42)
        # Providing y is sufficient for generating the splits,
        # but API requires some X with n_samples rows
        X_dummy = np.zeros(len(y))
        for k, (train_index, test_index) in enumerate(spl.split(X_dummy, y)):
            print('\nStarted iteration', (k + 1))
            print('Split: %d, %d' % (len(train_index), len(test_index)))
            model = TagLearner(OnlineLearner(tag='tag', model_uuid='1234'))

            n_train, n_test = len(train_index), len(test_index)

            # Train sample by sample
            for i, idx in enumerate(train_index):
                if i and i % 50 == 0:
                    print('> %d/%d' % (i, n_train))

                model.fit([X[idx][0]], [X[idx][1]], [y[idx]])

                # Test on the whole test set
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
        import pylab as plt

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
        plt.savefig('onlinelearner_learncurve_partymasked.png')

    def test_online_vectorizer_fit_transform_emptyflags(self):
        from ml.vecs import TagLearnerOnlineVectorizer
        vectorizer = TagLearnerOnlineVectorizer('uuid', 'tag')
        vectorizer.fit([])
        featvec_len = vectorizer.transform('T', 'Text', []).shape[1]

        self.assertEqual(featvec_len, vectorizer.SPARSE_FEATS_SIZE + 1)

    def test_offline_vectorizer_fit_transform_emptyflags(self):
        from ml.vecs import TagLearnerOfflineVectorizer
        vectorizer = TagLearnerOfflineVectorizer('uuid', 'tag')
        vectorizer.fit(['Text the text', 'The rabbit', 'The text'], [])
        featvec_len = vectorizer.transform('The', 'Text', []).shape[1]

        self.assertEqual(featvec_len, vectorizer.SPARSE_FEATS_SIZE + 1)

    def test_component_get_all(self):
        initial = list(LearnerFacade.get_all(self.user))
        self.assertTrue(len(initial) == 0)

        LearnerFacade.get_or_create('tag1', self.user)
        all_clfs = list(LearnerFacade.get_all(self.user))
        self.assertTrue(len(all_clfs) == 1)

        # Get the previous tag again. Shouldn't create a new one
        LearnerFacade.get_or_create('tag1', self.user)
        all_clfs = list(LearnerFacade.get_all(self.user))
        self.assertTrue(len(all_clfs) == 1)

        # Add another one
        LearnerFacade.get_or_create('tag2', self.user)
        all_clfs = list(LearnerFacade.get_all(self.user))
        self.assertTrue(len(all_clfs) == 2)

    def test_component_add_samples(self):
        clf = LearnerFacade.get_or_create('tag1', self.user)

        sentences = ['Ana.', 'Are.', 'Mere.']
        doc = self.create_analysed_document('fname', sentences, self.user)
        sents = doc.get_sorted_sentences()
        ps = doc.get_parties()
        sent1 = sents[0]

        clf.train([Capsule(sent1.text, idx=0, parties=ps)], [True],
                  infer_negatives=True, all_capsules=[(Capsule(s.text), s.get_tags()) for s in sents])
        self.assertTrue(clf.db_model.positive_set_size == 1)

        clf.train([Capsule('Dummy sent.')], [True])
        clf.train([Capsule('Dummy negative sent.')], [False])
        self.assertTrue(clf.db_model.positive_set_size == 2)

    def test_component_mask_parties(self):
        clf = LearnerFacade.get_or_create('tag', self.user)

        sentences = ['Ana Blandiana.', 'Are.', 'Mere.']
        doc = self.create_analysed_document('fname', sentences, self.user)
        doc.doclevel_analysis['parties'] = {
            'them': {
                'name': 'Ana',
                'confidence': 1.,
            },
            'you': {
                'name': 'Mere',
                'confidence': 1.,
            }
        }
        doc.save()
        sents = doc.get_sorted_sentences()
        ps = doc.get_parties()
        sent1 = sents[0]

        clf.train([Capsule(sent1.text, idx=0, parties=ps)], [True],
                  infer_negatives=True, all_capsules=[(Capsule(s.text), s.get_tags()) for s in sents])
        self.assertTrue(clf.db_model.positive_set_size == 1)

        self.assertEqual(clf.db_model.samples['text'][0], '__THEM_PARTY__ Blandiana.')

    def test_reset_learner(self):
        model = TagLearner(OnlineLearner(tag='tag', model_uuid='1234'))

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

    def test_reset_learner_initial_samples(self):
        model = TagLearner(OnlineLearner(tag='tag', model_uuid='1234'))

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

    def test_learner_remove_tag_by_idx(self):
        clf = LearnerFacade.get_or_create('tag', self.user)

        for i in range(20):
            clf.train([Capsule('Aaaa Aaaa')], [True])
            clf.train([Capsule('Bbbb Bbbb')], [False])

        self.assertTrue(clf.predict([Capsule('Aaaa Aaaa')]))
        self.assertFalse(clf.predict([Capsule('Bbbb Bbbb')]))

        # Reset and retrain providing initial samples
        for i in range(20):
            clf._remove_positive_sample_by_idx(2 * i)

        self.assertFalse(clf.predict([Capsule('Aaaa Aaaa')]))

    def test_learner_remove_tag(self):
        sentences = ['Aaaa Aaaa', 'Bbbb Bbbb', 'Cccc Cccc']
        doc = self.create_analysed_document('original_filename', sentences, self.user)
        sents = doc.get_sorted_sentences()
        ps = doc.get_parties()
        s3 = sents[2]

        clf = LearnerFacade.get_or_create('tag', self.user)
        clf.train([Capsule(s3.text, idx=2, parties=ps)], [True],
                  infer_negatives=True, all_capsules=[(Capsule(s.text), s.get_tags()) for s in sents])
        clf.remove_sample(Capsule(s3.text, idx=2, parties=ps))

        self.assertFalse(any(clf.db_model.samples['label']))

    def test_learner_get_deleted(self):
        all_clfs = list(LearnerFacade.get_all(self.user))

        clf = LearnerFacade.get_or_create('unique_tag00', self.user)
        clf.db_model.deleted = True
        clf.db_model.save()

        self.assertEqual(all_clfs, list(LearnerFacade.get_all(self.user)))
        self.assertNotEqual(all_clfs, list(LearnerFacade.get_all(self.user, include_deleted=True)))

    def test_learner_get_active(self):
        all_clfs = list(LearnerFacade.get_all(self.user))

        clf = LearnerFacade.get_or_create('unique_tag01', self.user)
        clf.db_model.active = False
        clf.db_model.save()

        self.assertNotEqual(all_clfs, list(LearnerFacade.get_all(self.user)))
        self.assertEqual(all_clfs, list(LearnerFacade.get_all(self.user, active_only=True)))

    def test_learner_conflicts(self):
        sentences = ['Aaaa Aaaa', 'Bbbb Bbbb', 'Cccc Cccc']
        doc = self.create_analysed_document('original_filename', sentences, self.user)
        sents = doc.get_sorted_sentences()
        ps = doc.get_parties()
        s1 = sents[0]
        s3 = sents[2]

        fcd = LearnerFacade.get_or_create('tag', self.user)

        s3.add_tag(user=None, label='tag')
        fcd.train([Capsule(s3.text, idx=2, parties=ps)], [True],
                  infer_negatives=True, all_capsules=[(Capsule(s.text), s.get_tags()) for s in sents])

        s1.add_tag(user=None, label='tag')
        fcd.train([Capsule(s1.text, idx=0, parties=ps)], [True],
                  infer_negatives=True, all_capsules=[(Capsule(s.text), s.get_tags()) for s in sents])

        self.assertEqual(sorted(fcd.db_model.samples['label']), [False, True, True])

    def test_train_using_celery_tasks(self):
        sentences = ['Aaaa Aaaa', 'Bbbb Bbbb', 'Cccc Cccc', 'Dddd Dddd']
        doc = self.create_analysed_document('original_filename', sentences, self.user)
        s1 = Sentence.objects.get(pk=doc.sentences_pks[0])
        s2 = Sentence.objects.get(pk=doc.sentences_pks[1])
        s3 = Sentence.objects.get(pk=doc.sentences_pks[2])

        onlinelearner_negative_train_task('tag', self.user, s1, 0)
        onlinelearner_train_task('tag', self.user, s2, 1)
        onlinelearner_train_task('tag', self.user, s3, 2)
        onlinelearner_removesample_task('tag', self.user, s3, 2)

        olmodel = OnlineLearner.objects.get(owner=self.user, tag='tag')
        samples = {txt: (lbl, infr) for txt, lbl, infr in zip(olmodel.samples['text'],
                                                              olmodel.samples['label'],
                                                              olmodel.samples['infered'])}
        groundtruth = {
            'Aaaa Aaaa': (False, False),
            'Bbbb Bbbb': (True, False),
            'Cccc Cccc': (False, False),
            'Dddd Dddd': (False, True)
        }

        self.assertEqual(samples, groundtruth)

    def test_ml_model_save_load_workflow(self):
        """
        Checks that a classifier's parameters are properly loaded
        (when available) from and saved to S3.
        """
        db_model = OnlineLearner(tag='sometag', owner=self.user)
        db_model.save()

        model_s3_path = 'online_learners/model_%s.pkl' % db_model.model_uuid

        self.assertEqual(db_model.model_s3,
                         '%s:%s' % (settings.PREDICTION_MODELS_BUCKET, model_s3_path))

        sentences = ['Aaaa Aaaa', 'Bbbb Bbbb', 'Cccc Cccc', 'Dddd Dddd']
        doc = self.create_analysed_document('original_filename', sentences, self.user)
        s1 = Sentence.objects.get(pk=doc.sentences_pks[0])
        s2 = Sentence.objects.get(pk=doc.sentences_pks[1])
        s3 = Sentence.objects.get(pk=doc.sentences_pks[2])

        # Temporarily disable patching
        self.save_online_model_patcher.stop()
        self.load_models_patcher.stop()

        with mock.patch('ml.models.get_s3_bucket_manager',
                        side_effect=S3BucketManagerMock):
            onlinelearner_negative_train_task('sometag', self.user, s1, 0)
            onlinelearner_train_task('sometag', self.user, s2, 1)
            onlinelearner_train_task('sometag', self.user, s3, 2)

            with mock.patch('ml.tests.test_online_learners.S3BucketManagerMock.save_string',
                            side_effect=S3BucketManagerMock.save_string) as s3_save_mock, \
                 mock.patch('ml.tests.test_online_learners.S3BucketManagerMock.read_to_string',
                            side_effect=S3BucketManagerMock.read_to_string) as s3_load_mock:
                facade = LearnerFacade.get_or_create('sometag', self.user)
                s3_load_mock.assert_called_once_with(model_s3_path)
                pickled_data = s3_load_mock(model_s3_path)
                facade.ml_model.save_online_model()
                s3_save_mock.assert_called_once_with(model_s3_path, pickled_data)

        # Enable patching again
        self.load_models_patcher.start()
        self.save_online_model_patcher.start()
