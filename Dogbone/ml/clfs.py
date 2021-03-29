import os
import logging
import numpy as np
import pickle as pkl

from ml.vecs import (
    TagLearnerOnlineVectorizer, TagLearnerOfflineVectorizer,
    LearnerAttributeVectorizer,
)
from ml.models import OnlineLearner, PretrainedLearner, LearnerAttribute
from ml.exceptions import ModelNotFoundException

from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer


class TagLearner:
    """
    Could have a pre-trained classifier and should be able to improve when users
    provide more data.

    Designed as an Ensemble classifier with an online classifier at it's core.
    Beside the online classifier, TagLearner can also feature a pre-trained
    offline classifier that, if exists, is common to all the TagLearners for
    a specific tag.

    Each user has it's own TagLearner for a specific tag. Relationship between
    TagLearner and offline model for a tag is M:1 (more TagLearners can build
    on top of the same offline pre-trained model).
    """

    def __init__(self, db_model, flags=None):
        self.model = None
        self.global_model = None
        self.online_vectorizer = TagLearnerOnlineVectorizer(db_model.model_uuid, db_model.tag)
        self.offline_vectorizer = TagLearnerOfflineVectorizer(db_model.model_uuid, db_model.tag)
        self.meta = db_model

        self.flags = ['LIABILITY', 'RESPONSIBILITY', 'TERMINATION']
        if flags:
            self.flags = flags
        self.loaded_from_pkl = False

        # Initial fitting of the online vectorizer
        self.online_vectorizer.fit(self.flags)
        self.offline_vectorizer.fit_dict(self.flags)

    def reset(self, initial_samples=None):
        if initial_samples is None:
            initial_samples = []

        self.model = OnlineLearner.init_ml_model()
        X_text = [s[0] for s in initial_samples]
        X_flags = [s[1] for s in initial_samples]
        y = [s[2] for s in initial_samples]

        if X_text:
            self.fit(X_text, X_flags, y)

    def prefit(self, X_text, X_flags, y):
        """
        (Re)trains the offline global model used for the current tag.
        X_text:  list of sentences
        X_flags: list of lists of flags
        y:       list of labels
        """
        # Init the vocabulary from the whole dataset
        self.offline_vectorizer.fit(X_text, self.flags)

        if not self.global_model:
            self.global_model = PretrainedLearner.init_ml_model()
        X = self.offline_vectorizer.transform(self.meta.tag, X_text, X_flags)
        self.global_model.fit(X, y)

    def fit(self, X_text, X_flags, y):
        """
        Trains the user specific online model (in a partial_fit manner).
        X_text:  list of sentences
        X_flags: list of lists of flags
        y:       list of labels
        """
        if not self.model:
            self.model = OnlineLearner.init_ml_model()
        X = self.online_vectorizer.transform(self.meta.tag, X_text, X_flags)
        classes = None
        if self.model.classes_ is None:
            # On first run the classes are not initialized yet
            classes = [True, False]
        self.model.partial_fit(X, y, classes)

    def predict(self, X_text, X_flags):
        """ Takes list of sentences, list of lists of flags, returns list of labels """
        scores = self.decision_score(X_text, X_flags)
        return (scores > 0)

    def decision_score(self, X_text, X_flags):
        """ Returns the decision function scores """
        # Include both online and offline models
        offline_pred = np.array([0.] * len(X_text))
        online_pred = np.array([0.] * len(X_text))
        offline_confidence = 0.
        online_confidence = 0.

        if self.global_model:
            X_offline = self.offline_vectorizer.transform(self.meta.tag, X_text, X_flags)
            offline_pred = self.global_model.decision_function(X_offline)
            offline_confidence = 0.6

        if self.model:
            X = self.online_vectorizer.transform(self.meta.tag, X_text, X_flags)
            online_pred = self.model.decision_function(X)
            online_confidence = 0.4

        # Normalize confidence ratios
        offline_confidence /= (offline_confidence + online_confidence) or .000001
        online_confidence /= (offline_confidence + online_confidence) or .000001

        scores = offline_confidence * offline_pred + online_confidence * online_pred
        return scores

    def load_online_model(self):
        self.model = self.meta.load_ml_model()
        if self.model is not None:
            self.loaded_from_pkl = True

    def load_offline_model(self):
        self.global_model = PretrainedLearner.load_ml_model(self.meta.tag)
        if self.global_model is not None:
            self.loaded_from_pkl = True

    def save_online_model(self):
        if not self.model:
            return

        self.meta.save_ml_model(self.model)

    def save_offline_model(self):
        if not self.global_model:
            return

        PretrainedLearner.save_ml_model(self.meta.tag, self.global_model)

    def load_models(self):
        """ Loads the available models (offline and online) from stored pkls """
        if isinstance(self.meta, OnlineLearner):
            try:
                self.load_online_model()
            except ModelNotFoundException:
                # Not an error
                pass

        self.load_offline_model()
        self.offline_vectorizer.load_model()

    def save_models(self):
        """ Store the available models (offline and online) to pkls """
        self.save_online_model()
        self.save_offline_model()
        self.offline_vectorizer.save_model()


class LearnerAttributeClassifier:
    """
    A classifier meant to augment already labeled clauses with additional info.
    This additional info can be diverse, so the output classes can vary.

    Note: at the moment it has the same classifier model and vectorizer as a
    PretrainedLearner, but this can be changed and optimized in time.
    """

    def __init__(self, db_model, flags=[]):
        self.model = None
        self.vectorizer = LearnerAttributeVectorizer(db_model.model_uuid, db_model.tag)
        self.meta = db_model
        self.flags = flags

        # Initial fitting of the vectorizer
        self.vectorizer.fit_dict(self.flags)

    def prefit(self, X_text, X_flags, y):
        """
        (Re)trains the model for the current attribute.
        X_text:  list of sentences
        X_flags: list of lists of flags
        y:       list of labels
        """
        # Init the vocabulary from the whole dataset
        self.vectorizer.fit(X_text, self.flags)

        if not self.model:
            self.model = LearnerAttribute.init_ml_model()
        X = self.vectorizer.transform(self.meta.tag, X_text, X_flags)
        self.model.fit(X, y)

    def predict(self, X_text, X_flags):
        """ Takes list of sentences, list of lists of flags, returns list of labels """
        pred = np.array([0.] * len(X_text))
        if self.model:
            X = self.vectorizer.transform(self.meta.tag, X_text, X_flags)
            pred = self.model.predict(X)
        return pred

    def load_models(self):
        """ Loads the available model from stored pkl """
        name = '%s_%s' % (self.meta.tag or self.meta.parent_learner.tag,
                          '-'.join(self.meta.name.lower().split()) if self.meta.name else 'default')
        self.model = self.meta.load_ml_model(name)
        self.vectorizer.load_model(name)

    def save_models(self):
        if not self.model:
            return
        name = '%s_%s' % (self.meta.tag or self.meta.parent_learner.tag,
                          '-'.join(self.meta.name.lower().split()) if self.meta.name else 'default')
        self.meta.save_ml_model(name, self.model)
        self.vectorizer.save_model(name)


class AgreementTypeClassifier:
    """
    Determines the type of the agreement.

    TODO:
    As a start, it's trained to tell between an NDA and anything else.
    """

    def __init__(self):
        self.ready = False

    def initialize(self):
        if not self.ready:
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
            self.model = LogisticRegression(C=1e5)

            self.load_model()
            self.load_vectorizer()

            self.ready = True

    def fit(self, X_text, y):
        # Lazy initialization
        self.initialize()

        # Init the vocabulary from the whole dataset
        X = self.vectorizer.fit_transform(X_text)

        self.vectorizer.transform(X_text)
        self.model.fit(X, y)

    def predict(self, text):
        # Lazy initialization
        self.initialize()

        single_sample = not isinstance(text, (list, tuple))
        if single_sample:
            text = [text]
        X = self.vectorizer.transform(text)
        y_pred = self.model.predict(X)
        return y_pred if not single_sample else y_pred[0]

    def predict_proba(self, text):
        # Lazy initialization
        self.initialize()

        single_sample = not isinstance(text, (list, tuple))
        if single_sample:
            text = [text]
        X = self.vectorizer.transform(text)
        y_proba = self.model.predict_proba(X)
        return y_proba if not single_sample else y_proba[0]

    def load_model(self):
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'agreement_type', 'model.pkl')
        logging.info('Loading AgreementType model from path: %s' % model_path)
        if os.path.exists(model_path):
            with open(model_path, 'rb') as model_in:
                self.model.coef_, self.model.intercept_, self.model.classes_ = pkl.load(model_in)
        else:
            logging.error('Could not load the model from %s because file does not exist' % model_path)

    def load_vectorizer(self):
        vec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'agreement_type', 'vectorizer.pkl')
        logging.info('Loading AgreementType vectorizer from path: %s' % vec_path)
        if os.path.exists(vec_path):
            with open(vec_path, 'rb') as vec_in:
                self.vectorizer = pkl.load(vec_in)
        else:
            logging.error('Could not load the vec from %s because file does not exist' % vec_path)


# Instantiate singleton
AGREEMENT_TYPE_CLASSIFIER = AgreementTypeClassifier()
