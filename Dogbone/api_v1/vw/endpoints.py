import re
import json
import langdetect
import numpy as np
from copy import deepcopy
from unidecode import unidecode

from beagle_simpleapi.mixin import PutDetailModelMixin
from beagle_simpleapi.endpoint import ActionView, ListView, DetailView
from ml.models import OnlineLearner, PretrainedLearner
from ml.facade import LearnerFacade, LEARNER_MATURITY_THREASHOLD
from ml.capsules import Capsule
from clauses_statistics.models import ClausesStatistic

from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import f1_score, precision_score, recall_score


# -- Utility stuff --

number_re = re.compile(r'\b([0-9]+[,./-]?)+k?\b')

def process(s):
    text = unidecode(s.strip())
    text = number_re.sub(' __NUM_MASK__ ', text)
    return text


# -- API endpoints --

class VWLearnersListView(ListView):
    model = PretrainedLearner
    url_pattern = r'vw/learners$'
    endpoint_name = 'vw_learners_list_view'

    def has_access(self, instance):
        return (self.user.username == 'vw' or self.user.is_superuser)

    def get_list(self, request, *args, **kwargs):
        if not self.has_access(None):
            raise self.UnauthorizedException("You don't have access to this resource")
        learners = PretrainedLearner.objects.filter(exclusivity='vw')
        return learners


class VWLearnerDetailView(DetailView, PutDetailModelMixin):
    model = PretrainedLearner
    url_pattern = r'vw/(?P<tag>[^/]+)/details$'
    endpoint_name = 'vw_learner_detail_view'

    model_key_name = 'tag'
    url_key_name = 'tag'

    def has_access(self, instance):
        if instance.exclusivity != 'vw':
            return False
        return (self.user.username == 'vw' or self.user.is_superuser)

    def save_model(self, model, data, request, *args, **kwargs):
        if 'description' in data and data['description']:
            model.description = data['description']

        model.save()
        return model


class VWLearnerResetView(DetailView):
    model = OnlineLearner
    url_pattern = r'vw/(?P<tag>[^/]+)/reset$'
    endpoint_name = 'vw_learner_reset_view'

    model_key_name = 'tag'
    url_key_name = 'tag'

    def get_object(self, request, *args, **kwargs):
        learner_name = self.key_getter(request, *args, **kwargs)
        if not OnlineLearner.objects.filter(tag=learner_name, owner=self.user).exists():
            return {'status': 0, 'message': "Requested classifier doesn't exist or cannot be reset (%s)" % learner_name}
        return OnlineLearner.objects.get(tag=learner_name, owner=self.user)

    def has_access(self, instance):
        return (self.user.username == 'vw' or self.user.is_superuser)

    def put(self, request, *args, **kwargs):
        """ On PUT, reset the learner """
        instance = self.get_object(request, *args, **kwargs)
        if not self.has_access(instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        instance.reset()
        instance.save()

        serialized = self.to_dict(instance)
        url = self.get_url(instance)
        if url:
            serialized['url'] = url
        return serialized

    def to_dict(self, instance):
        return {'fresh': (not instance.samples)}


class VWLearnerPredictView(ActionView):
    """
    Requests prediction for a list of 'supplier_comment' entries.
    Language is auto-detected and appended to learner name (tag_lang).
    POST request body format:
        [{'supplier_comment': 'text 1'},
         {'supplier_comment': 'text 2'}]
    """
    model = OnlineLearner
    url_pattern = r'vw/(?P<tag>[^/]+)/predict$'
    endpoint_name = 'vw_learner_predict_view'

    model_key_name = 'tag'
    url_key_name = 'tag'

    def get_object(self, request, *args, **kwargs):
        return self.key_getter(request, *args, **kwargs)

    def has_access(self, instance):
        return (self.user.username == 'vw' or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        """ Feed samples for predicting """
        data = json.loads(request.body.decode('utf-8'))
        if type(data) != list:
            data = [data]

        # Language can be enforced by using a clf name such as 0001_en
        learner_name = self.instance
        need_lang_detect = True
        lang = None
        if self.instance[-3:] in ['_en', '_de']:
            need_lang_detect = False
            lang = self.instance[-2:]

        pred_samples  = []
        for sample in data:
            if 'supplier_comment' not in sample:
                return {'status': 0, 'message': "Malformed! Please provide a 'supplier_comment'"}

            rawtext = sample['supplier_comment']
            if need_lang_detect:
                lang = langdetect.detect(rawtext)
                if lang == 'ca':
                    lang = 'en'
                if lang not in ['en', 'de']:
                    # Just default to Deutsch
                    lang = 'de'

                learner_name = '%s_%s' % (self.instance, lang)

            if not PretrainedLearner.objects.filter(tag=learner_name).exists():
                # return {'status': 0, 'message': "Requested classifier doesn't exist (%s)" % learner_name}
                # Don't kill the whole request, just mark this sample
                pred_samples.append(
                    {'predicted': "Requested classifier doesn't exist (%s)" % learner_name,
                     'confidence': None,
                     'detected_lang': lang}
                )
            else:
                fcd = LearnerFacade.get_or_create(learner_name, self.user)

                text = process(rawtext)
                cnf = fcd.ml_model.decision_score([text], [[]])[0]
                pred_samples.append(
                    {'predicted': int(cnf > 0.),
                     'confidence': min(1., abs(cnf) / 10.) * 100,
                     'detected_lang': lang})

        return {'status': 1, 'answer': pred_samples}


class VWLearnerTrainView(ActionView):
    """
    Trains the online classifier sample by sample on POST request.
    Language is auto-detected and appended to learner name (tag_lang).
    Request body format:
        [{'supplier_comment': 'text 3', 'label': True},
         {'supplier_comment': 'text 2', 'label': False}]
    (where label is true if the tag applies to the supplier_comment)
    """
    model = OnlineLearner
    url_pattern = r'vw/(?P<tag>[^/]+)/train$'
    endpoint_name = 'vw_learner_train_view'

    model_key_name = 'tag'
    url_key_name = 'tag'

    def get_object(self, request, *args, **kwargs):
        return self.key_getter(request, *args, **kwargs)

    def has_access(self, instance):
        return (self.user.username == 'vw' or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        """ Feed sample for training """
        data = json.loads(request.body.decode('utf-8'))
        if type(data) != list:
            data = [data]

        # Language can be enforced by using a clf name such as 0001_en
        learner_name = self.instance
        need_lang_detect = True
        lang = None
        if self.instance[-3:] in ['_en', '_de']:
            need_lang_detect = False
            lang = self.instance[-2:]

        langs = []
        maturity = {}
        for sample in data:
            if 'supplier_comment' not in sample:
                return {'status': 0, 'message': "Malformed! Please provide a 'supplier_comment'"}
            if 'label' not in sample:
                return {'status': 0, 'message': "Please provide a 'label'"}

            rawtext = sample['supplier_comment']
            if need_lang_detect:
                lang = langdetect.detect(rawtext)
                if lang == 'ca':
                    lang = 'en'
                if lang not in ['en', 'de']:
                    # Just default to Deutsch
                    lang = 'de'

                learner_name = '%s_%s' % (self.instance, lang)

            if not PretrainedLearner.objects.filter(tag=learner_name).exists():
                return {'status': 0, 'message': "Requested classifier doesn't exist (%s)" % learner_name}

            fcd = LearnerFacade.get_or_create(learner_name, self.user)
            fcd.train([Capsule(rawtext)], [sample['label']])
            maturity[learner_name] = fcd.db_model.positive_set_size >= LEARNER_MATURITY_THREASHOLD
            langs.append(lang)

        return {'status': 1, 'message': 'OK', 'detected_lang': langs, 'clfs_maturity': maturity}


class VWLearnerInitView(ActionView):
    """
    Pre-trains the classifier from an initial dataset on POST request.
    Language is not auto-detected, it's specified in the url and appended to
    learner name (tag_lang).
    Request body format:
        [{'supplier_comment': 'text 3', 'label': True},
         {'supplier_comment': 'text 2', 'label': False}]
    (where label is true if the tag applies to the supplier_comment)
    """
    model = OnlineLearner
    url_pattern = r'vw/(?P<tag>[^/]+)/(?P<lang>[^/]+)/init$'
    endpoint_name = 'vw_learner_init_view'

    model_key_name = 'tag'
    url_key_name = 'tag'

    def get_object(self, request, *args, **kwargs):
        return self.key_getter(request, *args, **kwargs)

    def has_access(self, instance):
        return (self.user.username == 'vw' or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        """ Feed data for pre-training and init the Learner """
        data = json.loads(request.body.decode('utf-8'))
        if type(data) != list:
            data = [data]

        tag = self.instance
        lang = kwargs['lang']
        learner_name = '%s_%s' % (tag, lang)

        if PretrainedLearner.objects.filter(tag=learner_name).exists():
            return {'status': 0, 'message': "Requested classifier already exists (%s)" % learner_name}

        clf = LearnerFacade.get_or_create(learner_name)

        # --- Train ---
        X_text  = [d['supplier_comment'] for d in data]
        y       = [d['label'] for d in data]

        spl = StratifiedShuffleSplit(n_splits=10, test_size=0.4, random_state=42)

        candidates = []
        scores = []
        # Providing y is sufficient for generating the splits,
        # but API requires some X with n_samples rows
        X_dummy = np.zeros(len(y))
        for train_index, test_index in spl.split(X_dummy, y):
            print('Split: %d, %d' % (len(train_index), len(test_index)))
            train_text = [X_text[i] for i in train_index]
            train_y = [y[i] for i in train_index]

            clf_candidate = deepcopy(clf)
            clf_candidate.ml_model.prefit(train_text, [[]] * len(train_y), train_y)

            # --- Evaluate ---
            texts = [Capsule(data[k]['supplier_comment']) for k in test_index]
            gold = [data[k]['label'] for k in test_index]
            pred = clf_candidate.predict(texts)

            f1score = f1_score(gold, pred)
            print('Precision:', precision_score(gold, pred))
            print('Recall:   ', recall_score(gold, pred))
            print('F1 score: ', f1score)
            print()

            candidates.append(clf_candidate)
            scores.append(f1score)

        i = np.argmax(scores)
        clf = candidates[i]
        print
        print('-' * 80)
        print('Picked the model [%s] with Fscore:' % learner_name, scores[i])
        print()

        print('Saving the ML model and the ML vectorizer')
        clf.ml_model.save_models()
        print('Saving the DB model')
        clf.db_model.exclusivity = 'vw'
        clf.db_model.save()

        # Redo the ClausesStatistic whether or not it already exists
        cstat = ClausesStatistic.objects.get_or_create(tag=learner_name)[0]
        cstat.set_avgwordcount([d['supplier_comment'] for d in data if d['label']])
        print('ClausesStatistic regenerated for [%s]: %d' % (learner_name, cstat.avg_word_count))

        return {'status': 1, 'message': 'OK', 'f-score': scores[i]}
