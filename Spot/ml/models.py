from collections import OrderedDict
from io import StringIO, BytesIO
import logging
import itertools
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
import joblib
import jsonfield
from model_utils.models import TimeStampedModel
from scipy.special import logit
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier, SGDClassifier
from sklearn.neural_network import MLPClassifier

from experiment.models import Experiment
from integrations.s3 import get_s3_bucket_manager


RANDOM_STATE = 42


class ModelS3Mixin(object):

    @classmethod
    def generate_model_s3(cls, key_s3):
        return cls.build_default_storage_string(cls.stored_model_name(key_s3))

    def model_s3(self):
        return self.generate_model_s3(self.key_s3)

    model_s3.short_description = 'Model S3 address (bucket:filename)'
    model_s3 = property(model_s3)


class VectorizerS3Mixin(object):

    @classmethod
    def generate_vectorizer_s3(cls, key_s3):
        return cls.build_default_storage_string(cls.stored_vectorizer_name(key_s3))

    def vectorizer_s3(self):
        return self.generate_vectorizer_s3(self.key_s3)

    vectorizer_s3.short_description = 'Vectorizer S3 address (bucket:filename)'
    vectorizer_s3 = property(vectorizer_s3)


class SetSizeMixin(object):

    @property
    def total_set_size(self):
        return len((self.samples or {}).get('text', []))

    @property
    def positive_set_size(self):
        return sum((self.samples or {}).get('label', []))

    @property
    def negative_set_size(self):
        return self.total_set_size - self.positive_set_size

    @property
    def infered_set_size(self):
        return sum((self.samples or {}).get('infered', []))

    @property
    def noninfered_set_size(self):
        return self.total_set_size - self.infered_set_size


class OnlineDataset(SetSizeMixin, TimeStampedModel):
    # UUID used to identify the dataset
    uuid = models.CharField('UUID', max_length=100, unique=True)

    # Set of samples
    samples = jsonfield.JSONField('Samples', load_kwargs={'object_pairs_hook': OrderedDict},
                                  null=True, blank=True, default=None)

    def add_sample(self, text, flags, label, infered=False, persist=True):
        if not self.samples:
            self.samples = OrderedDict([
                ('text', [text]),
                ('flags', [flags]),
                ('label', [label]),
                ('infered', [infered]),
            ])
        else:
            self.samples['text'].append(text)
            self.samples['flags'].append(flags)
            self.samples['label'].append(label)
            self.samples['infered'].append(infered)
        if persist:
            self.save()

    def add_sample_batch(self, samples):
        if not samples:
            return
        # Save the dataset only once immediately after adding all samples
        for text, flags, label, infered in itertools.izip(samples['text'],
                                                          samples['flags'],
                                                          samples['label'],
                                                          samples['infered']):
            self.add_sample(text, flags, label, infered, persist=False)
        self.save()

    def edit_sample_by_idx(self, idx, text=None, label=None):
        if text is not None:
            self.samples['text'][idx] = text
        if label is not None and not self.samples['infered'][idx]:
            self.samples['label'][idx] = label
        self.save()

    def discard_sample_by_idx(self, idx):
        self.samples['text'].pop(idx)
        self.samples['flags'].pop(idx)
        self.samples['infered'].pop(idx)
        self.samples['label'].pop(idx)
        self.save()

    def reset(self):
        self.samples = None
        self.save()

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        return super(OnlineDataset, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.uuid


class MLModelWrapperBase(object):

    def __init__(self, ml_model):
        self.ml_model = ml_model

    def fit(self, X, y):
        return self.ml_model.fit(X, y)

    def decision_function(self, X):
        # Should be a symmetric function centered at 0, i.e. negative or
        # positive values are considered as belonging to the negative or
        # positive class respectively (the class of 0 is more of a convention)
        return self.ml_model.decision_function(X)

    def predict(self, X):
        return self.ml_model.predict(X)

    def predict_proba(self, X):
        # Since the classification is always binary, simply return the
        # probability of belonging to the positive class
        return self.ml_model.predict_proba(X)[:, 1]

    def serialize(self):
        raise NotImplementedError

    def deserialize(self, ml_model_params):
        raise NotImplementedError


class OnlineMLModelWrapperBase(MLModelWrapperBase):

    def partial_fit(self, X, y):
        classes = None
        if self.ml_model.classes_ is None:
            # On the very first run the classes are not initialized yet
            classes = [True, False]
        return self.ml_model.partial_fit(X, y, classes)


class PassiveAggressiveModelWrapper(OnlineMLModelWrapperBase):

    def __init__(self):
        model = PassiveAggressiveClassifier(fit_intercept=True,
                                            random_state=RANDOM_STATE)
        super(PassiveAggressiveModelWrapper, self).__init__(model)

    def predict_proba(self, X):
        # There is no `predict_proba` method, so use
        # probability estimation for logistic regression
        return self.ml_model._predict_proba_lr(X)[:, 1]

    def serialize(self):
        data = (self.ml_model.coef_, self.ml_model.intercept_, self.ml_model.classes_)
        return data

    def deserialize(self, ml_model_params):
        self.ml_model.coef_, self.ml_model.intercept_, self.ml_model.classes_ = ml_model_params


LEARNER_MATURITY_THRESHOLD = 12


class OnlineLearner(ModelS3Mixin, SetSizeMixin, TimeStampedModel):
    # UUID used to identify the learner
    uuid = models.CharField('UUID', max_length=100, unique=True)

    # The user whom the learner belongs to (not necessarily the trainer!)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # Triggering tag
    tag = models.CharField('Tag', max_length=300, db_index=True)

    # Enclosing experiment (optional)
    experiment = models.ForeignKey(Experiment, related_name='online_learners',
                                   on_delete=models.SET_DEFAULT,
                                   null=True, blank=True, default=None)

    # Dataset containing actual samples and encapsulating their processing logic
    dataset = models.OneToOneField(OnlineDataset, related_name='learner',
                                   on_delete=models.SET_DEFAULT,
                                   null=True, blank=True, default=None)

    # It has a pretrained component
    pretrained = models.BooleanField('Pretrained', default=False)

    # Enabled flag
    active = models.BooleanField('Active', default=True)

    # Flag of deletion
    deleted = models.BooleanField('Deleted', default=False)

    @property
    def key_s3(self):
        return self.uuid

    @classmethod
    def init_ml_model(cls):
        """
        Returns an instance of the online classifier that Beagle uses.
        Use this every time you need to instantiate an Online Classifier.
        """
        return PassiveAggressiveModelWrapper()

    @classmethod
    def serialize_ml_model(cls, ml_model, fout):
        data = ml_model.serialize()
        joblib.dump(data, fout, compress=True)

    @classmethod
    def deserialize_ml_model(cls, fin):
        ml_model_params = joblib.load(fin)
        ml_model = cls.init_ml_model()
        ml_model.deserialize(ml_model_params)
        return ml_model

    @classmethod
    def build_default_storage_string(self, file_name):
        return '%s:online_learners/%s' % (settings.PREDICTION_MODELS_BUCKET, file_name)

    @classmethod
    def stored_model_name(cls, uuid):
        return 'model_%s.pkl' % uuid

    @property
    def samples(self):
        """ Allows direct access to the samples. """
        return self.dataset.samples if self.dataset else None

    def add_sample(self, text, flags, label, infered=False):
        if not self.dataset:
            self.dataset = OnlineDataset.objects.create()
            self.save()
        self.dataset.add_sample(text, flags, label, infered)

    def edit_sample_by_idx(self, idx, text=None, label=None):
        self.dataset.edit_sample_by_idx(idx, text, label)

    def discard_sample_by_idx(self, idx):
        self.dataset.discard_sample_by_idx(idx)

    def reset(self):
        if self.dataset:
            self.dataset.reset()
            self.clear_s3()

    @property
    def is_mature(self):
        return self.pretrained or self.positive_set_size >= LEARNER_MATURITY_THRESHOLD

    @property
    def maturity(self):
        return self.positive_set_size / float(LEARNER_MATURITY_THRESHOLD)

    def to_dict(self):
        return {
            'tag': self.tag,
            'pretrained': self.pretrained,
            'active': self.active,
            'deleted': self.deleted,
            'stats': {
                'positive': self.positive_set_size,
                'negative': self.negative_set_size,
                'total': self.total_set_size,
                'infered': self.infered_set_size,
                'noninfered': self.noninfered_set_size,
            },
            'is_mature': self.is_mature,
            'maturity': self.maturity,
        }

    def load_ml_model(self):
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)

        model_s3_path = self.model_s3.split(':')[1]

        # When no model is found, None is returned, so replace it with an
        # empty string (another exception will be raised anyway, but at least
        # it will be handled in the try-except block below)
        serialized_model = manager.read_to_string(model_s3_path) or ''

        temp_file = StringIO()
        temp_file.write(serialized_model)
        temp_file.seek(0)

        try:
            logging.info('Loading online model from S3 path: %s' % model_s3_path)
            ml_model = self.deserialize_ml_model(temp_file)
            return ml_model

        except EOFError:
            logging.error('Could not load online model (no such file) from S3 path: %s' % model_s3_path)

    def save_ml_model(self, ml_model):
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)

        model_s3_path = self.model_s3.split(':')[1]

        temp_file = StringIO()

        logging.info('Saving online model to S3 path: %s' % model_s3_path)
        self.serialize_ml_model(ml_model, temp_file)

        temp_file.seek(0)

        manager.save_string(model_s3_path, temp_file.read())

    def clear_s3(self):
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)

        model_s3_key = self.model_s3.split(':')[1]

        manager.delete_key(model_s3_key)

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        if self.dataset:
            self.dataset.save()
        return super(OnlineLearner, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'OL: [%s] %s' % (self.owner, self.tag)


@receiver(models.signals.post_delete, sender=OnlineLearner)
def delete_dataset(sender, instance, **kwargs):
    if instance.dataset:
        instance.dataset.delete()


LOGREG_MODEL = 'logreg'
MLP_MODEL = 'mlp'
RF_MODEL = 'rf'
ADABOOST_MODEL = 'adaboost'

MODEL_TYPES = OrderedDict((
    (LOGREG_MODEL, 'Logistic Regression'),
    (MLP_MODEL, 'Multi-layer Perceptron'),
    (RF_MODEL, 'Random Forest'),
    (ADABOOST_MODEL, 'AdaBoost SVM'),
))


class OfflineMLModelWrapperBase(MLModelWrapperBase):

    @classmethod
    def get_model_type(cls):
        raise NotImplementedError

    def predict(self, X, decision_threshold=None):
        if decision_threshold is None:
            return self.ml_model.predict(X)
        else:
            return self.decision_function(X) > decision_threshold


class LogRegModelWrapper(OfflineMLModelWrapperBase):

    def __init__(self):
        model = LogisticRegression(C=1e5, random_state=RANDOM_STATE)
        super(LogRegModelWrapper, self).__init__(model)

    @classmethod
    def get_model_type(cls):
        return LOGREG_MODEL

    def serialize(self):
        data = (
            LOGREG_MODEL,  # add model type for correct loading
            (self.ml_model.coef_, self.ml_model.intercept_, self.ml_model.classes_)
        )
        return data

    def deserialize(self, ml_model_params):
        self.ml_model.coef_, self.ml_model.intercept_, self.ml_model.classes_ = ml_model_params


class MLPModelWrapper(OfflineMLModelWrapperBase):

    def __init__(self):
        model = MLPClassifier(hidden_layer_sizes=(10,), solver='lbfgs',
                              activation='logistic', alpha=1e-3,
                              random_state=RANDOM_STATE)
        super(MLPModelWrapper, self).__init__(model)

    @classmethod
    def get_model_type(cls):
        return MLP_MODEL

    def decision_function(self, X):
        # There is no `decision_function` method, so use
        # inverse (i.e. logit) values of sigmoid probabilities
        return logit(self.predict_proba(X))

    def serialize(self):
        data = (
            MLP_MODEL,  # add model type for correct loading
            (self.ml_model.coefs_, self.ml_model.intercepts_,
             self.ml_model._label_binarizer, self.ml_model.n_layers_,
             self.ml_model.n_outputs_, self.ml_model.out_activation_)
        )
        return data

    def deserialize(self, ml_model_params):
        self.ml_model.coefs_, self.ml_model.intercepts_, \
            self.ml_model._label_binarizer, self.ml_model.n_layers_, \
                self.ml_model.n_outputs_, self.ml_model.out_activation_ = ml_model_params


class RFModelWrapper(OfflineMLModelWrapperBase):

    def __init__(self):
        model = RandomForestClassifier(random_state=RANDOM_STATE)
        super(RFModelWrapper, self).__init__(model)

    @classmethod
    def get_model_type(cls):
        return RF_MODEL

    def decision_function(self, X):
        # There is no `decision_function` method, so use the `predict_proba`
        # method instead by mapping the the range [0, 1] to the range [-1, 1]
        return 2 * self.predict_proba(X) - 1

    def serialize(self):
        data = (
            RF_MODEL,  # add model type for correct loading
            (self.ml_model.estimators_, self.ml_model.classes_, self.ml_model.n_outputs_)
        )
        return data

    def deserialize(self, ml_model_params):
        self.ml_model.estimators_, self.ml_model.classes_, self.ml_model.n_outputs_ = ml_model_params


class AdaBoostModelWrapper(OfflineMLModelWrapperBase):

    def __init__(self):
        svm_classifier = SGDClassifier(random_state=RANDOM_STATE)
        model = AdaBoostClassifier(base_estimator=svm_classifier,
                                   n_estimators=10,
                                   algorithm='SAMME',
                                   random_state=RANDOM_STATE)
        super(AdaBoostModelWrapper, self).__init__(model)

    @classmethod
    def get_model_type(cls):
        return ADABOOST_MODEL

    def predict_proba(self, X):
        # Since "probability estimates are not available for loss='hinge'",
        # therefore use the `decision_function` method instead;
        # it returns values from the range [-1, 1], and for binary
        # classification values closer to -1 or 1 mean more like the
        # negative or positive class respectively
        return (self.decision_function(X) + 1) / 2

    def serialize(self):
        data = (
            ADABOOST_MODEL,  # add model type for correct loading
            (self.ml_model.estimators_, self.ml_model.estimator_weights_,
             self.ml_model.classes_, self.ml_model.n_classes_)
        )
        return data

    def deserialize(self, ml_model_params):
        self.ml_model.estimators_, self.ml_model.estimator_weights_, \
            self.ml_model.classes_, self.ml_model.n_classes_ = ml_model_params


MODEL_CLASSES = OrderedDict(
    (model_class.get_model_type(), model_class)
    for model_class in OfflineMLModelWrapperBase.__subclasses__()
)


class AbstractPretrainedLearner(ModelS3Mixin, VectorizerS3Mixin, TimeStampedModel):
    """
    Abstracts the PretrainedLearner such that it can be extended by
    LearnerAttribute without a PretrainedLearner object being created for each
    new LearnerAttribute.
    """

    class Meta:
        abstract = True

    # UUID used to identify the learner
    uuid = models.CharField('UUID', max_length=100, unique=True)

    # Triggering tag
    tag = models.CharField('Tag', max_length=300, db_index=True)

    # Optional description (may be shown to the user)
    description = models.CharField('Description', max_length=2000, default='', null=True, blank=True)

    # Type of ML model used internally
    model_type = models.CharField('Model Type', max_length=10, choices=MODEL_TYPES.items(), default=LOGREG_MODEL)

    @property
    def key_s3(self):
        return self.tag

    @classmethod
    def init_ml_model(cls, model_type=None):
        if model_type is None:
            model_type = LOGREG_MODEL  # default model

        ml_model_class = MODEL_CLASSES.get(model_type)
        if ml_model_class is None:
            raise NotImplementedError

        ml_model = ml_model_class()
        return ml_model

    @classmethod
    def serialize_ml_model(cls, ml_model, fout):
        data = ml_model.serialize()
        joblib.dump(data, fout, compress=True)

    @classmethod
    def deserialize_ml_model(cls, fin):
        model_type, ml_model_params = joblib.load(fin)
        ml_model = cls.init_ml_model(model_type)
        ml_model.deserialize(ml_model_params)
        return ml_model

    @classmethod
    def build_default_storage_string(cls, file_name):
        return '%s:pretrained_learners/%s' % (settings.PREDICTION_MODELS_BUCKET, file_name)

    @classmethod
    def stored_model_name(cls, tag):
        raise NotImplementedError

    @classmethod
    def stored_vectorizer_name(cls, tag):
        raise NotImplementedError

    @classmethod
    def load_ml_model(cls, tag):
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)

        model_s3_path = cls.generate_model_s3(tag).split(':')[1]

        # When no model is found, None is returned, so replace it with an
        # empty string (another exception will be raised anyway, but at least
        # it will be handled in the try-except block below)
        serialized_model = manager.read_to_string(model_s3_path) or ''

        temp_file = StringIO()
        temp_file.write(serialized_model)
        temp_file.seek(0)

        try:
            logging.info('Loading offline model from S3 path: %s' % model_s3_path)
            ml_model = cls.deserialize_ml_model(temp_file)
            return ml_model

        except EOFError:
            logging.error('Could not load offline model (no such file) from S3 path: %s' % model_s3_path)

    @classmethod
    def save_ml_model(cls, tag, ml_model):
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)

        model_s3_path = cls.generate_model_s3(tag).split(':')[1]

        temp_file = BytesIO()

        logging.info('Saving offline model to S3 path: %s' % model_s3_path)
        cls.serialize_ml_model(ml_model, temp_file)

        temp_file.seek(0)

        manager.save_string(model_s3_path, temp_file.read())

    @classmethod
    def load_ml_vectorizer(cls, tag):
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)

        vectorizer_s3_path = cls.generate_vectorizer_s3(tag).split(':')[1]

        # When no vectorizer is found, None is returned, so replace it with an
        # empty string (another exception will be raised anyway, but at least
        # it will be handled in the try-except block below)
        serialized_vectorizer = manager.read_to_string(vectorizer_s3_path) or ''

        temp_file = StringIO()
        temp_file.write(serialized_vectorizer)
        temp_file.seek(0)

        try:
            logging.info('Loading offline vectorizer from S3 path: %s' % vectorizer_s3_path)
            ml_vectorizer = joblib.load(temp_file)
            return ml_vectorizer

        except EOFError:
            logging.error('Could not load offline vectorizer (no such file) from S3 path: %s' % vectorizer_s3_path)

    @classmethod
    def save_ml_vectorizer(cls, tag, vectorizer):
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)

        vectorizer_s3_path = cls.generate_vectorizer_s3(tag).split(':')[1]

        temp_file = BytesIO()

        logging.info('Saving offline vectorizer to S3 path: %s' % vectorizer_s3_path)
        joblib.dump(vectorizer, temp_file, compress=True)

        temp_file.seek(0)

        manager.save_string(vectorizer_s3_path, temp_file.read())

    def clear_s3(self):
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)

        model_s3_key = self.model_s3.split(':')[1]
        vectorizer_s3_key = self.vectorizer_s3.split(':')[1]

        manager.delete_key(model_s3_key)
        manager.delete_key(vectorizer_s3_key)

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        return super(AbstractPretrainedLearner, self).save(*args, **kwargs)


class PretrainedLearner(AbstractPretrainedLearner):

    # If none, this learner is exclusive to the specified username
    exclusivity = models.CharField('Exclusive to:', max_length=200, default=None, null=True, blank=True)

    @classmethod
    def stored_model_name(cls, tag):
        return 'model_%s_global.pkl' % tag

    @classmethod
    def stored_vectorizer_name(cls, tag):
        return 'vectorizer_%s.pkl' % tag

    def to_dict(self):
        return {
            'tag': self.tag,
            'exclusivity': self.exclusivity,
        }

    @property
    def is_mature(self):
        return True

    def __unicode__(self):
        return u'PL: %s' % self.tag


class LearnerAttribute(AbstractPretrainedLearner):
    """
    Based on a PretrainedLearner, but it's used for a specific purpose and has
    a specific output (e.g. Y/T/B for party assignation, True/False for boolean
    attributes)
    """

    # Name / Short description
    name = models.CharField('Name', max_length=300, default='', blank=True)

    # Parent PretrainedLearner
    parent_learner = models.ForeignKey(PretrainedLearner, related_name='learner_attribute', null=True, default=None, on_delete=models.CASCADE)

    # List of all the possible labels/outputs
    output_range = jsonfield.JSONField(null=True, blank=True, default=None)

    @classmethod
    def stored_model_name(cls, tag):
        return 'attrs/model_%s_attr.pkl' % tag

    @classmethod
    def stored_vectorizer_name(cls, tag):
        return 'attrs/vectorizer_%s_attr.pkl' % tag

    def __unicode__(self):
        return u'LearnerAttribute [%s/%s]' % (self.tag or self.parent_learner.tag, self.name)

    def to_dict(self):
        return {
            'name': self.name,
            'parent': self.parent_learner.tag if self.parent_learner else None,
            'output_range': self.output_range
        }


def clear_s3(sender, instance, **kwargs):
    """
    Receiver function for connecting to pre_delete signal of OnlineLearner
    or AbstractPretrainedLearner's concrete subclasses.
    """

    if issubclass(sender, (OnlineLearner, AbstractPretrainedLearner)):
        instance.clear_s3()


models.signals.pre_delete.connect(receiver=clear_s3, sender=OnlineLearner)


for subclass in AbstractPretrainedLearner.__subclasses__():
    models.signals.pre_delete.connect(receiver=clear_s3, sender=subclass)
