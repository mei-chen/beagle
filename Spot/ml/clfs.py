import numpy as np

from ml.models import OnlineLearner, PretrainedLearner, LearnerAttribute
from ml.vecs import TagLearnerOnlineVectorizer, TagLearnerOfflineVectorizer, LearnerAttributeVectorizer


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

    def __init__(self, db_model, flags=None, **kwargs):
        self.model = None
        self.model_type = kwargs.get('online_model_type')  # not used now (added for consistency)

        self.global_model = None
        self.global_model_type = kwargs.get('offline_model_type')

        self.online_decision_threshold = kwargs.get('online_decision_threshold')  # not used now (added for consistency)
        self.offline_decision_threshold = kwargs.get('offline_decision_threshold')

        self.online_vectorizer = TagLearnerOnlineVectorizer(db_model.uuid, db_model.tag)
        self.offline_vectorizer = TagLearnerOfflineVectorizer(db_model.uuid, db_model.tag)

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
            self.global_model = PretrainedLearner.init_ml_model(self.global_model_type)
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
        self.model.partial_fit(X, y)

    def predict(self, X_text, X_flags):
        """
        Takes list of sentences, list of lists of flags.
        Returns list of boolean labels.
        """

        if self.global_model:
            X_offline = self.offline_vectorizer.transform(self.meta.tag, X_text, X_flags)
            if not self.model:
                return self.global_model.predict(X_offline, self.offline_decision_threshold)

        if self.model:
            X_online = self.online_vectorizer.transform(self.meta.tag, X_text, X_flags)
            if not self.global_model:
                return self.model.predict(X_online)

        # Assume that confidence scores are some probabilities
        scores_offline = self.global_model.predict_proba(X_offline)
        scores_online = self.model.predict_proba(X_online)

        # Combine offline and online scores
        scores_final = 0.6 * scores_offline + 0.4 * scores_online
        return scores_final > 0.5

    def decision_function(self, X_text, X_flags):
        """
        Takes list of sentences, list of lists of flags.
        Returns list of real numbers.
        """

        scores = []
        weights = []

        if self.global_model:
            X_offline = self.offline_vectorizer.transform(self.meta.tag, X_text, X_flags)
            scores_offline = self.global_model.decision_function(X_offline)

            scores.append(scores_offline)
            weights.append(0.6)

        if self.model:
            X_online = self.online_vectorizer.transform(self.meta.tag, X_text, X_flags)
            scores_online = self.model.decision_function(X_online)

            scores.append(scores_online)
            weights.append(0.4)

        return np.average(np.vstack(scores), axis=0, weights=weights)

    def load_online_model(self):
        if isinstance(self.meta, OnlineLearner):
            self.model = self.meta.load_ml_model()
        if self.model:
            self.loaded_from_pkl = True

    def load_offline_model(self):
        self.global_model = PretrainedLearner.load_ml_model(self.meta.tag)
        if self.global_model:
            self.loaded_from_pkl = True

    def save_online_model(self):
        if self.model:
            self.meta.save_ml_model(self.model)

    def save_offline_model(self):
        if self.global_model:
            PretrainedLearner.save_ml_model(self.meta.tag, self.global_model)

    def load_models(self):
        """ Loads the available models (offline and online) from stored pkls """
        self.load_online_model()
        if PretrainedLearner.objects.filter(tag=self.meta.tag).exists():
            self.load_offline_model()
            self.offline_vectorizer.load_model()

    def save_models(self):
        """ Stores the available models (offline and online) to pkls """
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
        self.vectorizer = LearnerAttributeVectorizer(db_model.uuid, db_model.tag)
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
        """
        Takes list of sentences, list of lists of flags.
        Returns list of labels.
        """
        if self.model:
            X = self.vectorizer.transform(self.meta.tag, X_text, X_flags)
            return self.model.predict(X)
        # Return some dummy predictions in the case of an absent model
        return np.array([None] * len(X_text))

    def _build_full_name(self):
        return '%s_%s' % (self.meta.tag or self.meta.parent_learner.tag,
                          '-'.join((self.meta.name or 'default').split()))

    def load_models(self):
        """ Loads the available model from stored pkl """
        name = self._build_full_name()
        self.model = self.meta.load_ml_model(name)
        self.vectorizer.load_model(name)

    def save_models(self):
        """ Stores the available model to pkl """
        if not self.model:
            return
        name = self._build_full_name()
        self.meta.save_ml_model(name, self.model)
        self.vectorizer.save_model(name)
