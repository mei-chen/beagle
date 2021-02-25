from __future__ import unicode_literals

import collections
import itertools
import jsonfield
import operator
import uuid

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.dispatch import receiver
from model_utils.models import TimeStampedModel


class Dataset(TimeStampedModel):
    name = models.CharField('Name', max_length=300)
    uuid = models.UUIDField('UUID', default=uuid.uuid4)
    description = models.TextField('Description', blank=True)

    klasses = jsonfield.JSONField(
        'Classes', null=True, blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )
    # A dict containing at least a 'texts' field
    samples = jsonfield.JSONField('Samples', null=True, blank=True)
    # If supervised, the samples dict also contains a 'labels' field
    supervised = models.BooleanField('Supervised', default=True)

    # Defines a train/test splitting schema for the dataset
    train_percentage = models.IntegerField(
        default=80, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='datasets',
                              null=True, blank=True, default=None)

    # The cached number of samples (otherwise in order to calculate the
    # size of the dataset one have to fetch all the samples);
    # the field gets updated automatically each time the dataset is saved
    samples_count = models.IntegerField('Samples count', null=True, blank=True)

    @property
    def current_samples_count(self):
        return len((self.samples or {}).get('texts', []))

    @property
    def test_percentage(self):
        return 100 - self.train_percentage

    @property
    def collaborators(self):
        qs = self.collaboration_invites.select_related('invitee')
        return [collaboration_invite.invitee for collaboration_invite in qs]

    def has_access(self, user):
        return user == self.owner or user in self.collaborators

    @property
    def pending_invites(self):
        qs = self.external_invites.values_list('email', flat=True)
        return list(qs)

    def __unicode__(self):
        return u'[%s] %s' % (self.owner or '-', self.name)

    def klass_to_index(self, klass):
        return self.klasses.index(klass)

    def index_to_klass(self, index):
        return self.klasses[index]

    @property
    def texts(self):
        return self.samples['texts'] if self.samples else []

    @property
    def index_labels(self):
        if not self.supervised:
            return
        return self.samples['labels'] if self.samples else []

    @property
    def klass_labels(self):
        if not self.supervised:
            return
        return [self.index_to_klass(label) for label in self.index_labels]

    def get_sample(self, sample_index):
        return Sample(
            text=self.texts[sample_index],
            label=(self.index_to_klass(self.index_labels[sample_index])
                   if self.supervised else None),
            dataset=self.pk,
            index=sample_index
        )

    def add_sample(self, text=None, label=None):
        if self.samples is None:
            self.samples = {'texts': []}
            if self.supervised:
                self.samples['labels'] = []
        # Allow storing temporary placeholder values
        self.samples['texts'].append(text)
        if self.supervised:
            label = None if label is None else self.klass_to_index(label)
            self.samples['labels'].append(label)
        self.save()

    def set_sample(self, sample_index, text=None, label=None):
        if text is not None:
            self.samples['texts'][sample_index] = text
        if self.supervised:
            if label is not None:
                label = self.klass_to_index(label)
                self.samples['labels'][sample_index] = label
        self.save()

    def pop_sample(self, sample_index):
        text = self.samples['texts'].pop(sample_index)
        label = (self.index_to_klass(self.samples['labels'].pop(sample_index))
                 if self.supervised else None)
        self.save()
        return Sample(
            text=text,
            label=label,
            dataset=self.pk,
            index=sample_index
        )

    def to_dict(self):
        dataset_dict = {
            'id': self.id,
            'name': self.name
        }
        if self.owner:
            owner_dict = {
                'id': self.owner.id,
                'username': self.owner.username,
                'email': self.owner.email
            }
            dataset_dict['owner'] = owner_dict
        return dataset_dict


@receiver(models.signals.pre_save, sender=Dataset)
def update_samples_count(sender, instance, **kwargs):
    if hasattr(instance, 'samples'):  # i.e. not deferred
        instance.samples_count = instance.current_samples_count


class Sample(object):

    def __init__(self, text=None, label=None, dataset=None, index=None):
        self.text = text
        self.label = label
        self.dataset = dataset
        self.index = index

    @property
    def body(self):  # alias
        return self.text

    def to_dict(self):
        return vars(self)


class DatasetMapping(TimeStampedModel):
    dataset = models.ForeignKey(Dataset, related_name='mappings')
    mapping = jsonfield.JSONField(
        'Mapping', null=True, blank=True,
        load_kwargs={'object_pairs_hook': collections.OrderedDict}
    )
    # Optional UUID of a classifier
    clf_uuid = models.UUIDField('Clf UUID', null=True, blank=True)

    def set_mapping(self, mapping=None):
        """
        Sets self.mapping.
        If mapping is not None, then it is expected to be
        a dict of the following format:
        {
            'neg': [list of labels, which should be mapped to False],
            'pos': [list of labels, which should be mapped to True]
        },
        where mapping['neg'] and mapping['pos'] are supposed to be disjunctive
        subsets of self.dataset.klasses.
        """
        if mapping is None:
            self.mapping = None
        else:
            self.mapping = {
                label: False for label in mapping['neg']
            }
            self.mapping.update({
                label: True for label in mapping['pos']
            })
        self.save()

    def get_mapping(self):
        """
        Gets a raw mapping in the same format as expected for set_mapping.
        """
        if self.mapping is None:
            return None
        else:
            mapping = {'neg': [], 'pos': []}
            for label in self.mapping:
                label_type = 'pos' if self.mapping[label] else 'neg'
                mapping[label_type].append(label)
            for label_type in mapping:
                mapping[label_type].sort()
            return mapping

    def map(self, label):
        """
        Maps a label to either True/False or None.
        The latter means that the label cannot be mapped.
        """
        return (self.mapping or {}).get(label)

    def transform(self):
        """
        Transforms the dataset by mapping the labels to True/False and
        filtering out the texts whose labels were mapped to None.
        Returns a pair consisting of the filtered texts and the mapped labels.
        """
        filtered_texts = []
        mapped_labels = []
        for text, klass_label in \
                itertools.izip(self.dataset.texts, self.dataset.klass_labels):
            label = self.map(klass_label)
            if label is not None:
                filtered_texts.append(text)
                mapped_labels.append(label)
        return filtered_texts, mapped_labels


class LabelingTask(TimeStampedModel):
    dataset = models.ForeignKey(Dataset, related_name='labeling_tasks')
    owner = models.ForeignKey(User, related_name='labeling_tasks')

    name = models.CharField('Name', max_length=300)
    description = models.TextField('Description', blank=True)

    evaluation_set = jsonfield.JSONField('Evaluation set',
                                         null=True, blank=True)

    @property
    def indices(self):
        return self.evaluation_set['indices'] if self.evaluation_set else []

    @property
    def texts(self):
        return list(
            operator.itemgetter(*self.indices)(self.dataset.texts)
        ) if self.evaluation_set else []

    @property
    def labels(self):
        return self.evaluation_set['labels'] if self.evaluation_set else []

    def initialize_evaluation_set(self, samples):
        evaluation_set = {'indices': [], 'labels': []}
        for sample in samples:
            evaluation_set['indices'].append(sample['index'])
            evaluation_set['labels'].append(sample['label'])
        self.evaluation_set = evaluation_set
        self.save()

    def __unicode__(self):
        return u'%s -> [%s] %s' % (self.dataset, self.owner, self.name)


class Assignment(TimeStampedModel):
    labeling_task = models.ForeignKey(LabelingTask, related_name='assignments')
    assignee = models.ForeignKey(User, related_name='assignments')

    stages = jsonfield.JSONField('Stages', null=True, blank=True)

    # The cached numbers of stages and labeled samples (otherwise in order to
    # calculate these values one have to fetch all the stages);
    # the fields get updated automatically each time the assignment is saved
    stages_count = models.IntegerField('Stages count', null=True, blank=True)
    labeled_samples_count = models.IntegerField('Labeled samples count',
                                                null=True, blank=True)
    # Ditto
    skipped_samples_count = models.IntegerField('Skipped samples count',
                                                null=True, blank=True)

    # The cached score computed on the labeling task's evaluation set
    # (used by the labeling task's owner to check the assignee)
    score = models.FloatField('Score', null=True, blank=True)

    @property
    def dataset(self):
        """ Allows direct access to the dataset of the labeling task. """
        return self.labeling_task.dataset

    @property
    def owner(self):
        """ Allows direct access to the owner of the labeling task. """
        return self.labeling_task.owner

    @property
    def current_stages_count(self):
        return len(self.stages or [])

    @property
    def current_labeled_samples_count(self):
        # Skipped samples are also considered as labeled (i.e. processed)
        return sum(len(stage['labels']) for stage in (self.stages or []))

    @property
    def current_skipped_samples_count(self):
        return sum(stage['labels'].count(None) for stage in (self.stages or []))

    @property
    def total_samples_count(self):
        return self.dataset.samples_count

    @property
    def left_samples_count(self):
        return self.total_samples_count - self.labeled_samples_count

    @property
    def is_done(self):
        return self.left_samples_count <= 0

    @property
    def progress(self):
        return {
            'stage': self.stages_count + 1,  # current stage number
            'labeled': self.labeled_samples_count,
            'skipped': self.skipped_samples_count,
            'total': self.total_samples_count
        }

    @property
    def indices(self):
        return list(
            itertools.chain(*(stage['indices'] for stage in self.stages))
        ) if self.stages else []

    @property
    def texts(self):
        return list(
            operator.itemgetter(*self.indices)(self.dataset.texts)
        ) if self.stages else []

    @property
    def labels(self):
        return list(
            itertools.chain(*(stage['labels'] for stage in self.stages))
        ) if self.stages else []

    def transform(self):
        """ Filters out skipped samples. """
        texts = []
        labels = []
        for text, label in itertools.izip(self.texts, self.labels):
            if label is not None:
                texts.append(text)
                labels.append(label)
        return texts, labels

    def _compute_evaluation_score(self):
        from sklearn.metrics import accuracy_score

        if self.labeling_task.evaluation_set is None:
            return None

        owner_index_label_map = dict(
            itertools.izip(self.labeling_task.evaluation_set['indices'],
                           self.labeling_task.evaluation_set['labels'])
        )

        if self.stages is None:
            return None

        assignee_index_label_map = dict(
            itertools.izip(self.stages[0]['indices'],
                           self.stages[0]['labels'])
        )

        owner_labels = []
        assignee_labels = []

        for index in owner_index_label_map:
            owner_label = owner_index_label_map[index]
            # The initial stage always includes the whole evaluation set
            assignee_label = assignee_index_label_map[index]
            # Skipped labels should be treated as errors
            if assignee_label is None:
                assignee_label = not owner_label
            owner_labels.append(owner_label)
            assignee_labels.append(assignee_label)

        return accuracy_score(owner_labels, assignee_labels)

    def add_stage(self, samples):
        # Make sure to add each sample only once
        labeled_indices = frozenset(self.indices)
        samples = [sample for sample in samples
                   if sample['index'] not in labeled_indices]
        if not samples:
            return
        check = False
        if not self.stages:
            self.stages = []
            check = True
        stage = {'indices': [], 'labels': []}
        for sample in samples:
            stage['indices'].append(sample['index'])
            # Boolean or None (if skipped)
            stage['labels'].append(sample.get('label'))
        self.stages.append(stage)
        if check:
            self.score = self._compute_evaluation_score()
        self.save()

    def __unicode__(self):
        return u'%s -> %s' % (self.labeling_task, self.assignee)


@receiver(models.signals.pre_save, sender=Assignment)
def update_stages_and_labeled_samples_count(sender, instance, **kwargs):
    if hasattr(instance, 'stages'):  # i.e. not deferred
        instance.stages_count = instance.current_stages_count
        instance.labeled_samples_count = instance.current_labeled_samples_count
        instance.skipped_samples_count = instance.current_skipped_samples_count
