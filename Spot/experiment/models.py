from __future__ import unicode_literals

import operator
import re
import uuid
from collections import OrderedDict

import jsonfield
from django.contrib.auth.models import User
from django.core.cache import cache
from django.dispatch import receiver
from django.db import models
from model_utils.models import TimeStampedModel
import numpy as np

from dataset.models import Dataset, DatasetMapping


class Formula(TimeStampedModel):
    """
    Defines the equation on which more classifiers can be assembled to decide
    together. Other put, it defines the voting schema.
    """
    uuid = models.UUIDField('UUID', default=uuid.uuid4, db_index=True)

    """
    A list of dicts specifying the type of a decision maker and its weight:
      [
        # UUID of a classifier that inherits GenericClassifier
        {'weight': 0.6, 'uuid': '8b8611c4-5f44-4d9b-aa3a-b73c7c195ca2'},
        ...
      ]
    """
    content = jsonfield.JSONField(
        'Formula content', null=True, blank=True,
        load_kwargs={'object_pairs_hook': OrderedDict}
    )

    def _get_classifier(self, clf_uuid):
        """
        Gets and caches the specific classifier
        (at least during the formula's lifetime).
        """
        attr = '_classifier_%s' % clf_uuid
        if not hasattr(self, attr):
            setattr(self, attr, get_classifer(clf_uuid))
        return getattr(self, attr)

    def _clear_classifier(self, clf_uuid):
        """
        Deletes the specific classifier from the db and the formula's cache.
        """
        attr = '_classifier_%s' % clf_uuid
        if hasattr(self, attr):
            clf = getattr(self, attr)
            delattr(self, attr)
        else:
            clf = get_classifer(clf_uuid)
        if clf:
            clf.delete()

    def _create_classifier(self, clf_data):
        """
        Creates and caches a specified classifier
        (at least during the formula's lifetime).
        """
        clf = create_classifier(clf_data)
        attr = '_classifier_%s' % clf.uuid
        setattr(self, attr, clf)
        return clf

    def get_classifiers(self):
        if self.content is None:
            return []
        return [
            {
                'weight': clf_data['weight'],
                'classifier': self._get_classifier(clf_data['uuid'])
            }
            for clf_data in self.content
        ]

    def clear_classifiers(self):
        if self.content is None:
            return
        for clf_data in self.content:
            self._clear_classifier(clf_data['uuid'])
        self.content = None
        self.save()

    def create_classifiers(self, clfs_data):
        # Clean up the old classifiers only after successfully
        # creating the new ones
        content = [
            {
                'weight': clf_data['weight'],
                'uuid': self._create_classifier(clf_data['classifier']).uuid
            }
            for clf_data in clfs_data
        ]
        self.clear_classifiers()
        self.content = content
        self.save()

    def update_classifiers(self, clfs_data):
        content = []
        clf_by_uuid = {str(clf_data['classifier'].uuid): clf_data['classifier']
                       for clf_data in self.get_classifiers()}
        for clf_data in clfs_data:
            weight = clf_data.pop('weight')
            clf_uuid = clf_data.pop('uuid', None)
            clf_data = clf_data['classifier']
            # Create a new classifier
            if clf_uuid is None:
                clf = self._create_classifier(clf_data)
            # Update an existing classifier
            else:
                if clf_uuid in clf_by_uuid:
                    clf = clf_by_uuid.pop(clf_uuid)
                else:
                    clf = self._get_classifer(clf_uuid)
                if 'type' in clf_data:
                    assert clf_data.pop('type') == clf.clf_type
                clf.config(**clf_data)
            content.append({'weight': weight, 'uuid': clf.uuid})
        # Clean up the old classifiers which weren't used during the update
        # (i.e. they are not needed anymore)
        for clf_uuid in clf_by_uuid:
            self._clear_classifier(clf_uuid)
        self.content = content
        self.save()

    @property
    def content_extended(self):
        if self.content is None:
            return None
        content = self.get_classifiers()
        for clf_data in content:
            clf_dict = clf_data['classifier'].to_dict()
            clf_uuid = clf_dict.pop('uuid')
            clf_data['uuid'] = clf_uuid
            clf_data['classifier'] = clf_dict
        return content

    def predict(self, X, with_confidence=False, per_classifier=False):
        """
        Aggregates predictions from the classifiers with the corresponding
        weights. Converts the boolean predictions to {-1, +1} before applying
        the actual aggregation. A sample is considered as being positive, if
        its final weighted prediction is > 0, otherwise it is considered as
        being negative.
        Returns an array of boolean predictions. If with_confidence is True,
        then also returns an additional array of confidence values for each
        prediction (each value is a measure of how much the classifier's
        ensemble is confident that the corresponding prediction is actually
        True or False). If per_classifer is True, then also return an
        additional array of dicts containing 'name', 'type', 'uuid', 'weight'
        and 'predictions' for each classifier.
        """
        predictions = []
        weights = []
        if per_classifier:
            boolean_predictions_per_clf = []
        for clf_data in self.get_classifiers():
            weight = clf_data['weight']
            clf = clf_data['classifier']
            try:
                clf_predictions = clf.predict(X)
            except NotImplementedError:
                pass
            else:
                # False (0) -> -1, True (1) -> +1
                predictions.append(2 * clf_predictions - 1)
                weights.append(weight)
                if per_classifier:
                    boolean_predictions_per_clf.append({
                        'classifier': clf,
                        'weight': weight,
                        'predictions': clf_predictions
                    })
        weighting_options = {'axis': 0}
        if np.sum(weights) > 0:
            weighting_options['weights'] = weights
        # Use default (i.e. uniform) weights when all voting weights are zeros
        weighted_predictions = np.average(
            np.vstack(predictions), **weighting_options
        )
        boolean_predictions = weighted_predictions > 0
        output = [boolean_predictions]
        if with_confidence:
            confidence_values = np.abs(weighted_predictions)
            output.append(confidence_values)
        if per_classifier:
            output.append(boolean_predictions_per_clf)
        if len(output) > 1:
            return tuple(output)
        # The most common use case
        return boolean_predictions

    def __str__(self):
        return str(self.uuid)


@receiver(models.signals.pre_delete, sender=Formula)
def delete_classifiers(sender, instance, **kwargs):
    # Clean up the classifiers before deleting the formula
    instance.clear_classifiers()


DEFAULT_EXPERIMENT_NAME = 'Default Experiment'
DEFAULT_EXPERIMENT_NAME_PATTERN = r'^%s(?: (\d+))?$' % DEFAULT_EXPERIMENT_NAME
default_experiment_name_re = re.compile(DEFAULT_EXPERIMENT_NAME_PATTERN)


def generate_default_experiment_name(user=None, manager=None):
    if manager is None:
        manager = Experiment.objects

    numbers = []
    default_name_used = False

    qs = manager.filter(name__regex=DEFAULT_EXPERIMENT_NAME_PATTERN)
    if user:
        qs = qs.filter(owner=user)
    for experiment in qs:
        number = default_experiment_name_re.match(experiment.name).group(1)
        if number is None:
            default_name_used = True
            # Take into account that 'Default Experiment 1'
            # could also be matched by the regexp, so add 1 only once
            if 1 not in numbers:
                numbers.append(1)
        else:
            number = int(number)
            # Take into account that 'Default Experiment 0'
            # could also be matched the regexp, so discard that 0
            if number > 0:
                if number != 1 or 1 not in numbers:
                    numbers.append(number)

    if not default_name_used:
        return DEFAULT_EXPERIMENT_NAME

    numbers.sort()

    generated_name = DEFAULT_EXPERIMENT_NAME
    # Use the same logic as an OS does when it creates new empty text files
    for index, number in enumerate(numbers, start=1):
        if index != number:
            break
    else:
        index += 1
    if index != 1:
        generated_name += ' %d' % index
    return generated_name


class PublicManager(models.Manager):

    def get_queryset(self):
        return super(PublicManager, self).get_queryset().filter(public=True)


class PrivateManager(models.Manager):

    def get_queryset(self):
        return super(PrivateManager, self).get_queryset().filter(public=False)


class ExperimentBase(TimeStampedModel):

    objects = models.Manager()

    public = PublicManager()
    private = PrivateManager()

    class Meta:
        abstract = True


class Experiment(ExperimentBase):
    """
    Definition of an automatic labeling system that's based on a
    experiment.models.Formula and can be applied over dataset.models.Dataset.
    """
    name = models.CharField('Name', max_length=300, db_index=True,
                            default=None)
    uuid = models.UUIDField('UUID', default=uuid.uuid4, db_index=True)

    formula = models.OneToOneField(Formula, on_delete=models.CASCADE,
                                   null=True, blank=True, default=None)

    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='experiments',
                              null=True, blank=True, default=None)

    # Defines whether the experiment can be shared (i.e. public),
    # otherwise it is considered internal (i.e. private)
    public = models.BooleanField(default=True)

    # namespace -> cache_key_template
    EXPERIMENT_CACHED_DATA_KEY_TEMPLATES = {
        'evaluate': 'experiment_%d_evaluate_data',
        'generate': 'experiment_%d_generate_data',
    }

    def _build_cache_key(self, namespace):
        cache_key_template = \
            self.EXPERIMENT_CACHED_DATA_KEY_TEMPLATES[namespace]
        return cache_key_template % self.id

    def get_cached_data(self, namespace):
        cache_key = self._build_cache_key(namespace)
        return cache.get(cache_key)

    def set_cached_data(self, namespace, data):
        cache_key = self._build_cache_key(namespace)
        # This type of data should be persistent and should never expire
        # (unless the experiment is explicitly deleted)
        cache.set(cache_key, data, timeout=None)

    def delete_cached_data(self, namespace):
        cache_key = self._build_cache_key(namespace)
        cache.delete(cache_key)

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

    def save(self, *args, **kwargs):
        if self.name is None:
            manager = Experiment.public if self.public else Experiment.private
            self.name = generate_default_experiment_name(self.owner, manager)
        super(Experiment, self).save(*args, **kwargs)

    def __str__(self):
        return u'[%s] %s' % (self.owner or '-', self.name)

    def to_dict(self):
        experiment_dict = {
            'id': self.id,
            'uuid': str(self.uuid),
            'name': self.name
        }
        if self.owner:
            owner_dict = {
                'id': self.owner.id,
                'username': self.owner.username,
                'email': self.owner.email
            }
            experiment_dict['owner'] = owner_dict
        return experiment_dict

    # ML-related stuff

    # NOTE: along with the (offline) experiment itself, one may also have
    # supplementary online components (a.k.a. learners).

    def build_online_learner_tag(self, tag):
        """
        Returns a dummy tag which uniquely identifies an appropriate
        OnlineLeaner from the ml.models package.
        """
        return '%s#%s' % (tag, self.uuid)

    def get_or_create_online_learner_facade(self, tag, preload=True):
        if not hasattr(self, '_learner_facade'):
            # Hack against circular import dependencies
            from ml.facade import LearnerFacade
            tag = self.build_online_learner_tag(tag)
            kwargs = {'experiment': self}
            learner_facade = LearnerFacade.get_or_create(
                tag, user=self.owner, preload=False, **kwargs
            )
            if preload:
                tag_learner = learner_facade.ml_model
                tag_learner.load_online_model()
            setattr(self, '_learner_facade', learner_facade)
        return getattr(self, '_learner_facade')

    def predict(self, *args, **kwargs):
        """ Treats the experiment as a (black box) classifier. """
        if not self.formula:
            raise NotImplementedError
        return self.formula.predict(*args, **kwargs)


@receiver(models.signals.pre_delete, sender=Experiment)
def clear_cache(sender, instance, **kwargs):
    for namespace in sender.EXPERIMENT_CACHED_DATA_KEY_TEMPLATES:
        instance.delete_cached_data(namespace)


@receiver(models.signals.post_delete, sender=Experiment)
def delete_formula(sender, instance, **kwargs):
    if instance.formula:
        instance.formula.delete()


class ExperimentAttribute(TimeStampedModel):
    """
    Defines the one-level tree-like structure for combining several experiments
    in order to augment predictions of the main experiment (i.e. the parent)
    with additional information, i.e. with independent predictions
    of the other attribute-specialized experiments (i.e. the children).
    """
    name = models.CharField('Name', max_length=300)

    parent = models.ForeignKey(Experiment, related_name='child_attribute',
                               help_text='Main classifier', on_delete=models.CASCADE)
    child = models.ForeignKey(Experiment, related_name='attribute_parent',
                              help_text='Attribute classifier', on_delete=models.CASCADE)


# -- Classifiers --

REGEX_CLF = 'regex'
BUILTIN_CLF = 'builtin'
TRAINED_CLF = 'trained'

CLF_TYPES = OrderedDict((
    (REGEX_CLF, 'Regular Expression'),
    (BUILTIN_CLF, 'BuiltIn Classifier'),
    (TRAINED_CLF, 'Trained Classifier'),
))


class GenericClassifier(TimeStampedModel):
    uuid = models.UUIDField('UUID', default=uuid.uuid4, db_index=True)
    clf_type = models.CharField(
        'Clf Type', max_length=10, choices=CLF_TYPES.items()
    )
    # Reverse=True if the application type is "Exclude"
    reverse = models.BooleanField('Reversed', default=False)
    # Optional name set by the user for distinguishing
    # between classifiers within an experiment
    name = models.CharField('Name', max_length=30, blank=True)

    @classmethod
    def get_clf_type(cls):
        raise NotImplementedError

    def __init__(self, *args, **kwargs):
        super(GenericClassifier, self).__init__(*args, **kwargs)
        # The actual type should always be available
        self.clf_type = self.get_clf_type()

    def save(self, *args, **kwargs):
        # Ensure that only the actual type is saved
        self.clf_type = self.get_clf_type()
        super(GenericClassifier, self).save(*args, **kwargs)

    def config(self, *args, **kwargs):
        """ Initialize, set up and edit the parameters of the classifier """
        raise NotImplementedError

    def fit(self, X, y):
        """
        Trains the classifier on the vector of text samples X and the list of
        labels y. Applicable only for trainable classifiers.
        """
        return None

    def predict(self, X):
        """
        Generate a list of boolean predictions for the vector of text samples X
        """
        raise NotImplementedError

    def __str__(self):
        return str(self.uuid)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.uuid)

    def to_dict(self):
        return {
            'uuid': str(self.uuid),
            'type': self.clf_type,
            'apply': 'exclude' if self.reverse else 'include',
            'name': self.name
        }

    def _find_changed_attrs(self, fe_attrs):
        """
        Checks whether the classifier is actually going to be changed after
        next configuring. The method is private and shouldn't be called outside
        the class (ideally it's intended to be used only inside the config
        method).

        :param fe_attrs: a dict describing the classifier's front-end state;
        :return changed_attrs: a list of fields which were edited by the user.
        """

        changed_attrs = []
        for attr_name in fe_attrs:
            be_attr_value = getattr(self, attr_name)  # old value
            fe_attr_value = fe_attrs[attr_name]  # new value
            if be_attr_value != fe_attr_value:
                setattr(self, attr_name, fe_attr_value)
                changed_attrs.append(attr_name)
        return changed_attrs

    class Meta:
        abstract = True


class RegexClassifier(GenericClassifier):
    expression = models.CharField(
        'Expression', max_length=1200, null=True, blank=True
    )

    @classmethod
    def get_clf_type(cls):
        return REGEX_CLF

    def config(self, expression, apply, **kwargs):
        reverse = apply == 'exclude'

        changed_attrs = self._find_changed_attrs({
            'expression': expression,
            'reverse': reverse,
            'name': kwargs.get('name', self.name)
        })

        if changed_attrs:
            if 'expression' in changed_attrs:
                # The internal regular expression should be recompiled again
                if hasattr(self, '_re_expression'):
                    delattr(self, '_re_expression')
            self.save()

    def _compile(self):
        if not hasattr(self, '_re_expression'):
            # Lazy compilation of the internal regular expression
            self._re_expression = re.compile(self.expression)

    def _search(self, text):
        self._compile()
        return self._re_expression.search(text)

    def _finditer(self, text):
        self._compile()
        return self._re_expression.finditer(text)

    def predict(self, X):
        predictions = list(map(bool, list(map(self._search, X))))
        if self.reverse:
            predictions = list(map(operator.not_, predictions))
        return np.array(predictions)

    def split(self, text):
        """
        Splits the given text into a disjunctive union of
        matching and non-matching parts.
        Returns a list of the following format: [(part, match), ...].
        """
        partition = []
        last_match_end = 0
        for match_obj in self._finditer(text):
            match_start = match_obj.start()
            if match_start - last_match_end > 0:
                non_matching_part = text[last_match_end : match_start]
                partition.append((non_matching_part, self.reverse))
            matching_part = match_obj.group()
            partition.append((matching_part, not self.reverse))
            last_match_end = match_obj.end()
        if last_match_end < len(text):
            non_matching_part = text[last_match_end:]
            partition.append((non_matching_part, self.reverse))
        return partition

    def to_dict(self):
        rc = super(RegexClassifier, self).to_dict()
        rc.update({
            'expression': self.expression
        })
        return rc


class BuiltInClassifier(GenericClassifier):
    model = models.CharField(
        'Model', max_length=100, null=True, blank=True
    )
    description = models.CharField(
        'Description', max_length=5000, null=True, blank=True
    )
    example = models.CharField(
        'Example', max_length=1000, null=True, blank=True
    )

    @classmethod
    def get_clf_type(cls):
        return BUILTIN_CLF

    def config(self, model, apply, **kwargs):
        reverse = apply == 'exclude'

        changed_attrs = self._find_changed_attrs({
            'model': model,
            'reverse': reverse,
            'name': kwargs.get('name', self.name)
        })

        if changed_attrs:
            self.save()

    def to_dict(self):
        bic = super(BuiltInClassifier, self).to_dict()
        bic.update({
            'model': self.model
        })
        return bic

    # ML-related stuff

    def build_pretrained_learner_tag(self):
        """
        Returns a dummy tag which uniquely identifies an appropriate
        PretrainedLearner from the ml.models package.
        """
        return '%s#%s' % (self.clf_type, self.model.lower())

    def get_or_create_pretrained_tag_learner(self, cache=True, preload=True,
                                             model_type=None):
        if not (cache and hasattr(self, '_tag_learner')):
            # Hack against circular import dependencies
            from ml.facade import LearnerFacade
            tag = self.build_pretrained_learner_tag()
            kwargs = {'offline_model_type': model_type}
            learner_facade = LearnerFacade.get_or_create(
                tag, preload=preload, **kwargs
            )
            tag_learner = learner_facade.ml_model
            setattr(self, '_tag_learner', tag_learner)
        return getattr(self, '_tag_learner')

    @property
    def trained(self):
        # Hack against circular import dependencies
        from ml.models import PretrainedLearner
        tag = self.build_pretrained_learner_tag()
        return PretrainedLearner.objects.filter(tag=tag).exists()

    def fit(self, X, y, model_type=None, persist=True):
        # Take into account that this method directly modifies
        # the single global model shared among all built-in classifiers
        # Each call to fit can update the model type of the corresponding
        # pretrained learner, so fetch the tag learner again and thus
        # refresh the cache
        # No need to load the offline model and the offline vectorizer,
        # since they will be fitted from scratch and thus overwritten anyway
        tag_learner = self.get_or_create_pretrained_tag_learner(
            cache=False, preload=False, model_type=model_type
        )
        tag_learner.prefit(X,
                           [[] for _ in range(len(X))],  # no flags
                           y)
        # Possible optimization for the case of model selection
        # allowing to actually save only the final (i.e. the best) model
        if persist:
            # Save the model and the vectorizer to the S3
            tag_learner.save_offline_model()
            tag_learner.offline_vectorizer.save_model()

    def predict(self, X):
        tag_learner = self.get_or_create_pretrained_tag_learner()
        if tag_learner.global_model is None:  # not trained yet
            raise NotImplementedError
        predictions = tag_learner.predict(
            X, [[] for _ in range(len(X))]  # no flags
        )
        if self.reverse:
            predictions = ~predictions  # flipping of booleans
        return predictions

    def decision_function(self, X):
        tag_learner = self.get_or_create_pretrained_tag_learner()
        if tag_learner.global_model is None:  # not trained yet
            raise NotImplementedError
        scores = tag_learner.decision_function(
            X, [[] for _ in range(len(X))]  # no flags
        )
        if self.reverse:
            scores = 1 - scores  # flipping of probabilities
        return scores


LOGREG_MODEL = 'logreg'
MLP_MODEL = 'mlp'
RF_MODEL = 'rf'
ADABOOST_MODEL = 'adaboost'

MODELS = OrderedDict((
    (LOGREG_MODEL, 'Logistic Regression'),
    (MLP_MODEL, 'Multi-layer Perceptron'),
    (RF_MODEL, 'Random Forest'),
    (ADABOOST_MODEL, 'AdaBoost SVM'),
))


class TrainedClassifier(GenericClassifier):
    model = models.CharField(
        'Model', max_length=10, choices=MODELS.items(), default=LOGREG_MODEL
    )
    datasets = models.ManyToManyField(
        Dataset, related_name='trained_classifiers', blank=True
    )

    dirty = models.BooleanField(default=True)
    training = models.BooleanField(default=False)

    # A parameter of the decision function, i.e.: an arbitrary sample x
    # is considered positive iff decision_function(x) > decision_threshold
    decision_threshold = models.FloatField('Decision Threshold', default=0)

    # A dict with evaluation scores which may include metrics like
    # precision, recall, f1 etc.
    scores = jsonfield.JSONField(
        'Scores', null=True, blank=True,
        load_kwargs={'object_pairs_hook': OrderedDict}
    )

    @classmethod
    def get_clf_type(cls):
        return TRAINED_CLF

    def config(self, datasets, model, apply, **kwargs):
        reverse = apply == 'exclude'

        changed_attrs = self._find_changed_attrs({
            'model': model,
            'reverse': reverse,
            'decision_threshold': kwargs.get('decision_threshold',
                                             self.decision_threshold),
            'name': kwargs.get('name', self.name)
        })

        if self.id is None:
            # Initial save in order to at least create the datasets field
            # and to get access to the corresponding relations
            self.save()

        be_datasets_ids = set(dataset.id for dataset in
                              self.datasets.all().only('id'))
        fe_datasets_ids = set(dataset['id'] for dataset in datasets)

        remove_datasets_ids = be_datasets_ids.difference(fe_datasets_ids)
        if remove_datasets_ids:
            self.datasets.remove(*remove_datasets_ids)

            DatasetMapping.objects.filter(dataset_id__in=remove_datasets_ids,
                                          clf_uuid=self.uuid).delete()

        datasets_mappings_by_id = {dataset['id']: dataset.get('mapping')
                                   for dataset in datasets}

        add_datasets_ids = fe_datasets_ids.difference(be_datasets_ids)
        if add_datasets_ids:
            self.datasets.add(*add_datasets_ids)

            for dataset_id in add_datasets_ids:
                dataset_mapping = DatasetMapping.objects.create(
                    dataset_id=dataset_id, clf_uuid=self.uuid
                )
                mapping = datasets_mappings_by_id[dataset_id]
                dataset_mapping.set_mapping(mapping)
                del datasets_mappings_by_id[dataset_id]

        any_mappings_changed = False
        for dataset_id in datasets_mappings_by_id:
            dataset_mapping = DatasetMapping.objects.get(
                dataset_id=dataset_id, clf_uuid=self.uuid
            )
            be_mapping = dataset_mapping.get_mapping()
            fe_mapping = datasets_mappings_by_id[dataset_id]
            if be_mapping != fe_mapping:
                any_mappings_changed = True
                dataset_mapping.set_mapping(fe_mapping)

        # Decide whether the classifier should be marked as dirty,
        # i.e. it's inconsistent now and should be retrained again

        # Unlike other changed attributes (like model, reverse,
        # decision_threshold), changed name doesn't imply dirtiness
        name_changed = 'name' in changed_attrs
        if name_changed:
            changed_attrs.remove('name')

        # If the model has been changed, then also reset the decision_threshold
        # (the old value doesn't make sense anymore for the new model type)
        if 'model' in changed_attrs:
            self.decision_threshold = 0

        inconsistent = any([changed_attrs, remove_datasets_ids,
                            add_datasets_ids, any_mappings_changed])

        if inconsistent:
            self.dirty = True
            self.scores = None

        if name_changed or inconsistent:
            self.save()

    def to_dict(self):
        datasets = []
        for dataset in self.datasets.all().only('id', 'name'):
            dataset_mapping = DatasetMapping.objects.get(
                dataset=dataset, clf_uuid=self.uuid
            )
            # The dataset can be unavailable for some users, so even if they
            # know its ID, they won't be able to access it. That's why we also
            # add the name of the dataset and the username of its owner
            # to the payload, so that at least we will be able to show a valid
            # notification to those users.
            datasets.append({
                'id': dataset.id,
                'name': dataset.name,
                'owner': dataset.owner.username,
                'mapping': dataset_mapping.get_mapping()
            })

        tc = super(TrainedClassifier, self).to_dict()
        tc.update({
            'model': self.model,
            'datasets': datasets,
            'dirty': self.dirty,
            'training': self.training,
            'decision_threshold': self.decision_threshold,
            'scores': self.scores
        })
        return tc

    # ML-related stuff

    def build_pretrained_learner_tag(self):
        """
        Returns a dummy tag which uniquely identifies an appropriate
        PretrainedLearner from the ml.models package.
        """
        return '%s#%s' % (self.clf_type, self.uuid)

    def get_or_create_pretrained_tag_learner(self, preload=True):
        if not hasattr(self, '_tag_learner'):
            # Hack against circular import dependencies
            from ml.facade import LearnerFacade
            tag = self.build_pretrained_learner_tag()
            kwargs = {'offline_model_type': self.model,
                      'offline_decision_threshold': self.decision_threshold}
            learner_facade = LearnerFacade.get_or_create(
                tag, preload=preload, **kwargs
            )
            tag_learner = learner_facade.ml_model
            setattr(self, '_tag_learner', tag_learner)
        return getattr(self, '_tag_learner')

    @property
    def trained(self):
        """
        Checks whether the classifier has been trained at least once and some
        ML model (may be even inconsistent now) has already been stored in S3.
        """
        tag_learner = self.get_or_create_pretrained_tag_learner()
        return tag_learner.global_model is not None

    def fit(self, X, y):
        # No need to load the offline model and the offline vectorizer,
        # since they will be fitted from scratch and thus overwritten anyway
        tag_learner = self.get_or_create_pretrained_tag_learner(preload=False)
        tag_learner.prefit(X,
                           [[] for _ in range(len(X))],  # no flags
                           y)
        # Save the model and the vectorizer to the S3
        tag_learner.save_offline_model()
        tag_learner.offline_vectorizer.save_model()

    def predict(self, X):
        tag_learner = self.get_or_create_pretrained_tag_learner()
        if tag_learner.global_model is None:  # not trained yet
            raise NotImplementedError
        predictions = tag_learner.predict(
            X, [[] for _ in range(len(X))]  # no flags
        )
        if self.reverse:
            predictions = ~predictions  # flipping of booleans
        return predictions

    def decision_function(self, X):
        tag_learner = self.get_or_create_pretrained_tag_learner()
        if tag_learner.global_model is None:  # not trained yet
            raise NotImplementedError
        scores = tag_learner.decision_function(
            X, [[] for _ in range(len(X))]  # no flags
        )
        if self.reverse:
            scores = -scores  # flipping of values symmetric with respect to 0
        return scores


@receiver(models.signals.pre_delete, sender=Dataset)
def make_trained_classifiers_dirty(sender, instance, **kwargs):
    instance.trained_classifiers.update(dirty=True)


@receiver(models.signals.pre_delete, sender=TrainedClassifier)
def delete_pretrained_learner(sender, instance, **kwargs):
    tag_learner = instance.get_or_create_pretrained_tag_learner(preload=False)
    pretrained_learner = tag_learner.meta
    pretrained_learner.delete()


CLF_CLASSES = OrderedDict(
    (clf_class.get_clf_type(), clf_class)
    for clf_class in GenericClassifier.__subclasses__()
)


def create_classifier(clf_data):
    """ Factory function for spawning different types of classifiers. """
    clf_type = clf_data.pop('type')
    clf_class = CLF_CLASSES[clf_type]
    clf_instance = clf_class()
    clf_instance.config(**clf_data)
    return clf_instance


def get_classifer(clf_uuid):
    """ Tries to find a classifier instance by the given UUID. """
    clf_instance = None
    for clf_type in CLF_CLASSES:
        clf_class = CLF_CLASSES[clf_type]
        try:
            clf_instance = clf_class.objects.get(uuid=clf_uuid)
            break
        except clf_class.DoesNotExist:
            continue
    return clf_instance
