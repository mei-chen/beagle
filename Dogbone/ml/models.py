import os
import uuid
import logging
import jsonfield
import StringIO
import cPickle as pickle

from collections import OrderedDict

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from model_utils.models import TimeStampedModel
from integrations.s3 import get_s3_bucket_manager

from .exceptions import ModelNotFoundException

from sklearn.linear_model import PassiveAggressiveClassifier, LogisticRegression


class OnlineLearner(TimeStampedModel):
    # UUID used to identify the stored model
    model_uuid = models.CharField('Model UUID', max_length=100, unique=True)

    # The path to the model in S3
    model_s3 = models.CharField('S3 Model address', blank=True, null=True, max_length=255,
                                help_text='Format: bucket:filename')

    # The user that trains this classifier
    owner = models.ForeignKey(User)

    # Triggering tag
    tag = models.CharField('Tag', max_length=300)

    # Samples set
    samples = jsonfield.JSONField(load_kwargs={'object_pairs_hook': OrderedDict}, null=True, blank=True, default=None)

    # The number of positive samples used for training yet
    positive_set_size = models.IntegerField(default=0)

    # It has a pretrained component
    pretrained = models.BooleanField('Pretrained', default=False)

    # Enabled flag
    active = models.BooleanField('Active', default=True)

    # Flag of deletion
    deleted = models.BooleanField('Deleted', default=False)

    # Highlight color
    color_code = models.CharField(default="#f9f6fb", max_length=7)

    @classmethod
    def init_ml_model(cls):
        """
        Returns an instance of the online classifier that Beagle uses
        Use this every time you need to instantiate an Online Classifier
        """
        return PassiveAggressiveClassifier(fit_intercept=True)

    def add_sample(self, text, flags, label, infered=False):
        if not self.samples:
            self.samples = {
                'text': [text],
                'flags': [flags],
                'label': [label],
                'infered': [infered],
            }
        else:
            self.samples['text'].append(text)
            self.samples['flags'].append(flags)
            self.samples['label'].append(label)
            self.samples['infered'].append(infered)
        if label is True:
            self.positive_set_size += 1
        self.save()

    def discard_sample_by_idx(self, idx):
        self.samples['text'].pop(idx)
        self.samples['flags'].pop(idx)
        self.samples['infered'].pop(idx)
        label = self.samples['label'].pop(idx)

        if label is True:
            self.positive_set_size -= 1
        self.save()

    def reset(self):
        self.samples = None
        self.positive_set_size = 0

    def to_dict(self):
        total_size = (len(self.samples['text'])
                      if self.samples and 'text' in self.samples
                      else 0)
        noninfered_size = (len(filter(lambda x: not x, self.samples['infered']))
                           if self.samples and 'infered' in self.samples
                           else 0)

        return {
            'name': self.tag,
            'positive_set_size': self.positive_set_size,
            'noninfered_set_size': noninfered_size,
            'total_set_size': total_size,
            'deleted': self.deleted,
            'active': self.active,
            'pretrained': self.pretrained,
            'id': self.id,
            'color_code': self.color_code
        }

    def build_default_storage_string(self):
        file_name = "model_%s.pkl" % self.model_uuid
        return "%s:online_learners/%s" % (settings.PREDICTION_MODELS_BUCKET, file_name)

    def is_mature(self):
        from ml.facade import LEARNER_MATURITY_THREASHOLD
        return (self.pretrained or
                self.positive_set_size >= LEARNER_MATURITY_THREASHOLD)

    def load_ml_model(self):
        """
        Loads the pickled machine learning model
        from the S3 location stored internally in the Django model
        :return: the machine learning model
        """
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)
        serialized_model = manager.read_to_string(self.model_s3.split(':')[1])

        temp_file = StringIO.StringIO()
        temp_file.write(serialized_model)
        temp_file.seek(0)

        try:
            model_params = pickle.load(temp_file)
        except EOFError:
            logging.warning('S3 path is incorrect: %s or we were just looking for a pre-trained classifier'
                            % self.model_s3.split(':')[1])
            raise ModelNotFoundException("S3 path is incorrect")

        ml_model = self.init_ml_model()
        ml_model.coef_, ml_model.intercept_, ml_model.classes_ = model_params

        return ml_model

    def save_ml_model(self, ml_model):
        """
        Saves the specified machine to the S3 location
        :param ml_model: the machine learning model
        :return: None
        """
        manager = get_s3_bucket_manager(settings.PREDICTION_MODELS_BUCKET)
        temp_file = StringIO.StringIO()

        # Only save the data, not the entire sklearn object
        pickle.dump((ml_model.coef_, ml_model.intercept_, ml_model.classes_), temp_file)

        temp_file.seek(0)
        manager.save_string(self.model_s3.split(':')[1], temp_file.read())

    def save(self, *args, **kwargs):
        """ Auto generate an unique ID """
        if not self.model_uuid:
            self.model_uuid = str(uuid.uuid4())

        # Generate the default S3 path
        if not self.pk and not self.model_s3:
            self.model_s3 = self.build_default_storage_string()

        if not self.samples:
            self.samples = None

        return super(OnlineLearner, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'Tag [%s] - %s' % (self.tag, self.owner.username)


class AbstractPretrainedLearner(TimeStampedModel):
    """
    Abstracts the PretrainedLearner such that it can be extended by
    LearnerAttribute without a PretrainedLearner object being created for each
    new LearnerAttribute.
    """

    class Meta:
        abstract = True

    OFFLINE_MODELS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')

    # UUID used to identify the stored model
    model_uuid = models.CharField('Model UUID', max_length=100, unique=True)

    # Triggering tag
    tag = models.CharField('Tag', max_length=300)

    # Optional description (may be shown to the user)
    description = models.CharField('Description', max_length=2000, default='', null=True, blank=True)

    @classmethod
    def init_ml_model(cls):
        return LogisticRegression(C=1e5)

    @classmethod
    def load_ml_model(cls, tag):
        model_path = os.path.join(cls.OFFLINE_MODELS_PATH, cls.stored_model_name(tag))
        logging.info('Loading offline model from path: %s' % model_path)
        if os.path.exists(model_path):
            with open(model_path, 'rb') as model_in:
                ml_model = cls.init_ml_model()
                ml_model.coef_, ml_model.intercept_, ml_model.classes_ = pickle.load(model_in)

                return ml_model
        else:
            logging.error('Could not load the model from %s because file does not exist' % model_path)

    @classmethod
    def save_ml_model(cls, tag, ml_model):
        if not os.path.exists(cls.OFFLINE_MODELS_PATH):
            os.makedirs(cls.OFFLINE_MODELS_PATH)

        model_path = os.path.join(cls.OFFLINE_MODELS_PATH, cls.stored_model_name(tag))

        with open(model_path, 'wb') as model_out:
            pickle.dump((ml_model.coef_,
                         ml_model.intercept_,
                         ml_model.classes_), model_out)

    @classmethod
    def load_ml_vectorizer(cls, tag):
        vec_path = os.path.join(cls.OFFLINE_MODELS_PATH, cls.stored_vectorizer_name(tag))
        logging.info('Loading vectorizer from path: %s' % vec_path)
        if os.path.exists(vec_path):
            with open(vec_path, 'rb') as vec_in:
                vectorizer = pickle.load(vec_in)
                return vectorizer
        else:
            logging.error('Could not load the vec from %s because file does not exist' % vec_path)

    @classmethod
    def save_ml_vectorizer(cls, tag, vectorizer):
        if not os.path.exists(cls.OFFLINE_MODELS_PATH):
            os.makedirs(cls.OFFLINE_MODELS_PATH)

        vec_path = os.path.join(cls.OFFLINE_MODELS_PATH, cls.stored_vectorizer_name(tag))

        with open(vec_path, 'wb') as vec_out:
            pickle.dump(vectorizer, vec_out)

    def save(self, *args, **kwargs):
        """ Auto generate an unique ID """
        if not self.model_uuid:
            self.model_uuid = str(uuid.uuid4())

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

    def is_mature(self):
        return True

    def __unicode__(self):
        return u'Pretrained Tag [%s]' % (self.tag)

    def to_dict(self):
        return {
            'name': self.tag,
            'description': self.description
        }


class LearnerAttribute(AbstractPretrainedLearner):
    """
    Based on a PretrainedLearner, but it's used for a specific purpose and has
    a specific output (e.g. Y/T/B for party assignation, True/False for boolean
    attributes)
    """

    OFFLINE_MODELS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'attrs')
    # Note: Inherits model_uuid and the model save/load functions from PretrainedLearner

    # Name / Short description
    name = models.CharField('Name', max_length=300, default='', blank=True)

    # Parent PretrainedLearner
    parent_learner = models.ForeignKey(PretrainedLearner, related_name='learner_attribute', null=True, default=None)

    # List of all the possible labels/outputs
    output_range = jsonfield.JSONField(null=True, blank=True, default=None)

    @classmethod
    def stored_model_name(cls, tag):
        return 'model_%s_attr.pkl' % tag

    @classmethod
    def stored_vectorizer_name(cls, tag):
        return 'vectorizer_%s_attr.pkl' % tag

    def __unicode__(self):
        return u'LearnerAttribute [%s/%s]' % (self.tag or self.parent_learner.tag, self.name)

    def to_dict(self):
        return {
            'name': self.name,
            'parent': self.parent_learner.tag if self.parent_learner else None,
            'output_range': self.output_range
        }
