import logging
from scipy import sparse as sp

from ml.models import PretrainedLearner, LearnerAttribute
from nlplib.utils import number_re, fillin_underscore_re

from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer, CountVectorizer
from sklearn.feature_extraction import DictVectorizer


class TagLearnerVectorizer:
    """
    Base class for vectorizers.
    Not usable on it's own, use one of the versions that inherit it.
    """

    def __init__(self, uuid, tag, sparse_featurevector_size=None):
        self.uuid = uuid
        self.flags = None
        self.tag = tag

        self.sparsevec = self._new_sparse_vectorizer(sparse_featurevector_size)
        self.dictvec = DictVectorizer()

    def _new_sparse_vectorizer(self, sparse_featurevector_size=None):
        raise NotImplementedError()

    def fit_dict(self, flags=None):
        if flags is None:
            flags = []

        # Add length flag
        self.flags = flags + ['__SHORT__']  # + ['NE_PRESENT']
        allflags = {fl: True for fl in self.flags}
        self.dictvec.fit([allflags])

    def transform(self, tag, text, flags):
        # Also accept only one sample
        if type(text) != list:
            text = [text]
            flags = [flags]

        feats = []
        for i, sample_flgs in enumerate(flags):
            currft = {fl: True for fl in sample_flgs}
            currft['__SHORT__'] = len(text[i].split()) < 10
            feats.append(currft)
        # # Add whether a NamedEntity is present as a feature
        # for i, ft in enumerate(feats):
            # ne_present = False
            # from ml.gazetteer import LOC_REs
            # for loc_re in LOC_REs:
            #     if loc_re.search(text[i]):
            #         ne_present = True
            #         # print '  ---  [%s]' % str(loc_re.search(text[i]).groups())
            #         # print text[i]
            #         break
            # ft['NE_PRESENT'] = ne_present

        # Mask numbers for better generalization
        nm_text = []
        for tx in text:
            cln_tx = number_re.sub(' __NUM_MASK__ ', fillin_underscore_re.sub(' _ ', tx))
            nm_text.append(cln_tx)

        # Vectorize
        sparse = self.sparsevec.transform(nm_text)
        dense = self.dictvec.transform(feats)

        if self.flags:
            data = sp.hstack((sparse, dense))
        else:
            data = sparse
        return data


class TagLearnerOnlineVectorizer(TagLearnerVectorizer):
    """
    Designated for online training.
    Uses a small number of sparse features to get decent result quicker.
    Uses a hashing vectorizer so that the vocabulary doesn't have to be known
    in advance.

    It doesn't need to persist it's state.
    """

    # The number of features in the hashing vectorizer (for n-grams)
    SPARSE_FEATS_SIZE = 10000

    def _new_sparse_vectorizer(self, sparse_featurevector_size=None):
        return HashingVectorizer(n_features=sparse_featurevector_size or self.SPARSE_FEATS_SIZE,
                                 ngram_range=(1, 2),
                                 stop_words='english')

    def fit(self, flags=None):
        self.fit_dict(flags)


class TagLearnerOfflineVectorizer(TagLearnerVectorizer):
    """
    Designated for offline training.
    As the training dataset is provided in advance, a vocabulary and IDF scores
    can be compiled. Thus the vectorizer takes advantage of TF-IDF scoring.
    Also, a larger set of sparse features is used for better generalization.

    The fitted vectorizer has to be stored on disk for later use.
    """

    # The number of features in the hashing vectorizer (for n-grams)
    SPARSE_FEATS_SIZE = 30000

    def _new_sparse_vectorizer(self, sparse_featurevector_size=None):
        return HashingVectorizer(n_features=sparse_featurevector_size or self.SPARSE_FEATS_SIZE,
                                 ngram_range=(1, 2),
                                 stop_words='english')

    def fit(self, text_samples, flags=None):
        if flags or (not self.dictvec or not hasattr(self.dictvec, 'feature_names_') or not self.dictvec.feature_names_):
            self.fit_dict(flags)
        self.sparsevec.fit(text_samples)

    def load_model(self):
        loaded = PretrainedLearner.load_ml_vectorizer(self.tag)
        if loaded:
            self.sparsevec = loaded

    def save_model(self):
        if not self.sparsevec:
            logging.info('The TagLearnerOfflineVectorizer(%s / %s) has no vectorizer model to save' % (self.tag, self.uuid))
            return
        PretrainedLearner.save_ml_vectorizer(self.tag, self.sparsevec)


class LearnerAttributeVectorizer(TagLearnerOfflineVectorizer):

    def load_model(self, attr_name=None):
        loaded = LearnerAttribute.load_ml_vectorizer(attr_name or self.tag)
        if loaded:
            self.sparsevec = loaded

    def save_model(self, attr_name=None):
        if not self.sparsevec:
            logging.info('The LearnerAttributeVectorizer(%s / %s) has no vectorizer model to save' % (self.tag, self.uuid))
            return
        LearnerAttribute.save_ml_vectorizer(attr_name or self.tag,
                                            self.sparsevec)
