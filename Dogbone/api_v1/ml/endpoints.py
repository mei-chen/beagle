import json
import logging
import re
import urllib

from beagle_simpleapi.endpoint import DetailView, ActionView
from beagle_simpleapi.mixin import DeleteDetailModelMixin, PutDetailModelMixin
from ml.models import OnlineLearner
from ml.facade import LearnerFacade
from ml.capsules import Capsule

color_code_re = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')


class IncorrectColorCode(Exception):
    pass


class OnlineLearnerViewMixin(object):

    model = OnlineLearner

    model_key_name = 'tag'
    url_key_name = 'tag'

    @classmethod
    def key_getter(cls, request, *args, **kwargs):
        return urllib.parse.unquote(kwargs[cls.url_key_name])

    def get_object(self, request, *args, **kwargs):
        return self.model.objects.get(**{
            self.model_key_name: self.key_getter(request, *args, **kwargs),
            'owner': self.user
        })

    def has_access(self, instance):
        return instance.owner == self.user or self.user.is_superuser


class OnlineLearnerDetailView(OnlineLearnerViewMixin,
                              DetailView,
                              DeleteDetailModelMixin,
                              PutDetailModelMixin):

    # NOTE: this least specific greedy pattern must be added only
    # after all more specific (r'ml/(?P<tag>.+)/action$') ones!
    url_pattern = r'ml/(?P<tag>.+)$'
    endpoint_name = 'online_learner_detail_view'

    def delete_model(self, model, request, *args, **kwargs):
        model.deleted = True
        model.save()
        return model

    def put(self, request, *args, **kwargs):
        color_code = json.loads(request.body).get('color_code')
        if color_code and color_code_re.match(str(color_code)):
            return super(OnlineLearnerDetailView, self).put(request, *args, **kwargs)
        else:
            raise IncorrectColorCode('Incorrect color code provided: %s' % color_code)


class OnlineLearnerSamplesDetailView(OnlineLearnerViewMixin,
                                     DetailView):

    url_pattern = r'ml/(?P<tag>.+)/samples$'
    endpoint_name = 'online_learner_samples_detail_view'

    def to_dict(self, instance):
        return {'samples': list(zip(instance.samples['text'], instance.samples['label'])) if instance.samples else []}


class OnlineLearnerActiveView(OnlineLearnerViewMixin,
                              DetailView,
                              DeleteDetailModelMixin):

    url_pattern = r'ml/(?P<tag>.+)/active$'
    endpoint_name = 'online_learner_active_view'

    def to_dict(self, instance):
        return {
            'active': instance.active,
            'id': instance.id
        }

    def put(self, request, *args, **kwargs):
        """ On PUT, activate the learner """
        instance = self.get_object(request, *args, **kwargs)
        if not self.has_access(instance):
            raise self.UnauthorizedException("You don't have access to this resource")

        instance.active = True
        instance.save()

        serialized = self.to_dict(instance)
        url = self.get_url(instance)
        if url:
            serialized['url'] = url
        return serialized

    def delete_model(self, model, request, *args, **kwargs):
        """ On DELETE, deactivate the learner """
        model.active = False
        model.save()
        return model


class OnlineLearnerResetView(OnlineLearnerViewMixin,
                             DetailView):

    url_pattern = r'ml/(?P<tag>.+)/reset$'
    endpoint_name = 'online_learner_reset_view'

    def to_dict(self, instance):
        output = {'reset': (not instance.samples)}
        output.update(instance.to_dict())
        return output

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


class OnlineLearnerTrainView(OnlineLearnerViewMixin,
                             ActionView):
    """
    Trains the online classifier sample by sample on POST request.
    Request body format:
        [{'content': 'text 3', 'polarity': True},
         {'content': 'text 2', 'polarity': False}]
    (where polarity is true if the tag applies to the content)
    """

    url_pattern = r'ml/(?P<tag>.+)/train$'
    endpoint_name = 'online_learner_train_view'

    def action(self, request, *args, **kwargs):
        """ Feed sample for training """
        logger = logging.getLogger(__name__)

        data = json.loads(request.body)
        if type(data) != list:
            data = [data]

        fcd = LearnerFacade.get_or_create(self.instance.tag, self.user)
        try:
            capsules = [Capsule(sample['content']) for sample in data]
        except KeyError:
            logger.error('OnlineLearner train API endpoint called with '
                         'malformed data (missing `content`)')
            return {'status': 0, 'message': "Please provide a 'content'"}
        try:
            labels = [sample['polarity'] for sample in data]
        except KeyError:
            logger.error('OnlineLearner train API endpoint called with '
                         'malformed data (missing `polarity`)')
            return {'status': 0, 'message': "Please provide a 'polarity'"}

        fcd.train(capsules, labels)

        return {'status': 1, 'message': "OK"}
