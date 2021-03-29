import logging
import numpy as np

from ml.clfs import TagLearner, LearnerAttributeClassifier
from ml.utils import party_pattern
from ml.models import OnlineLearner, PretrainedLearner
from ml.capsules import Capsule
from ml.exceptions import ModelNotFoundException


LEARNER_MATURITY_THREASHOLD = 12


class LearnerFacade:

    def __init__(self, db_model, ml_model):
        self.db_model = db_model
        self.ml_model = ml_model

    @classmethod
    def get_or_create(cls, tag, user=None, include_deleted=False, preload=True):
        """
        Takes care of preparing the component for a specific (tag, user) pair.

        If no user is provided, will try to load a global pretrained model.

        Otherwise, an online model is instantiated. Either a fresh one, or an
        existing one loaded from DB/memory
        """
        db_model = None
        ml_model = None
        if user:
            if OnlineLearner.objects.filter(tag=tag, owner=user).exists():
                logging.info('OnlineLearner object found for tag=%s' % tag)

                # Could probably be optimized to only one query
                db_model = OnlineLearner.objects.get(tag=tag, owner=user)

                if not include_deleted and db_model.deleted:
                    # Recycle this model (will lose all old data)
                    db_model.reset()
                    db_model.deleted = False
                    db_model.save()

            else:
                # Check if pretrained exists and is not exclusive
                pretrained_flag = False
                if PretrainedLearner.objects.filter(tag=tag).exists():
                    pt_model = PretrainedLearner.objects.get(tag=tag)
                    if not pt_model.exclusivity or pt_model.exclusivity == user.username:
                        pretrained_flag = True
                db_model = OnlineLearner(tag=tag, owner=user, pretrained=pretrained_flag)
                db_model.save()
                logging.info('OnlineLearner object created for tag=%s' % tag)

            ml_model = TagLearner(db_model)
            logging.info('The TagLearner model has been initialized')

            if preload:
                try:
                    ml_model.load_models()
                except ModelNotFoundException:
                    # Nothing to be loaded, just skip this step
                    logging.warning('ModelNotFoundException in LearnerFacade.get_or_create')

        else:
            if PretrainedLearner.objects.filter(tag=tag).exists():
                logging.info('PretrainedLearner object found for tag=%s' % tag)
                # Could probably be optimized to only one query
                db_model = PretrainedLearner.objects.get(tag=tag)
            else:
                db_model = PretrainedLearner(tag=tag)
                db_model.save()
                logging.info('PretrainedLearner object created for tag=%s' % tag)

            ml_model = TagLearner(db_model)
            if preload:
                try:
                    ml_model.load_models()
                except ModelNotFoundException:
                    logging.warning('ModelNotFoundException: Could not load models for TagLearner model=%s' % ml_model)

        return cls(db_model, ml_model)

    @classmethod
    def get_all(cls, user=None, active_only=False, mature_only=False, include_deleted=False, preload=True):
        """
        Returns all the classifiers available for one user, generating
        LearnerFacade objects.
        If `preload` is false, the ML models won't get loaded.
        """
        if user:
            q = OnlineLearner.objects.filter(owner=user).order_by('tag')

            if not include_deleted:
                q = q.filter(deleted=False)
            if active_only:
                q = q.filter(active=True)

            for db_model in q:
                # Sometimes we like to be among mature ones
                if mature_only and not db_model.is_mature():
                    continue
                ml_model = TagLearner(db_model)
                if preload:
                    try:
                        ml_model.load_models()
                    except ModelNotFoundException:
                        continue
                yield cls(db_model, ml_model)
        else:
            for db_model in PretrainedLearner.objects.all():
                ml_model = TagLearner(db_model)
                if preload:
                    ml_model.load_models()
                yield cls(db_model, ml_model)

    def get_pretrained_component(self):
        return PretrainedLearner.objects.filter(tag=self.db_model.tag).last()

    @staticmethod
    def _features_to_proba(feats):
        """
        Estimates a probability for one clause (represented by the features
        dict :feats) to represent a negative example for the current tag
        classification.
        """
        proba = 1.
        # Assume that a contract is read top-down
        # Ergo, clauses above the current one are more probable to have been read
        if not feats['above']:
            proba *= 0.5
        # Clauses with tags were probably read
        # Since the current tag was not added, it's probably a negative sample
        if not feats['tags']:
            proba *= 0.5
        # Avoid very short clauses. May not provide much info
        if len(feats['text']) < 10:
            proba *= len(feats['text']) / 10.

        return proba

    def _fix_conflicts(self, texts, labels):
        """ Check for conflicts and resolve them """
        should_retrain = False
        if self.db_model.samples:
            for txt, lbl in zip(texts, labels):
                try:
                    conflict_idx = self.db_model.samples['text'].index(txt)
                    if self.db_model.samples['label'][conflict_idx] != lbl:
                        # Na belea! Conflict.
                        self.db_model.discard_sample_by_idx(conflict_idx)
                        should_retrain = True
                    else:
                        # It's a duplicate positive sample, should be ok to retrain on it
                        pass
                except ValueError:
                    # This is not an error, it's actually a good thing: no conflict
                    pass
        if should_retrain:
            # Now that the dataset is consistent again, retrain
            self.ml_model.reset(initial_samples=zip(
                self.db_model.samples['text'],
                self.db_model.samples['flags'],
                self.db_model.samples['label'],
            ))

    def _fit_samples(self, texts, flags, labels, infered=False):
        for txt, flg, lbl in zip(texts, flags, labels):
            self.db_model.add_sample(text=txt, flags=flg,
                                     label=lbl, infered=infered)
        self.ml_model.fit(texts, flags, labels)

        self.db_model.save()
        self.ml_model.save_online_model()

    @classmethod
    def _infer_negatives_generic(cls, tag, samples, capsules, labels, all_capsules):
        N_NEGATIVES = 2

        # Compute the number of candidates needed
        npositives = sum(labels)
        nnegatives = len(labels) - npositives
        ncands = npositives * N_NEGATIVES - nnegatives
        if ncands <= 0:
            return
        # Gather candidates for the negative samples
        caps_idx = [sc.idx for sc in capsules]
        candidates = []
        above = True
        first_capsule = capsules[np.argmin(caps_idx)]
        # We assume, that all sentences are from the same document,
        # so the parties should be the same
        ps = first_capsule.parties
        for i, (c, tags) in enumerate(all_capsules):
            sc = Capsule(c.text, idx=i, parties=ps)
            text = sc.preprocess()
            flags = sc.flags

            # Are we still above the first sample?
            if i == first_capsule.idx:
                above = False
            # Skip the positives
            if i in caps_idx:
                continue
            # Skip the empty sentences
            if not text.strip():
                continue
            # Skip the already validated as positive
            if tag in tags:
                continue
            # Look up the sentence in the samples dataset to avoid duplicates
            if text in samples:
                continue

            candidates.append({
                'text': text,
                'flags': flags,
                'above': above,  # Assume clauses above were more probably read
                'tags': tags,  # Assume clauses with tags were more probably read
            })

        if candidates:
            # Randomly sample based on computed probabilities
            candidate_probas = list(map(cls._features_to_proba, candidates))
            proba_sum = sum(candidate_probas)
            norm_probas = [p / (float(proba_sum) or 0.0001) for p in candidate_probas]
            chosen = np.random.choice(candidates,
                                      min(ncands, len(candidates)),
                                      p=norm_probas, replace=False)

            return [Capsule(text=neg['text'], flags=neg['flags']) for neg in chosen]

    @classmethod
    def infer_negatives_global(cls, tag, capsules, labels, all_capsules):
        # Don't care about duplicates in this version of the method
        return cls._infer_negatives_generic(tag, [],
                                            capsules, labels, all_capsules)

    def infer_negatives(self, capsules, labels, all_capsules):
        return self._infer_negatives_generic(self.db_model.tag, self.db_model.samples['text'],
                                             capsules, labels, all_capsules)

    def train(self, capsules, labels, infer_negatives=False, all_capsules=[]):
        """
        Takes :capsules as the annotated train samples and, from its
        containing document, infers some negative examples based on heuristics.

        If infer_negatives=True, then :all_capsules from the appropriate
        document are used for inferring additional negative examples absent
        in :capsules, and also indices (:idx) are expected inside :capsules
        (the current heuristics make use of them for proper selection).
        The following format of :all_capsules is expected:
            [(Capsule(text, ...), [tags]), ...],
        where :tags is a list of tags already added to a corresponding sample.
        """

        # Mask the party names for better generalization
        pmasked_texts = [sc.preprocess() for sc in capsules]
        flags_list = [sc.flags for sc in capsules]

        # This guy here takes care of eventual conflicts
        self._fix_conflicts(pmasked_texts, labels)
        # Train
        self._fit_samples(pmasked_texts, flags_list, labels)

        if infer_negatives:
            neg_capsules = self.infer_negatives(capsules, labels, all_capsules)

            if neg_capsules:
                # Texts were already preprocessed
                texts = [nsc.text for nsc in neg_capsules]
                flags = [nsc.flags for nsc in neg_capsules]
                self._fit_samples(texts, flags, [False] * len(texts), infered=True)

    def predict(self, capsules, include_attributes=False):
        """
        Takes a list of ml.capsules.Capsule objects and predicts labels.

        Returns a numpy array of predictions (True/False).
        If :include_attributes is true, each LearnerAttribute assigned to the
        current Learner is run over the data and the return format changes to a
        list of dicts. E.g.:
            [
                {'label': True,
                 'attrs': [
                    {
                        'name': 'party-assignment',
                        'label': 'Y'
                    },
                    {
                        'name': 'waiver',
                        'label': False
                    },
                 ]
                }
            ]
        """
        logging.info('Preprocessing %s sentences' % len(capsules))
        if capsules:
            # Generate the party mask regexs only once
            parties = capsules[0].parties
            if parties:
                yparty = parties['you']
                tparty = parties['them']
                you_party = party_pattern(yparty)
                them_party = party_pattern(tparty)

                pmasked_text = [sc.preprocess(you_party=you_party, them_party=them_party) for sc in capsules]
            else:
                pmasked_text = [sc.text for sc in capsules]
            flags = [sc.flags for sc in capsules]
        else:
            pmasked_text = []
            flags = []

        logging.info('Preprocessed %s sentences' % len(capsules))
        logging.info('Predicting tags with model: %s - type=%s' % (self.db_model, type(self.db_model)))
        pred = self.ml_model.predict(pmasked_text, flags)
        ptcomp = self.get_pretrained_component()
        if include_attributes and ptcomp:
            attr_names = []
            attr_preds = []
            for attr in ptcomp.learner_attribute.all():
                ml_attr = LearnerAttributeClassifier(attr)
                ml_attr.load_models()
                attr_names.append(attr.name or 'default')
                attr_preds.append(ml_attr.predict(pmasked_text, flags))
            return [
                {'label': p, 'attrs': [
                    {'name': aname,
                     'label': alabels[k]}
                    for aname, alabels in zip(attr_names, attr_preds)
                 ]}
                for k, p in enumerate(pred)
            ]
        return pred

    def _remove_positive_sample_by_idx(self, sample_idx):
        """
        Turns the sample at :sample_idx to negative and retrains the model
        It assumes that the sample is positive. Otherwise it has no effect.
        (It saves the models)
        """
        if sample_idx >= len(self.db_model.samples['text']):
            raise Exception('Index of sample to remove out of bounds')

        # Don't remove, change to negative and retrain
        self.db_model.samples['label'][sample_idx] = False

        self.ml_model.reset(initial_samples=zip(
            self.db_model.samples['text'],
            self.db_model.samples['flags'],
            self.db_model.samples['label'],
        ))

        self.db_model.save()
        self.ml_model.save_online_model()

    def remove_sample(self, capsule):
        pmasked_text = capsule.preprocess()
        # Should be found. If not, skip this
        try:
            idx = self.db_model.samples['text'].index(pmasked_text)
        except:
            logging.info('Sample not removed as it didn\'t match any in the dataset.')
            return False

        # Negative samples also need to be removed to not get unbalanced
        # Sort the negatives by decision function score, remove the most confident
        scores = []
        for i, (text, flags, label) in enumerate(zip(
                                        self.db_model.samples['text'],
                                        self.db_model.samples['flags'],
                                        self.db_model.samples['label'])):
            scr = self.ml_model.decision_score([text], [flags])
            scores.append((scr, i))
        scores.sort()

        self._remove_positive_sample_by_idx(idx)

        # Rebalance a bit by removing negative samples
        # TODO: evaluate this, maybe it's not needed
        # TODO: remove only from the infered samples

        return True

    def is_mature(self):
        return self.db_model.is_mature()

    def to_dict(self):
        d = self.db_model.to_dict()
        d['is_mature'] = self.is_mature()
        d['maturity'] = d['positive_set_size'] / float(LEARNER_MATURITY_THREASHOLD or 0.00001)
        return d
