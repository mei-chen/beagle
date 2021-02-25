from __future__ import absolute_import, unicode_literals

import collections
import itertools
import random
import time

# App
from dataset.models import Assignment, LabelingTask, Dataset
from experiment.models import Formula, Experiment
from ml.vecs import TagLearnerOfflineVectorizer
from realtime.notify import NotificationManager

# Celery
from celery import shared_task
from celery.utils.log import get_task_logger

# NumPy
import numpy as np

# SciKit-Learn
from sklearn.linear_model import PassiveAggressiveClassifier

logger = get_task_logger(__name__)


RANDOM_STATE = 42


class LabelSuggester(object):

    def __init__(self, assignment):
        self._assignment = assignment
        self._ready = False

    @staticmethod
    def _initialize_vectorizer():
        # No uuid, no tag, and default number of sparse features
        return TagLearnerOfflineVectorizer(None, None)

    @staticmethod
    def _initialize_model():
        return PassiveAggressiveClassifier(C=1e5, random_state=RANDOM_STATE)

    def _transform(self, X):
        # No tag, no per-sample flags
        return self._vectorizer.transform(None, X, [[] for _ in range(len(X))])

    def _initialize(self):
        if self._ready:
            return

        self._vectorizer = self._initialize_vectorizer()
        self._model = self._initialize_model()

        X, y = self._assignment.transform()

        self._vectorizer.fit(X)  # no global flags
        self._model.fit(self._transform(X), y)

        self._ready = True

    def __call__(self, text):
        self._initialize()  # lazy initialization
        return bool(self._model.predict(self._transform([text]))[0])


@shared_task
def select_samples(session_key, assignment_pk, task_uuid):
    logger.info("Selecting samples for Assignment(pk=%s)", assignment_pk)

    try:
        assignment = Assignment.objects.select_related(
            'labeling_task__dataset'
        ).get(pk=assignment_pk)
    except Assignment.DoesNotExist:
        logger.error("Could not find Assignment(pk=%s)", assignment_pk)
        return False

    random.seed(RANDOM_STATE)

    texts = assignment.dataset.texts

    stats = assignment.progress

    stage = stats['stage']

    if stage == 1:
        max_samples_count = 20
        evaluation_set_indices = frozenset(assignment.labeling_task.indices)
        max_samples_count -= len(evaluation_set_indices)
        left_indices = [index for index in range(len(texts))
                        if index not in evaluation_set_indices]
        indices = random.sample(
            left_indices, min(len(left_indices), max_samples_count)
        )
        indices += evaluation_set_indices
        random.shuffle(indices)
        samples = []
        for index in indices:
            text = texts[index]
            sample = {'index': index, 'text': text}  # no label suggestion
            samples.append(sample)

    else:
        max_samples_count = 10
        labeled_indices = frozenset(assignment.indices)
        left_indices = [index for index in range(len(texts))
                        if index not in labeled_indices]
        indices = random.sample(
            left_indices, min(len(left_indices), max_samples_count)
        )
        label_suggester = LabelSuggester(assignment)
        samples = []
        for index in indices:
            text = texts[index]
            suggested_label = label_suggester(text)
            sample = {'index': index, 'text': text,
                      'suggested_label': suggested_label}
            samples.append(sample)

    payload = {
        'task_uuid': task_uuid,
        'notification': NotificationManager.ServerNotifications.LABELING_TASK_SAMPLES_SELECTED_NOTIFICATION,
        'stage': stage,
        'samples': samples,
        'stats': stats
    }

    message = NotificationManager.notify_client(session_key, payload)
    return message.send()


@shared_task
def store_samples(session_key, assignment_pk, samples, task_uuid):
    logger.info("Storing samples for Assignment(pk=%s)", assignment_pk)

    try:
        assignment = Assignment.objects.select_related(
            'labeling_task'
        ).get(pk=assignment_pk)
    except Assignment.DoesNotExist:
        logger.error("Could not find Assignment(pk=%s)", assignment_pk)
        return False

    assignment.add_stage(samples)

    payload = {
        'task_uuid': task_uuid,
        'notification': NotificationManager.ServerNotifications.LABELING_TASK_SAMPLES_STORED_NOTIFICATION
    }

    message = NotificationManager.notify_client(session_key, payload)
    return message.send()


@shared_task
def export_supervised_dataset(session_key, labeling_task_pk, name, description,
                              task_uuid):
    logger.info("Exporting supervised dataset based on LabelingTask(pk=%s)",
                labeling_task_pk)

    try:
        labeling_task = LabelingTask.objects.select_related(
            'dataset', 'owner'
        ).get(pk=labeling_task_pk)
    except LabelingTask.DoesNotExist:
        logger.error("Could not find LabelingTask(pk=%s)", labeling_task_pk)
        return False

    texts = labeling_task.dataset.texts
    labels = [None] * len(texts)

    labels_votings = collections.defaultdict(lambda: {False: 0, True: 0})

    assignments = labeling_task.assignments.select_related('assignee').all()

    for assignment in assignments:
        if assignment.assignee == labeling_task.owner:  # veto
            for index, label in itertools.izip(assignment.indices,
                                               assignment.labels):
                if label is not None:  # i.e. not skipped
                    labels[index] = label

        else:  # voting
            for index, label in itertools.izip(assignment.indices,
                                               assignment.labels):
                if label is not None:  # i.e. not skipped
                    labels_votings[index][label] += 1

    for index, label in enumerate(labels):
        if label is not None:  # veto
            continue

        if index in labels_votings:  # voting
            voting_result = labels_votings[index]
            if voting_result[False] > voting_result[True]:
                labels[index] = False
            elif voting_result[False] < voting_result[True]:
                labels[index] = True
            else:  # draw (i.e. no decision can be made)
                pass

    final_texts, final_labels = zip(*[
        (text, int(label))  # convert boolean labels to integer indices
        for text, label in itertools.izip(texts, labels) if label is not None
    ])

    dataset = Dataset.objects.create(
        name=name,
        description=description,
        owner=labeling_task.owner,
        supervised=True,
        klasses=['False', 'True'],  # must be a list of strings!
        samples={
            'texts': final_texts,
            'labels': final_labels
        }
    )

    logger.info("Exported supervised dataset Dataset(pk=%s): %s",
                dataset.pk, dataset)

    payload = {
        'task_uuid': task_uuid,
        'notification': NotificationManager.ServerNotifications.LABELING_TASK_SUPERVISED_DATASET_EXPORTED_NOTIFICATION,
        'dataset': dataset.to_dict()
    }

    message = NotificationManager.notify_client(session_key, payload)
    return message.send()


def generate_random_sample(dataset, size=None, excluded=None):
    if size is None:
        size = 10
    if excluded is None:
        excluded = []

    random.seed(RANDOM_STATE)

    texts = dataset.texts

    excluded_indices = frozenset(excluded)
    left_indices = [index for index in range(len(texts))
                    if index not in excluded_indices]
    indices = random.sample(
        left_indices, min(len(left_indices), size)
    )

    samples = [{'index': index, 'text': texts[index]} for index in indices]
    return samples


@shared_task
def expand_evaluation_score(session_key, assignment_pk, task_uuid):
    logger.info("Expanding evaluation score for Assignment(pk=%s)",
                assignment_pk)

    try:
        assignment = Assignment.objects.select_related(
            'labeling_task__dataset'
        ).get(pk=assignment_pk)
    except Assignment.DoesNotExist:
        logger.error("Could not find Assignment(pk=%s)", assignment_pk)
        return False

    evaluation_set = assignment.labeling_task.evaluation_set
    stages = assignment.stages

    if evaluation_set is not None and stages is not None:
        texts = assignment.labeling_task.texts
        labels = [stages[0]['labels'][stages[0]['indices'].index(index)]
                  for index in evaluation_set['indices']]
        golds = evaluation_set['labels']

        samples = [
            {'text': text, 'label': label, 'gold': gold}
            for text, label, gold in itertools.izip(texts, labels, golds)
        ]

    else:
        samples = []

    payload = {
        'task_uuid': task_uuid,
        'notification': NotificationManager.ServerNotifications.LABELING_TASK_EVALUATION_SCORE_EXPANDED_NOTIFICATION,
        'samples': samples
    }

    message = NotificationManager.notify_client(session_key, payload)
    return message.send()


def build_index_label_map(assignment):
    return {
        index: label
        for index, label in itertools.izip(assignment.indices,
                                           assignment.labels)
        if label is not None  # discard skipped samples
    }


@shared_task
def compute_accord_matrix(session_key, labeling_task_pk, task_uuid):
    logger.info("Computing accord matrix for LabelingTask(pk=%s)",
                labeling_task_pk)

    try:
        labeling_task = LabelingTask.objects.select_related(
            'dataset'
        ).only(
            'dataset__samples_count'
        ).get(pk=labeling_task_pk)
    except LabelingTask.DoesNotExist:
        logger.error("Could not find LabelingTask(pk=%s)", labeling_task_pk)
        return False

    total = labeling_task.dataset.samples_count

    assignments = list(labeling_task.assignments.order_by('-created'))

    n = len(assignments)
    matrix = [[None for _ in range(n)] for _ in range(n)]

    for i in range(len(assignments)):
        for j in range(i + 1, len(assignments)):
            entry = [0.0, 0.0]

            index_label_map_i = build_index_label_map(assignments[i])
            index_label_map_j = build_index_label_map(assignments[j])

            intersection = np.intersect1d(index_label_map_i.keys(),
                                          index_label_map_j.keys(),
                                          assume_unique=True)

            if intersection.size > 0:
                overlap = float(intersection.size) / total

                matches = sum(
                    index_label_map_i[index] == index_label_map_j[index]
                    for index in intersection
                )

                agreement = float(matches) / intersection.size

                entry = [overlap, agreement]

            matrix[i][j] = matrix[j][i] = entry

    payload = {
        'task_uuid': task_uuid,
        'notification': NotificationManager.ServerNotifications.LABELING_TASK_ACCORD_MATRIX_COMPUTED_NOTIFICATION,
        'matrix': matrix
    }

    message = NotificationManager.notify_client(session_key, payload)
    return message.send()


@shared_task
def build_experiment(session_key, assignment_pk, task_uuid):
    logger.info("Building experiment based on Assignment(pk=%s)", assignment_pk)

    try:
        assignment = Assignment.objects.select_related(
            'labeling_task__dataset', 'assignee'
        ).get(pk=assignment_pk)
    except Assignment.DoesNotExist:
        logger.error("Could not find Assignment(pk=%s)", assignment_pk)
        return False

    texts, labels = zip(*[
        (text, int(label))  # convert boolean labels to integer indices
        for text, label in itertools.izip(assignment.texts, assignment.labels)
        if label is not None  # discard skipped samples
    ])

    name = '[Labeling-Stage%d-%.3f] %s' % (assignment.stages_count,
                                           time.time(),  # the current timestamp
                                           assignment.dataset.name)

    dataset = Dataset.objects.create(
        name=name,
        description=assignment.dataset.description,
        owner=assignment.assignee,
        supervised=True,
        klasses=['False', 'True'],  # must be a list of strings!
        samples={
            'texts': texts,
            'labels': labels
        }
    )

    formula = Formula.objects.create()
    formula.create_classifiers([  # a single default TrainedClassifier
        {
            'weight': 1,
            'classifier': {
                'type': 'trained',
                'name': 'Trained Classifier',
                'apply': 'include',
                'model': 'logreg',
                'datasets': [  # the only dataset
                    {
                        'id': dataset.id,
                        'mapping': {
                            'neg': ['False'],
                            'pos': ['True']
                        }
                    }
                ]
            }
        }
    ])

    experiment = Experiment.objects.create(
        name=name,
        formula=formula,
        owner=assignment.assignee
    )

    payload = {
        'task_uuid': task_uuid,
        'notification': NotificationManager.ServerNotifications.LABELING_TASK_EXPERIMENT_BUILT_NOTIFICATION,
        'dataset': dataset.to_dict(),
        'experiment': experiment.to_dict()
    }

    message = NotificationManager.notify_client(session_key, payload)
    return message.send()
