import json
from os import path, sep
from glob import glob
from copy import deepcopy
import numpy as np

from django.core.management.base import BaseCommand
from ml.facade import LearnerFacade
from ml.capsules import Capsule
from ml.models import PretrainedLearner

from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import f1_score, precision_score, recall_score


class Command(BaseCommand):
    help = 'Trains and saves the default global (pretrained) learners to the DB'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            dest='retrain',
            help='Force the pretrained learners to get retrained'
        )

    def handle(self, *args, **options):
        datasets_path = path.join(
            path.dirname(path.dirname(path.dirname(path.abspath(__file__)))),
            'resources',
            'pretrain_datasets',
            '*'
        )

        print
        print '=' * 80
        print

        for filename in sorted(glob(datasets_path)):
            if not filename.endswith('.json'):
                continue

            tag = filename.split(sep)[-1][:-5].lower()

            if PretrainedLearner.objects.filter(tag=tag).exists() and not options['retrain']:
                print 'Model already trained [%s]' % tag

            else:
                with open(filename) as jsin:
                    dataset = json.load(jsin)

                    clf = LearnerFacade.get_or_create(tag)

                    if not clf.ml_model.loaded_from_pkl or options['retrain']:
                        print '%s model [%s]' % ('Retraining' if clf.ml_model.loaded_from_pkl else '\nTraining', tag)
                        print

                        # --- Train ---
                        X_text  = [d[0] for d in dataset]
                        X_flags = [d[1] for d in dataset]
                        y       = [d[2] for d in dataset]

                        spl = StratifiedShuffleSplit(n_splits=10, test_size=0.2, random_state=42)

                        candidates = []
                        scores = []
                        # Providing y is sufficient for generating the splits,
                        # but API requires some X with n_samples rows
                        X_dummy = np.zeros(len(y))
                        for train_index, test_index in spl.split(X_dummy, y):
                            print 'Split: %d, %d' % (len(train_index), len(test_index))

                            train_text = [X_text[i] for i in train_index]
                            train_flags = [X_flags[i] for i in train_index]
                            train_y = [y[i] for i in train_index]

                            clf_candidate = deepcopy(clf)
                            clf_candidate.ml_model.prefit(train_text, train_flags, train_y)

                            # --- Evaluate ---
                            texts = [Capsule(dataset[k][0], flags=dataset[k][1]) for k in test_index]
                            gold = [dataset[k][2] for k in test_index]
                            pred = clf_candidate.predict(texts)

                            f1score = f1_score(gold, pred)
                            print 'Precision:', precision_score(gold, pred)
                            print 'Recall:   ', recall_score(gold, pred)
                            print 'F1 score: ', f1score
                            print

                            candidates.append(clf_candidate)
                            scores.append(f1score)

                        i = np.argmax(scores)
                        clf = candidates[i]
                        print '-' * 80
                        print
                        print 'Picked the model [%s] with the best F1 score:' % tag, scores[i]
                        print

                        print 'Saving the ML model'
                        clf.ml_model.save_offline_model()
                        print 'Saving the ML vectorizer'
                        clf.ml_model.offline_vectorizer.save_model()
                        print 'Saving the DB model'
                        clf.db_model.save()

                    else:
                        print 'Model already trained [%s]' % tag

            print
            print '=' * 80
            print
