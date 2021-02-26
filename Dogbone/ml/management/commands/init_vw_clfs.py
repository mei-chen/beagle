import json
from os import path
from glob import glob
from copy import deepcopy
import numpy as np

from django.core.management.base import BaseCommand
from ml.facade import LearnerFacade
from ml.capsules import Capsule
from clauses_statistics.models import ClausesStatistic

from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import f1_score, precision_score, recall_score


class Command(BaseCommand):
    help = 'Puts the VW pretrained learners in the database'

    def handle(self, *args, **options):
        datasets_path = path.join(path.dirname(path.dirname(path.dirname(path.dirname(
                                        path.abspath(__file__))))),
                                  'datasets',
                                  'VW_pretrain_*'
                        )

        for filename in glob(datasets_path):
            if filename.endswith('.json'):
                with open(filename) as jsin:
                    tag = filename.split('VW_pretrain_')[-1][:-5]
                    dataset = json.load(jsin)
                    clf = LearnerFacade.get_or_create(tag)

                    if not clf.ml_model.loaded_from_pkl:
                        # --- Train ---
                        X_text  = [d['text'] for d in dataset]
                        y       = [d['label'] for d in dataset]

                        spl = StratifiedShuffleSplit(n_splits=10, test_size=0.2, random_state=42)

                        candidates = []
                        scores = []
                        # Providing y is sufficient for generating the splits,
                        # but API requires some X with n_samples rows
                        X_dummy = np.zeros(len(y))
                        for train_index, test_index in spl.split(X_dummy, y):
                            print 'Split: %d, %d' % (len(train_index), len(test_index))

                            train_text = [X_text[i] for i in train_index]
                            train_y = [y[i] for i in train_index]

                            clf_candidate = deepcopy(clf)
                            clf_candidate.ml_model.prefit(train_text, [[]] * len(train_y), train_y)

                            # --- Evaluate ---
                            texts = [Capsule(dataset[k]['text']) for k in test_index]
                            gold = [dataset[k]['label'] for k in test_index]
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
                        print
                        print '-' * 80
                        print 'Picked the model [%s] with Fscore:' % tag, scores[i]
                        print

                        print 'Saving the ML model and the ML vectorizer'
                        clf.ml_model.save_models()
                        print 'Saving the DB model'
                        clf.db_model.exclusivity = 'vw'
                        clf.db_model.save()

                        # Redo the ClausesStatistic whether or not it already exists
                        cstat = ClausesStatistic.objects.get_or_create(tag=tag)[0]
                        cstat.set_avgwordcount([d['text'] for d in dataset if d['label']])
                        print 'ClausesStatistic regenerated for [%s]: %d' % (tag, cstat.avg_word_count)
                    else:
                        print 'Model already trained [%s]' % tag
                        print 'The DB instance was added successfully'

                        # Check if the ClausesStatistic should be generated
                        if not ClausesStatistic.objects.filter(tag=tag).exists():
                            cstat = ClausesStatistic(tag=tag)
                            cstat.set_avgwordcount([d[0] for d in dataset if d[2]])
                            print 'ClausesStatistic generated for [%s]: %d' % (tag, cstat.avg_word_count)
