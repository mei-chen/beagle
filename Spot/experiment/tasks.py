from __future__ import absolute_import, unicode_literals

import bisect
import itertools
import operator

# App
from dataset.models import Dataset, DatasetMapping
from experiment.models import (
    Experiment,
    get_classifer,
    REGEX_CLF, TRAINED_CLF,
)
from ml.capsules import Capsule
from ml.clfs import TagLearner
from ml.facade import LearnerFacade
from ml.models import OnlineLearner
from realtime.notify import NotificationManager

# Celery
from celery import shared_task
from celery.utils.log import get_task_logger

# Django
from django.contrib.auth.models import User

# NumPy
import numpy as np

# SciKit-Learn
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle

logger = get_task_logger(__name__)


MAX_WINDOW_SIZE = 14
DATASET_PREVIEW_SIZE = 10
HISTOGRAM_BINS = 15
RANDOM_STATE = 42


# Experiment API


def _text2tokens(text):
    return text.split()


def _tokens2text(tokens):
    return ' '.join(tokens)


def _apply_sliding_window(tokens, window_size):
    windows = []
    for from_index in range(len(tokens) - window_size + 1):
        to_index = from_index + window_size
        window = _tokens2text(tokens[from_index : to_index])
        windows.append(window)
    return windows


def _calculate_importance_scores(prediction, windows_predictions, window_size):
    scores = np.zeros(len(windows_predictions) + window_size - 1)
    for from_index, window_prediction in enumerate(windows_predictions):
        if prediction == window_prediction:
            to_index = from_index + window_size
            for index in range(from_index, to_index):
                scores[index] += 1
    return scores / window_size


@shared_task
def simulate_classification(session_key, experiment_pk, sample, task_uuid):
    logger.info("Simulating classification by Experiment(pk=%s) on sample:\n%r",
                experiment_pk, sample)

    try:
        experiment = Experiment.objects.get(pk=experiment_pk)
    except Experiment.DoesNotExist:
        logger.error("Could not find Experiment(pk=%s)", experiment_pk)
        return False

    prediction, confidence, prediction_per_clf = experiment.predict(
        [sample], with_confidence=True, per_classifier=True
    )
    prediction = prediction[0]
    confidence = confidence[0]

    # Also make sure to convert the status to `bool`,
    # since `numpy.bool_` "is not JSON serializable".
    status = bool(prediction)

    payload = {
        'task_uuid': task_uuid,
        'notification': NotificationManager.ServerNotifications.EXPERIMENT_SIMULATED_NOTIFICATION,
        'results': {
            'status': status,
            'confidence': confidence
        }
    }

    # Return immediately as soon as all the classifiers predict False
    if not status and np.isclose(confidence, 1):
        message = NotificationManager.notify_client(session_key, payload)
        return message.send()

    # Otherwise there is at least one classifier which predicts True

    # Calculate per-word importance scores by cropping parts of the sample
    # (using sliding windows of different sizes) and checking
    # whether obtained predictions stay the same

    tokens = _text2tokens(sample)

    per_clf = len(prediction_per_clf) > 1
    if per_clf:
        for clf_prediction in prediction_per_clf:
            clf_prediction['status'] = bool(
                clf_prediction.pop('predictions')[0]
            )
            # Augment the appropriate per-classifier payloads
            clf = clf_prediction['classifier']
            clf_prediction['name'] = clf.name
            clf_prediction['type'] = clf.clf_type
            clf_prediction['uuid'] = str(clf.uuid)

    scores = []
    if per_clf:
        scores_per_clf = [[] if clf_prediction['status'] else None
                          for clf_prediction in prediction_per_clf]
    for window_size in range(1, min(len(tokens), MAX_WINDOW_SIZE) + 1):
        window_weight = min(1, 1 - (window_size - 5) / 10.)
        if window_weight <= 0:
            break
        windows = _apply_sliding_window(tokens, window_size)
        if per_clf:
            windows_predictions, windows_predictions_per_clf = \
                experiment.predict(windows, per_classifier=True)
        else:
            windows_predictions = experiment.predict(windows)
        scores.append(
            window_weight * _calculate_importance_scores(
                prediction, windows_predictions, window_size
            )
        )
        if per_clf:
            for clf_prediction, clf_windows_predictions, clf_scores in \
                    itertools.izip(prediction_per_clf,
                                   windows_predictions_per_clf,
                                   scores_per_clf):
                if clf_prediction['status']:
                    # Don't apply sliding windows for individual regex
                    # classifiers (i.e. simply highlight matching parts
                    # of the sample instead of computing some window-based
                    # importance score for each token)
                    if clf_prediction['type'] == REGEX_CLF:
                        clf = clf_prediction['classifier']
                        partition = clf.split(sample)
                        charset = [False] * len(sample)
                        last_part_end = 0
                        for part, match in partition:
                            part_slice = slice(last_part_end,
                                               last_part_end + len(part))
                            charset[part_slice] = [match] * len(part)
                            last_part_end += len(part)
                        highlights = []
                        last_token_end = 0
                        for token in tokens:
                            token_start = sample.find(token, last_token_end)
                            token_slice = slice(token_start,
                                                token_start + len(token))
                            # Highlight a token if at least one of its
                            # characters was matched
                            highlight = any(charset[token_slice])
                            last_token_end = token_start + len(token)
                            highlights.append(highlight)
                        clf_scores.append(
                            np.array(highlights).astype(float)
                        )
                        continue
                    # The classifier's prediction (a.k.a. status here)
                    # is always True inside this branch
                    clf_scores.append(
                        window_weight * _calculate_importance_scores(
                            True, clf_windows_predictions['predictions'],
                            window_size
                        )
                    )

    if scores:
        scores = np.sum(scores, axis=0)
        max_score = np.max(scores)
        # Sometimes max_score can be zero, which means MAX_WINDOW_SIZE
        # turned out to be too small for the specific sample
        if max_score > 0:
            scores /= max_score
        payload['results']['sample'] = zip(tokens, scores)
        if per_clf:
            payload['results_per_classifier'] = []
            for clf_prediction, clf_scores in \
                    itertools.izip(prediction_per_clf, scores_per_clf):
                if clf_prediction['status']:
                    clf_scores = np.sum(clf_scores, axis=0)
                    clf_max_score = np.max(clf_scores)
                    if clf_max_score > 0:
                        clf_scores /= clf_max_score
                    clf_prediction['sample'] = zip(tokens, clf_scores)
                # The actual classifier is redundant and also
                # "is not JSON serializable"
                del clf_prediction['classifier']
                payload['results_per_classifier'].append(clf_prediction)

    message = NotificationManager.notify_client(session_key, payload)
    return message.send()


def prepare_dataset(dataset, mapping, split):
    """
    Prepares the dataset for ML processing by forming some set of samples
    (for training/testing) along with corresponding ground-truth labels.
    """

    # Create a mapping for the dataset (only for the current task's purposes)
    dataset_mapping = DatasetMapping(dataset=dataset)
    dataset_mapping.set_mapping(mapping)

    X, y = dataset_mapping.transform()

    # Delete the temporary dataset's mapping
    dataset_mapping.delete()

    if split:
        # Discard train data and leave only test data
        _, X, _, y = train_test_split(
            X, y, train_size=dataset.train_percentage / 100.,
            stratify=y, random_state=RANDOM_STATE
        )

    return X, y


def prepare_dataset_as_unsupervised(dataset, split):
    """
    Special version of prepare_dataset without using (possibly missing) labels.
    """

    X = dataset.texts

    if split:
        # Discard train data and leave only test data
        _, X, = train_test_split(
            X, train_size=dataset.train_percentage / 100.,
            random_state=RANDOM_STATE
        )

    return X


def preview_dataset(X, y):
    """
    Serializes first DATASET_PREVIEW_SIZE samples from a already prepared
    dataset represented as a (X: texts, y: labels) pair.
    Also adds some simple stats about the whole dataset to the final payload.
    """

    total = len(y)
    positive = sum(y)
    negative = total - positive

    X = X[:DATASET_PREVIEW_SIZE]
    y = y[:DATASET_PREVIEW_SIZE]

    return {
        'results': [{'text': text, 'label': label}
                    for text, label in itertools.izip(X, y)],
        'stats': {
            'positive': positive,
            'negative': negative,
            'total': total
        }
    }


def preview_dataset_as_unsupervised(X):
    """
    Special version of preview_dataset without using (possibly missing) labels.
    """

    total = len(X)

    X = X[:DATASET_PREVIEW_SIZE]

    return {
        'results': [{'text': text} for text in X],
        'stats': {
            'total': total
        }
    }


@shared_task
def evaluate_metrics(session_key, experiment_pk, dataset_pk,
                     mapping, split, task_uuid):
    logger.info("Evaluating metrics of Experiment(pk=%s) on %s Dataset(pk=%s)",
                experiment_pk, ('test split of' if split else 'full'), dataset_pk)

    try:
        experiment = Experiment.objects.get(pk=experiment_pk)
    except Experiment.DoesNotExist:
        logger.error("Could not find Experiment(pk=%s)", experiment_pk)
        return False

    try:
        dataset = Dataset.objects.get(pk=dataset_pk)
    except Dataset.DoesNotExist:
        logger.error("Could not find Dataset(pk=%s)", dataset_pk)
        return False

    try:
        assert mapping is not None, 'No mapping specified.'
        X, y_true = prepare_dataset(dataset, mapping, split)
    except (AssertionError, ValueError) as splitting_error:
        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_EVALUATING_ERROR_NOTIFICATION,
            'error': str(splitting_error)
        }
        message = NotificationManager.notify_client(session_key, payload)
        message.send()
        return False

    y_pred = experiment.predict(X)

    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)

    payload = {
        'task_uuid': task_uuid,
        'notification': NotificationManager.ServerNotifications.EXPERIMENT_EVALUATED_NOTIFICATION,
        'scores': {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    }
    message = NotificationManager.notify_client(session_key, payload)
    return message.send()


@shared_task
def generate_predictions(session_key, experiment_pk, dataset_pk,
                         mapping, split, task_uuid):
    logger.info("Generating predictions of Experiment(pk=%s) on %s Dataset(pk=%s)",
                experiment_pk, ('test split of' if split else 'full'), dataset_pk)

    try:
        experiment = Experiment.objects.get(pk=experiment_pk)
    except Experiment.DoesNotExist:
        logger.error("Could not find Experiment(pk=%s)", experiment_pk)
        return False

    try:
        dataset = Dataset.objects.get(pk=dataset_pk)
    except Dataset.DoesNotExist:
        logger.error("Could not find Dataset(pk=%s)", dataset_pk)
        return False

    try:
        if mapping is None:
            X = prepare_dataset_as_unsupervised(dataset, split)
        else:
            # Discard ground-truth labels
            X, _ = prepare_dataset(dataset, mapping, split)
    except ValueError as splitting_error:
        payload = {
            'task_uuid': task_uuid,
            'notification': NotificationManager.ServerNotifications.EXPERIMENT_GENERATING_ERROR_NOTIFICATION,
            'error': str(splitting_error)
        }
        message = NotificationManager.notify_client(session_key, payload)
        message.send()
        return False

    # Make sure to convert the obtained predictions to `bool`,
    # since `numpy.bool_` "is not JSON serializable"
    predictions = map(bool, experiment.predict(X))

    preview = preview_dataset(X, predictions)

    # Save the predictions (along with some additional data used during the last
    # generation) in the cache in order not to recompute them again
    data = {
        'dataset_pk': dataset.pk,
        'mapping': mapping,
        'split': split,
        'predictions': predictions
    }
    experiment.set_cached_data('generate', data)

    payload = {
        'task_uuid': task_uuid,
        'notification': NotificationManager.ServerNotifications.EXPERIMENT_GENERATED_NOTIFICATION,
        'preview': preview
    }
    message = NotificationManager.notify_client(session_key, payload)
    return message.send()


def _build_classifier_confidence_distribution(clf, X, y):
    scores = clf.decision_function(X)

    positive_samples, positive_scores = [], []
    negative_samples, negative_scores = [], []
    for text, label, score in itertools.izip(X, y, scores):
        if label:
            positive_samples.append(text)
            positive_scores.append(score)
        else:
            negative_samples.append(text)
            negative_scores.append(score)

    histogram_options = {'range': [scores.min(), scores.max()],
                         'bins': HISTOGRAM_BINS}

    positive_counts_per_bin, positive_bin_edges = \
        np.histogram(positive_scores, **histogram_options)

    positive_samples_per_bin = [[] for _ in range(HISTOGRAM_BINS)]
    for text, score in itertools.izip(positive_samples, positive_scores):
        # All but the last bin is half-open, i.e. looks like [a, b)
        index = bisect.bisect_right(positive_bin_edges, score) - 1
        if index == HISTOGRAM_BINS:
            index -= 1
        positive_samples_per_bin[index].append(text)

    negative_counts_per_bin, negative_bin_edges = \
        np.histogram(negative_scores, **histogram_options)

    negative_samples_per_bin = [[] for _ in range(HISTOGRAM_BINS)]
    for text, score in itertools.izip(negative_samples, negative_scores):
        # All but the last bin is half-open, i.e. looks like [a, b)
        index = bisect.bisect_right(negative_bin_edges, score) - 1
        if index == HISTOGRAM_BINS:
            index -= 1
        negative_samples_per_bin[index].append(text)

    histogram = [positive_counts_per_bin, negative_counts_per_bin]
    samples = [positive_samples_per_bin, negative_samples_per_bin]

    # Take into account that `numpy.ndarray` "is not JSON serializable"
    return {
        'histogram': map(np.ndarray.tolist, histogram),
        'samples': samples,
        'range': histogram_options['range']
    }


@shared_task
def train_classifier(session_key, clf_uuid):
    logger.info("Training classifier with uuid=%s", clf_uuid)

    try:
        clf = get_classifer(clf_uuid)
        # Check whether a valid classifier was found
        assert clf is not None
    except:
        logger.error("Could not find classifier with uuid=%s", clf_uuid)
        return False

    clf_type = clf.clf_type
    if clf_type != TRAINED_CLF:
        logger.error("Could not train classifier with uuid=%s: expected "
                     "classifier of type '%s' instead of type '%s'",
                     clf_uuid, TRAINED_CLF, clf_type)
        return False

    payload = {
        'notification': NotificationManager.ServerNotifications.CLASSIFIER_TRAINED_NOTIFICATION,
        'clf_uuid': clf_uuid
    }
    message = NotificationManager.notify_client(session_key, payload)

    if not clf.dirty or clf.training:  # no need to retrain
        return message.send()

    clf.training = True
    clf.save()

    # Compile full train/test data from several datasets

    X_train_full, y_train_full = [], []
    X_test_full, y_test_full = [], []

    for dataset in clf.datasets.all():
        dataset_mapping = DatasetMapping.objects.filter(
            dataset=dataset, clf_uuid=clf_uuid
        ).last()

        if dataset_mapping is None:
            continue

        X, y = dataset_mapping.transform()

        # Split dataset to train/test subsets and handle possible errors
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, train_size=dataset.train_percentage / 100.,
                stratify=y, random_state=RANDOM_STATE
            )
        except ValueError as splitting_error:
            payload['notification'] = NotificationManager.ServerNotifications.CLASSIFIER_TRAINING_ERROR_NOTIFICATION
            # Add problematic dataset to error message
            payload['error'] = '%s: "%s"' % (dataset.name, splitting_error)
            message.set_message(payload)
            message.send()
            return False
        finally:
            clf.training = False
            clf.save()

        X_train_full.extend(X_train)
        y_train_full.extend(y_train)
        X_test_full.extend(X_test)
        y_test_full.extend(y_test)

    X_train_full, y_train_full = shuffle(
        X_train_full, y_train_full, random_state=RANDOM_STATE
    )
    X_test_full, y_test_full = shuffle(
        X_test_full, y_test_full, random_state=RANDOM_STATE
    )

    # Actual learning (along with handling of possible training errors)

    try:
        clf.fit(X_train_full, y_train_full)
    except ValueError as training_error:
        payload['notification'] = NotificationManager.ServerNotifications.CLASSIFIER_TRAINING_ERROR_NOTIFICATION
        payload['error'] = str(training_error)
        message.set_message(payload)
        message.send()
        return False
    finally:
        clf.training = False
        clf.save()

    # Evaluate and store metrics

    if clf.reverse:
        # Test predictions were already flipped, so ground truth test labels
        # must also be flipped, since the reverse flag exchanges the meaning
        # between positive and negative labels
        y_test_full = map(operator.not_, y_test_full)

    test_predictions = clf.predict(X_test_full)

    precision = precision_score(y_test_full, test_predictions)
    recall = recall_score(y_test_full, test_predictions)
    f1 = f1_score(y_test_full, test_predictions)

    clf.scores = {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

    clf.dirty = False
    clf.save()

    payload['scores'] = clf.scores

    # Build the distribution of negative/positive (test) samples
    # over the confidence axis (an interactive histogram
    # will be plotted further based on that data)

    payload['confidence_distribution'] = \
        _build_classifier_confidence_distribution(clf, X_test_full, y_test_full)

    message.set_message(payload)
    return message.send()


@shared_task
def plot_classifier_decision_function(session_key, clf_uuid):
    logger.info("Plotting decision function of classifier with uuid=%s",
                clf_uuid)

    try:
        clf = get_classifer(clf_uuid)
        # Check whether a valid classifier was found
        assert clf is not None
    except:
        logger.error("Could not find classifier with uuid=%s", clf_uuid)
        return False

    clf_type = clf.clf_type
    if clf_type != TRAINED_CLF:
        logger.error("Could not plot decision function of classifier with uuid=%s: "
                     "expected classifier of type '%s' instead of type '%s'",
                     clf_uuid, TRAINED_CLF, clf_type)
        return False

    payload = {
        'notification': NotificationManager.ServerNotifications.CLASSIFIER_DECISION_FUNCTION_PLOTTED_NOTIFICATION,
        'clf_uuid': clf_uuid
    }
    message = NotificationManager.notify_client(session_key, payload)

    if not clf.trained:
        payload['notification'] = NotificationManager.ServerNotifications.CLASSIFIER_DECISION_FUNCTION_PLOTTING_ERROR_NOTIFICATION
        payload['error'] = 'Classifier is not trained yet.'
        message.set_message(payload)
        message.send()
        return False

    # Gather full test data from several datasets

    X_test_full, y_test_full = [], []

    for dataset in clf.datasets.all():
        dataset_mapping = DatasetMapping.objects.filter(
            dataset=dataset, clf_uuid=clf_uuid
        ).last()

        if dataset_mapping is None:
            continue

        X, y = dataset_mapping.transform()

        # Extract test subset from dataset
        _, X_test, _, y_test = train_test_split(
            X, y, train_size=dataset.train_percentage / 100.,
            stratify=y, random_state=RANDOM_STATE
        )

        X_test_full.extend(X_test)
        y_test_full.extend(y_test)

    X_test_full, y_test_full = shuffle(
        X_test_full, y_test_full, random_state=RANDOM_STATE
    )

    if clf.reverse:
        # Ground truth test labels must be flipped, since the reverse flag
        # exchanges the meaning between positive and negative labels
        y_test_full = map(operator.not_, y_test_full)

    # Build the distribution of negative/positive (test) samples
    # over the confidence axis (an interactive histogram
    # will be plotted further based on that data)

    payload['confidence_distribution'] = \
        _build_classifier_confidence_distribution(clf, X_test_full, y_test_full)

    message.set_message(payload)
    return message.send()


# Publish API


@shared_task
def add_sample_to_online_learner(experiment_pk, tag, text, label,
                                 infered_negatives=None):
    if infered_negatives is None:
        infered_negatives = []

    logger.info("Adding sample with label=%s to online component of "
                "Experiment(pk=%s) for tag=%s",
                label, experiment_pk, tag)

    try:
        experiment = Experiment.objects.get(pk=experiment_pk)
    except Experiment.DoesNotExist:
        logger.error("Could not find Experiment(pk=%s)", experiment_pk)
        return False

    learner_facade = experiment.get_or_create_online_learner_facade(tag)
    capsule = Capsule(text)

    # If the current sample is positive, then allow fitting the learner with
    # some additional inferred negative samples for more balanced training
    if label and infered_negatives:
        infered_negative_capsules = [Capsule(infered_negative)
                                     for infered_negative in infered_negatives]
    else:
        infered_negative_capsules = []

    learner_facade.train([capsule], [label], infered_negative_capsules)

    return True


@shared_task
def remove_sample_from_online_learner(experiment_pk, tag, text, label):
    logger.info("Removing sample with label=%s from online component of "
                "Experiment(pk=%s) for tag=%s",
                label, experiment_pk, tag)

    if not label:
        # Only removal of positive samples makes sense
        return False

    try:
        experiment = Experiment.objects.get(pk=experiment_pk)
    except Experiment.DoesNotExist:
        logger.error("Could not find Experiment(pk=%s)", experiment_pk)
        return False

    learner_facade = experiment.get_or_create_online_learner_facade(tag)
    capsule = Capsule(text)
    learner_facade.remove_sample(capsule)

    return True


@shared_task
def update_online_learner_samples(online_learner_pk,
                                  add=None, edit=None, remove=None):
    if add is None:
        add = []
    if edit is None:
        edit = []
    if remove is None:
        remove = []

    logger.info("Updating OnlineLearner(pk=%s)", online_learner_pk)

    try:
        online_learner = OnlineLearner.objects.get(pk=online_learner_pk)
    except OnlineLearner.DoesNotExist:
        logger.error("Could not find OnlineLearner(pk=%s)", online_learner_pk)
        return False

    for entry in add:
        online_learner.add_sample(
            text=entry['text'],
            flags=[],
            label=entry['label'],
        )

    for entry in edit:
        online_learner.edit_sample_by_idx(
            idx=entry['index'],
            text=entry.get('text'),
            label=entry.get('label'),
        )

    for entry in sorted(remove, reverse=True):
        online_learner.discard_sample_by_idx(entry)

    tag_learner = TagLearner(online_learner)
    samples = online_learner.samples
    if samples:
        tag_learner.reset(
            zip(samples['text'], samples['flags'], samples['label'])
        )
        tag_learner.save_online_model()
    else:
        online_learner.reset()

    return True


@shared_task
def reset_online_learner(online_learner_pk):
    logger.info("Resetting OnlineLearner(pk=%s)", online_learner_pk)

    try:
        online_learner = OnlineLearner.objects.get(pk=online_learner_pk)
    except OnlineLearner.DoesNotExist:
        logger.error("Could not find OnlineLearner(pk=%s)", online_learner_pk)
        return False

    online_learner.reset()
    return True


@shared_task
def make_combined_predictions(experiment_pk, tag, samples):
    logger.info("Making combined predictions by Experiment(pk=%s) for tag=%s",
                experiment_pk, tag)

    try:
        experiment = Experiment.objects.get(pk=experiment_pk)
    except Experiment.DoesNotExist:
        logger.error("Could not find Experiment(pk=%s)", experiment_pk)
        return

    predictions = offline_predictions = experiment.predict(samples)

    learner_facade = experiment.get_or_create_online_learner_facade(tag)

    if learner_facade.is_mature:
        capsules = [Capsule(sample) for sample in samples]
        online_predictions = learner_facade.predict(capsules)
        # FIXME: find a way to properly combine offline and online predictions
    else:
        logger.warning('Not combining: online component of Experiment(pk=%s) '
                       'for tag=%s is not mature yet', experiment_pk, tag)

    # `numpy.bool_` "is not JSON serializable"
    return map(bool, predictions)


# OnlineLearner API


@shared_task
def learner_facade_get_or_create(tag, user_pk=None, include_deleted=None,
                                 defaults=None):
    user = None if user_pk is None else User.objects.get(pk=user_pk)
    # Restore default values
    options = {
        'include_deleted': include_deleted or False,
        'defaults': defaults,
    }
    # Optimize things significantly
    options['preload'] = False
    return LearnerFacade.get_or_create(tag, user, **options).db_model.to_dict()


@shared_task
def learner_facade_get_all(user_pk=None, active_only=None, mature_only=None,
                           include_deleted=None):
    user = None if user_pk is None else User.objects.get(pk=user_pk)
    # Restore default values
    options = {
        'active_only': active_only or False,
        'mature_only': mature_only or False,
        'include_deleted': include_deleted or False,
    }
    # Optimize things significantly
    options['preload'] = False
    return map(lambda lf: lf.db_model.to_dict(),
               LearnerFacade.get_all(user, **options))


@shared_task
def learner_facade_train(user_pk, tag, texts, labels, flags=None,
                         infered_negatives=None):
    user = User.objects.get(pk=user_pk)
    learner_facade = LearnerFacade.get_or_create(tag, user=user)
    if flags is None:
        flags = [None] * len(texts)
    capsules = [Capsule(text=t, flags=fs)
                for t, fs in itertools.izip(texts, flags)]
    if isinstance(infered_negatives, dict):
        texts = infered_negatives['texts']
        flags = infered_negatives['flags']
        infered_negative_capsules = [Capsule(text=t, flags=fs)
                                     for t, fs in itertools.izip(texts, flags)]
    elif isinstance(infered_negatives, list):  # only texts, no flags
        texts = infered_negatives
        infered_negative_capsules = [Capsule(text=t) for t in texts]
    else:
        infered_negative_capsules = []
    learner_facade.train(capsules, labels, infered_negative_capsules)


@shared_task
def learner_facade_predict(user_pk, tag, texts, flags=None,
                           include_attributes=None):
    user = User.objects.get(pk=user_pk)
    learner_facade = LearnerFacade.get_or_create(tag, user=user)
    if flags is None:
        flags = [None] * len(texts)
    capsules = [Capsule(text=t, flags=fs)
                for t, fs in itertools.izip(texts, flags)]
    if include_attributes is None:
        include_attributes = False
    predictions = learner_facade.predict(capsules, include_attributes)
    if not include_attributes:
        # `numpy.bool_` "is not JSON serializable"
        predictions = map(bool, predictions)
    return predictions


@shared_task
def learner_facade_remove_sample(user_pk, tag, text):
    user = User.objects.get(pk=user_pk)
    learner_facade = LearnerFacade.get_or_create(tag, user=user)
    capsule = Capsule(text)
    learner_facade.remove_sample(capsule)


@shared_task
def online_learner_update_flags(user_pk, tag, flags=None):
    user = User.objects.get(pk=user_pk)
    online_learner = OnlineLearner.objects.get(tag=tag, owner=user)
    if flags is None:
        flags = {}
    # Update only the `active` and `deleted` flags, skip anything else
    if 'active' in flags:
        online_learner.active = flags['active']
    if 'deleted' in flags:
        online_learner.deleted = flags['deleted']
    online_learner.save()


@shared_task
def online_learner_reset(user_pk, tag):
    user = User.objects.get(pk=user_pk)
    online_learner = OnlineLearner.objects.get(tag=tag, owner=user)
    online_learner.reset()
    online_learner.save()


@shared_task
def online_learner_get_samples(user_pk, tag):
    user = User.objects.get(pk=user_pk)
    online_learner = OnlineLearner.objects.get(tag=tag, owner=user)
    return online_learner.samples or {}
