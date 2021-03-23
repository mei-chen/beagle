import json
import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle

from experiment.models import BuiltInClassifier
from ml.models import MODEL_TYPES


DATASETS_DIR = os.path.join(settings.BASE_DIR, 'ml', 'resources',
                            'pretrain_datasets')

TRAIN_SIZE = 0.8
RANDOM_STATE = 42


class Command(BaseCommand):
    help = 'Selects the best-performing ML model for a specific built-in ' + \
           'dataset and saves it to the DB as an instance of BuiltInClassifier'

    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--dataset',
            choices=['Jurisdiction', 'Termination'],
            required=True,
            help='A dataset to train the built-in classifier on'
        )
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            dest='retrain',
            help='Force the built-in classifier to get retrained'
        )

    def log_error(self, message):
        print(self.style.ERROR(message))

    def log_debug(self, message):
        print(message)

    def log_success(self, message):
        print(self.style.SUCCESS(message))

    def handle(self, *args, **options):
        dataset = options['dataset']

        # Create a temporary clf needed only for accessing the global model
        clf = BuiltInClassifier(model=dataset)

        if clf.trained and not options['retrain']:
            self.log_error('The built-in classifier is already trained. ' +
                           'Use -f or --force to retrain it.')
            return

        with open(os.path.join(DATASETS_DIR, dataset + '.json')) as jsin:
            dataset = json.load(jsin)

        # Discard flags
        X, _, y = zip(*dataset)

        # Imitate experiment.tasks.train_classifier

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, train_size=TRAIN_SIZE, stratify=y, random_state=RANDOM_STATE
        )

        X_train, y_train = shuffle(X_train, y_train, random_state=RANDOM_STATE)
        X_test, y_test = shuffle(X_test, y_test, random_state=RANDOM_STATE)

        model_types_and_scores = []

        for model_type in MODEL_TYPES:
            self.log_debug('Training %s model...' % MODEL_TYPES[model_type])
            start = time.time()
            clf.fit(X_train, y_train, model_type=model_type, persist=False)
            end = time.time()
            self.log_debug('Elapsed: %.3fs' % (end - start))
            model_score = f1_score(y_test, clf.predict(X_test))
            self.log_debug('F1: %.5f\n' % model_score)
            model_types_and_scores.append((model_type, model_score))

        # unpack tuple and get max
        best_model_type, best_model_score = max(
            model_types_and_scores,
            key=lambda m: m[1]
        )

        self.log_debug('Saving...\n')

        # Train the clf again and finally save the best model found
        clf.fit(X_train, y_train, model_type=best_model_type)

        self.log_success('Best model: %s (%.5f)' %
                         (MODEL_TYPES[best_model_type], best_model_score))
