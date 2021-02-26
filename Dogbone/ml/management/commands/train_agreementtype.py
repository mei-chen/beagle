import numpy as np
from os import path, sep
from glob import glob
import cPickle as pkl
from unidecode import unidecode

from django.core.management.base import BaseCommand
from ml.clfs import AgreementTypeClassifier

from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import f1_score, precision_score, recall_score


class Command(BaseCommand):
    help = '''(Re)trains the agreement_type classifier (for the moment it's
              NDA/Other binary classification)'''

    def handle(self, *args, **options):
        datasets_path = path.join(path.dirname(path.dirname(path.dirname(
                                      path.abspath(__file__)))),
                                  'resources',
                                  'agreementtype_dataset'
                        )
        nda_path   = path.join(datasets_path, 'nda', '*')
        other_path = path.join(datasets_path, 'other', '*')

        # Read data
        ndas = []
        for filename in glob(nda_path):
            if filename.endswith('.txt'):
                with open(filename) as txtin:
                    ndas.append(unidecode(txtin.read()))
        others = []
        for filename in glob(other_path):
            if filename.endswith('.txt'):
                with open(filename) as txtin:
                    others.append(unidecode(txtin.read()))
        # Collect all data
        X = ndas + others
        y = [True] * len(ndas) + [False] * len(others)

        # Split data into train/test
        N_ITERS = 10
        TEST_SIZE = 0.3
        spl = StratifiedShuffleSplit(n_splits=N_ITERS, test_size=TEST_SIZE, random_state=42)

        best_clf  = None
        best_fscr = 0.

        # Providing y is sufficient for generating the splits,
        # but API requires some X with n_samples rows
        X_dummy = np.zeros(len(y))
        for k, (train_index, test_index) in enumerate(spl.split(X_dummy, y)):
            print 'Started iteration', (k + 1)
            print 'Split: %d, %d' % (len(train_index), len(test_index))

            # Gather the splitted data
            train_set = []
            test_set_pos = []
            test_set_neg = []
            y_train = []
            for i in train_index:
                train_set.append(X[i])
                y_train.append(y[i])
            for i in test_index:
                if y[i]:
                    test_set_pos.append(X[i])
                else:
                    test_set_neg.append(X[i])
            test_set = test_set_pos + test_set_neg[:len(test_set_pos)]
            y_test = [True] * len(test_set_pos) + [False] * len(test_set_pos)

            print 'TRAIN:', len(train_set)
            print '       Pos:', len(filter(lambda x: x, y_train)), ' Neg:', len(filter(lambda x: not x, y_train))
            print 'TEST: ', len(test_set)
            print '       Pos:', len(filter(lambda x: x, y_test)), ' Neg:', len(filter(lambda x: not x, y_test))
            print

            # -- Train --
            # Init classifier
            clf = AgreementTypeClassifier()
            clf.fit(train_set, y_train)
            # -- Eval --
            y_pred = clf.predict(test_set)
            print 'Precision:', precision_score(y_test, y_pred)
            print 'Recall:   ', recall_score(y_test, y_pred)
            fscr = f1_score(y_test, y_pred)
            print 'F-score:  ', fscr

            if fscr > best_fscr:
                best_fscr = fscr
                best_clf  = clf

            # for i, (pr, gl) in enumerate(zip(y_pred, y_test)):
            #     if pr != gl:
            #         print '-------- ' * 5
            #         print test_set[i][:200]
            #         print 'Pred:', pr
            #         print 'Gold:', gl
            #         print

        print
        print '-'*80
        print 'Best F-score:', best_fscr

        # Store the best classifier's components
        model_path = path.join(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))), 'models', 'agreement_type', 'model.pkl')
        print
        print 'Storing AgreementType model to: %s' % model_path
        with open(model_path, 'wb') as model_out:
            pkl.dump((best_clf.model.coef_, best_clf.model.intercept_, best_clf.model._enc.classes_), model_out)

        vec_path = path.join(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))), 'models', 'agreement_type', 'vectorizer.pkl')
        print
        print 'Storing AgreementType vectorizer to: %s' % vec_path
        with open(vec_path, 'wb') as vec_out:
            pkl.dump(best_clf.vectorizer, vec_out)
