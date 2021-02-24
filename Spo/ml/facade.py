import logging

from django.db.models import Q

from experiment.models import Experiment
from ml.clfs import TagLearner, LearnerAttributeClassifier
from ml.models import OnlineLearner, OnlineDataset, PretrainedLearner


class LearnerFacade:

    def __init__(self, db_model, ml_model):
        self.db_model = db_model
        self.ml_model = ml_model

    @staticmethod
    def _retrain_generic(db_model, ml_model):
        ml_model.reset(
            initial_samples=zip(
                db_model.samples['text'],
                db_model.samples['flags'],
                db_model.samples['label'],
            )
        )

    def _retrain(self):
        self._retrain_generic(self.db_model, self.ml_model)

    @classmethod
    def get_or_create(cls, tag, user=None, include_deleted=False, preload=True, **kwargs):
        """
        Takes care of preparing the component for a specific (tag, user) pair.
        If no user is provided, will try to load a global pretrained model.
        Otherwise, an online model is instantiated. Either a fresh one, or an
        existing one loaded from the DB.
        If the `preload` flag is disabled, the corresponding ML model won't get loaded.
        If no model is found for the given tag, then the `defaults` dict is used
        for properly initializing a brand new model (i.e. not from scratch).
        """

        if user:
            db_model = OnlineLearner.objects.filter(tag=tag, owner=user).last()

            initial_train = False

            if db_model:
                logging.info('OnlineLearner object found for tag=%s, user=%s', tag, user)

                if not include_deleted and db_model.deleted:
                    # Recycle this model (will lose all old data)
                    db_model.reset()
                    db_model.deleted = False
                    db_model.save()

            else:
                # Check if pretrained exists and is not exclusive
                pretrained = False
                pt_model = PretrainedLearner.objects.filter(tag=tag).last()
                if pt_model and (not pt_model.exclusivity or pt_model.exclusivity == user.username):
                    pretrained = True

                experiment = kwargs.get('experiment')
                if not experiment:
                    experiment = Experiment.objects.create(name=tag, owner=user, public=False)

                db_model = OnlineLearner(tag=tag, owner=user, pretrained=pretrained, experiment=experiment)

                defaults = kwargs.get('defaults') or {}
                if 'active' in defaults:
                    db_model.active = defaults['active']
                if 'deleted' in defaults:
                    db_model.deleted = defaults['deleted']
                if 'samples' in defaults:
                    dataset = OnlineDataset.objects.create()
                    dataset.add_sample_batch(defaults['samples'])
                    db_model.dataset = dataset

                db_model.save()

                logging.info('OnlineLearner object created for tag=%s, user=%s', tag, user)

                # If the model was initialized with some non-empty dataset, then make sure to train it
                initial_train = db_model.total_set_size > 0

            ml_model = TagLearner(db_model)

            if initial_train:
                cls._retrain_generic(db_model, ml_model)

                ml_model.save_online_model()

        else:
            db_model, created = PretrainedLearner.objects.get_or_create(tag=tag)

            if created:
                logging.info('PretrainedLearner object created for tag=%s', tag)
            else:
                logging.info('PretrainedLearner object found for tag=%s', tag)

            offline_model_type = kwargs.get('offline_model_type')
            if offline_model_type and offline_model_type != db_model.model_type:
                db_model.model_type = offline_model_type
                db_model.save()

            offline_decision_threshold = kwargs.get('offline_decision_threshold')

            kwargs = {'offline_model_type': offline_model_type,
                      'offline_decision_threshold': offline_decision_threshold}

            ml_model = TagLearner(db_model, **kwargs)

        if preload:
            ml_model.load_models()

        return cls(db_model, ml_model)

    @classmethod
    def get_all(cls, user=None, active_only=False, mature_only=False, include_deleted=False, preload=True):
        """
        Returns all the classifiers available for one user, generating
        LearnerFacade objects.
        If the `preload` flag is disabled, the corresponding ML models won't get loaded.
        """

        if user:
            qs = OnlineLearner.objects.filter(
                Q(owner=user) & (Q(experiment=None) | Q(experiment__public=False))
            ).select_related(
                'owner', 'experiment'
            ).order_by('tag')

            if not include_deleted:
                qs = qs.filter(deleted=False)
            if active_only:
                qs = qs.filter(active=True)

            for db_model in qs:
                # Sometimes we like to be among mature ones
                if mature_only and not db_model.is_mature:
                    continue
                ml_model = TagLearner(db_model)
                if preload:
                    ml_model.load_models()
                yield cls(db_model, ml_model)

        else:
            for db_model in PretrainedLearner.objects.order_by('tag'):
                tag = db_model.tag
                if tag.startswith('trained#') or tag.startswith('builtin#'):
                    continue
                ml_model = TagLearner(db_model)
                if preload:
                    ml_model.load_models()
                yield cls(db_model, ml_model)

    def _fix_conflicts(self, texts, labels):
        """ Checks for conflicts and resolves them. """

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
                        # It's a duplicate sample, should be ok to retrain on it
                        pass
                except ValueError:
                    # This is not an error, it's actually a good thing: no conflict
                    pass

        if should_retrain:
            # Now that the dataset is consistent again, retrain
            self._retrain()

    def _find_duplicates(self, texts):
        return [
            duplicate_idx for duplicate_idx, txt in enumerate(texts)
            if txt in self.db_model.samples['text']
        ] if self.db_model.samples else []

    @staticmethod
    def _filter_list(obj_list, skip_idx_list):
        return [obj for idx, obj in enumerate(obj_list) if idx not in skip_idx_list]

    def _fit_samples(self, texts, flags, labels, infered=False):
        for txt, flgs, lbl in zip(texts, flags, labels):
            self.db_model.add_sample(text=txt, flags=flgs,
                                     label=lbl, infered=infered)
        self.ml_model.fit(texts, flags, labels)

    def train(self, capsules, labels, infered_negative_capsules=[]):
        """
        Takes :capsules as the annotated train samples.
        Uses :infered_negative_capsules as additional negative examples,
        which are absent in :capsules and were inferred from the same source
        based on some heuristics.
        """

        texts = [sc.text for sc in capsules]
        flags = [sc.flags for sc in capsules]

        # This guy here takes care of eventual conflicts
        self._fix_conflicts(texts, labels)
        # Train
        self._fit_samples(texts, flags, labels)

        if infered_negative_capsules:
            texts = [nsc.text for nsc in infered_negative_capsules]
            flags = [nsc.flags for nsc in infered_negative_capsules]

            # Filter out inferred negatives which turned out to be duplicates
            duplicates = self._find_duplicates(texts)
            if duplicates:
                texts = self._filter_list(texts, duplicates)
                flags = self._filter_list(flags, duplicates)

            if texts:
                self._fit_samples(texts, flags, [False] * len(texts), infered=True)

        self.db_model.save()
        self.ml_model.save_online_model()

    def get_pretrained_component(self):
        return PretrainedLearner.objects.filter(tag=self.db_model.tag).last()

    def predict(self, capsules, include_attributes=False):
        """
        Takes a list of ml.capsules.Capsule objects and predicts labels.
        Returns a numpy array of boolean predictions.
        If :include_attributes is true, each LearnerAttribute assigned to the
        current Learner is run over the data and the return format changes to a
        list of dicts. E.g.:
            [
                {
                    'label': True,
                    'attrs': [
                        {
                            'name': 'party-assignment',
                            'label': 'Y'
                        },
                        {
                            'name': 'waiver',
                            'label': False
                        },
                        ...
                    ]
                },
                ...
            ]
        """

        texts = [sc.text for sc in capsules]
        flags = [sc.flags for sc in capsules]

        predictions = self.ml_model.predict(texts, flags)

        if include_attributes:
            pretrained_component = self.get_pretrained_component()

            if pretrained_component:
                attr_names = []
                attr_predictions = []

                for attr in pretrained_component.learner_attribute.order_by('name'):
                    attr_clf = LearnerAttributeClassifier(attr)
                    attr_clf.load_models()

                    attr_names.append(attr.name or 'default')
                    attr_predictions.append(attr_clf.predict(texts, flags))

                return [
                    {
                        'label': bool(label),
                        'attrs': [
                            {
                                'name': attr_name,
                                'label': attr_labels[idx]
                            }
                            for attr_name, attr_labels in zip(attr_names, attr_predictions)
                        ]
                    }
                    for idx, label in enumerate(predictions)
                ]

        return predictions

    def remove_sample(self, capsule):
        """
        Makes a sample negative and retrains the model.
        Does not actually remove anything.
        Assumes that the sample is positive, has no effect otherwise.
        """

        text = capsule.text

        should_retrain = False

        for idx, (txt, lbl) in enumerate(zip(self.db_model.samples['text'],
                                             self.db_model.samples['label'])):
            if txt == text and lbl:
                self.db_model.samples['label'][idx] = False
                should_retrain = True

        if should_retrain:
            self._retrain()

            self.db_model.save()
            self.ml_model.save_online_model()

    @property
    def is_mature(self):
        return self.db_model.is_mature

    def __unicode__(self):
        return unicode(self.db_model)

    def __eq__(self, other):
        return self.db_model == other.db_model
