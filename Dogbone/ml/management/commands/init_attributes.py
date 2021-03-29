import json
import numpy as np
from os import path, sep
from glob import glob
from copy import deepcopy
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from ml.clfs import LearnerAttributeClassifier
from ml.facade import LearnerFacade
from ml.models import LearnerAttribute

from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import f1_score, precision_score, recall_score


class Command(BaseCommand):
    help = 'Installs the ML learner attributes for the pretrained learners'

    option_list = BaseCommand.option_list + (
        make_option('--tag', help='The tag of the pretrained learner whose attributes are installed'),
    )

    def handle(self, *args, **options):

        def check_dataset(data, value_range):
            valid = True
            for i, (sample, flags, label) in enumerate(data):
                if label not in value_range:
                    print()
                    print('ERROR: Sample %d has invalid label: %s')
                    print('   ', sample)
                    print('-' * 90)
                    valid = False
            return valid


        datasets_path = path.join(path.dirname(path.dirname(path.dirname(
                                        path.abspath(__file__)))),
                                  'resources',
                                  'attribute_datasets'
                        )

        tag = None
        if 'tag' in options:
            if not options['tag']:
                raise CommandError('Please specify a tag name, using the --tag option')
            tag = options['tag']
            datasets_path = path.join(datasets_path, tag)
        datasets_path = path.join(datasets_path, '*')

        print()
        print('Installing attributes for [%s]' % tag)

        for filename in glob(datasets_path):
            if filename.endswith('.json'):
                with open(filename) as jsin:
                    attr = filename.split(sep)[-1][:-5]
                    dataset = json.load(jsin)
                    fcd = LearnerFacade.get_or_create(tag)
                    ptcomp = fcd.get_pretrained_component()

                    if 'value_range' not in dataset:
                        raise CommandError('[%s/%s] Malformed dataset. No "value_range" specified.' % (tag, attr))
                    if 'data' not in dataset:
                        raise CommandError('[%s/%s] Malformed dataset. No "data" specified.' % (tag, attr))

                    value_range = dataset['value_range']
                    data = dataset['data']
                    if not check_dataset(data, value_range):
                        raise CommandError('[%s/%s] Invalid label in dataset' % (tag, attr))

                    attr_db = LearnerAttribute(name=attr,
                                               parent_learner=ptcomp,
                                               tag=tag,
                                               output_range=value_range)
                    if 'description' in dataset:
                        attr_db.description = dataset['description']

                    attr_clf = LearnerAttributeClassifier(attr_db)

                    if ptcomp:
                        # --- Train ---
                        X_text  = [d[0] for d in data]
                        X_flags = [d[1] for d in data]
                        y       = [d[2] for d in data]

                        spl = StratifiedShuffleSplit(n_splits=10, test_size=0.2, random_state=42)

                        candidates = []
                        scores = []
                        # Providing y is sufficient for generating the splits,
                        # but API requires some X with n_samples rows
                        X_dummy = np.zeros(len(y))
                        for train_index, test_index in spl.split(X_dummy, y):
                            print('Split: %d, %d' % (len(train_index), len(test_index)))

                            train_text = [X_text[i] for i in train_index]
                            train_flags = [X_flags[i] for i in train_index]
                            train_y = [y[i] for i in train_index]

                            clf_candidate = deepcopy(attr_clf)
                            clf_candidate.prefit(train_text, train_flags, train_y)

                            # --- Evaluate ---
                            test_text = [X_text[i] for i in test_index]
                            test_flags = [X_flags[i] for i in test_index]
                            gold = [data[k][2] for k in test_index]
                            pred = clf_candidate.predict(test_text, test_flags)

                            f1score = f1_score(gold, pred)
                            print('Precision:', precision_score(gold, pred))
                            print('Recall:   ', recall_score(gold, pred))
                            print('F1 score: ', f1score)
                            print()

                            candidates.append(clf_candidate)
                            scores.append(f1score)

                        i = np.argmax(scores)
                        attr_clf = candidates[i]
                        print()
                        print('-' * 80)
                        print('Picked the model [%s/%s] with Fscore:' % (tag, attr), scores[i])
                        print()

                        print('Saving the ML model and vectorizer')
                        attr_clf.save_models()
                        print('Saving the DB model')
                        attr_db.save()
                    else:
                        print('Pretrained Learner model doesn\'t exist [%s]' % tag)
                        print('Attribute [%s] was not installed' % attr)
                        print()
