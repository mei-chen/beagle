import itertools
import logging
import urllib

# App
from core.models import AccessToken, generate_random_token
from core.utils import (
    user_to_dict,
    send_experiment_invite,
    revoke_experiment_invite,
)
from dataset.models import Dataset
from experiment.api import serializers
from experiment.models import (
    Experiment, Formula,
    generate_default_experiment_name,
)
from experiment.tasks import (
    simulate_classification,
    evaluate_metrics,
    generate_predictions,
    add_sample_to_online_learner,
    remove_sample_from_online_learner,
    update_online_learner_samples,
    reset_online_learner,
    make_combined_predictions,
    learner_facade_get_or_create,
    learner_facade_get_all,
    learner_facade_train,
    learner_facade_predict,
    learner_facade_remove_sample,
    online_learner_update_flags,
    online_learner_reset,
    online_learner_get_samples,
)

# REST framework
from rest_framework import authentication
from rest_framework.decorators import action
from rest_framework import exceptions as drf_exceptions
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.settings import api_settings as drf_settings
from rest_framework import status
from rest_framework import viewsets

# Django
from django.conf import settings as django_settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.core import exceptions as django_exceptions
from django.core.validators import validate_email
from django.db.models import BooleanField, Case, When
from django.db.models.expressions import Value
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, reverse

# Misc
from constance import config as constance_settings
from itsdangerous import URLSafeSerializer

logger = logging.getLogger(__name__)


class ExperimentViewSet(viewsets.ModelViewSet):
    # Hide private experiments
    manager = Experiment.public

    def get_queryset(self):
        return self.manager.order_by('-created')

    def filter_queryset(self, queryset):
        """
        Each user has full access to its own experiments and
        limited access to experiments he/she is collaborating on.
        """
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        queryset_owning = queryset.filter(owner=user)
        queryset_collaborating = queryset.filter(
            id__in=user.experiment_collaboration_invites_received.values_list(
                'experiment_id', flat=True
            )
        )
        # Front-end should know whether the current user has owner permissions
        queryset_final = (queryset_owning | queryset_collaborating).annotate(
            is_owner=Case(
                When(owner=user, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).select_related('owner')
        return queryset_final

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.ExperimentSerializerExtended
        return serializers.ExperimentSerializer

    def _validate_data(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _respond(self, experiment):
        return Response(
            {
                'id': experiment.pk,
                'name': experiment.name,
                'formula': {
                    'content': experiment.formula.content_extended
                }
            }
        )

    @action(detail=False,methods=['GET'])
    def suggest_default_name(self, request, *args, **kwargs):
        next_default_name = generate_default_experiment_name(request.user,
                                                             self.manager)
        return Response({'next_default_name': next_default_name})

    def create(self, request, *args, **kwargs):
        data = self._validate_data(request)
        experiment, created = self.manager.get_or_create(
            name=data['name'], owner=request.user
        )
        if not created:
            return Response(
                {'error': 'This name has already been taken'},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            formula = Formula.objects.create()
            formula.create_classifiers(data['formula'])
            experiment.formula = formula
            experiment.save()
            return self._respond(experiment)

    def update(self, request, *args, **kwargs):
        data = self._validate_data(request)
        experiment = self.get_object()
        if experiment.name != data['name']:
            if self.manager.filter(
                name=data['name'], owner=request.user
            ).exists():
                return Response(
                    {'error': 'This name has already been taken'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                experiment.name = data['name']
        experiment.formula.update_classifiers(data['formula'])
        experiment.save()
        return self._respond(experiment)

    @action(detail=True, methods=['POST'])
    def simulate(self, request, *args, **kwargs):
        experiment = self.get_object()
        simulate_classification.delay(session_key=request.session.session_key,
                                      experiment_pk=experiment.pk,
                                      sample=request.data['sample'],
                                      task_uuid=request.data['task_uuid'])
        return Response()

    @action(detail=True, methods=['GET'])
    def get_evaluate_data(self, request, *args, **kwargs):
        experiment = self.get_object()
        data = experiment.get_cached_data('evaluate')
        if data is None:
            raise Http404
        response_data = {
            'id': data['dataset_pk'],
            'mapping': data['mapping']
        }
        return Response(response_data)

    @action(detail=True, methods=['POST'])
    def set_evaluate_data(self, request, *args, **kwargs):
        experiment = self.get_object()
        data = {
            'dataset_pk': request.data['id'],
            'mapping': request.data['mapping']
        }
        experiment.set_cached_data('evaluate', data)
        return Response()

    @action(detail=True, methods=['POST'])
    def evaluate(self, request, *args, **kwargs):
        experiment = self.get_object()
        evaluate_metrics.delay(session_key=request.session.session_key,
                               experiment_pk=experiment.pk,
                               dataset_pk=request.data['id'],
                               mapping=request.data['mapping'],
                               split=request.data['split'],
                               task_uuid=request.data['task_uuid'])
        return Response()

    @action(detail=True, methods=['POST'])
    def generate(self, request, *args, **kwargs):
        experiment = self.get_object()
        generate_predictions.delay(session_key=request.session.session_key,
                                   experiment_pk=experiment.pk,
                                   dataset_pk=request.data['id'],
                                   mapping=request.data['mapping'],
                                   split=request.data['split'],
                                   task_uuid=request.data['task_uuid'])
        return Response()

    def _check_owner(self, request, experiment):
        if request.user != experiment.owner:
            raise drf_exceptions.PermissionDenied('Access forbidden.')

    def destroy(self, request, *args, **kwargs):
        experiment = self.get_object()
        self._check_owner(request, experiment)
        experiment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET'])
    def list_collaborators(self, request, *args, **kwargs):
        experiment = self.get_object()
        self._check_owner(request, experiment)
        payload = {
            'collaborators': list(map(user_to_dict, experiment.collaborators)),
            'pending_invites': experiment.pending_invites
        }
        return Response(payload)

    @action(detail=True, methods=['POST'])
    def invite_collaborator(self, request, *args, **kwargs):
        experiment = self.get_object()
        self._check_owner(request, experiment)
        inviter = request.user
        email = request.data['email']
        try:
            validate_email(email)
        except django_exceptions.ValidationError:
            raise drf_exceptions.ValidationError('Invalid email address.')
        # The website domain is needed for building URLs later on,
        # and it is accessible only here (i.e. via request objects)
        domain = request.build_absolute_uri('/')
        status, message = send_experiment_invite(
            email, inviter, experiment, domain
        )
        if not status:
            raise drf_exceptions.ValidationError(message)
        return Response()

    @action(detail=True, methods=['POST'])
    def uninvite_collaborator(self, request, *args, **kwargs):
        experiment = self.get_object()
        user = request.user
        username = request.data.get('username')
        if username and username != user.username:
            # Only the owner is allowed to revoke access from anyone,
            # though collaborators can only revoke access from themselves
            self._check_owner(request, experiment)
        else:
            # The user revokes access from himself/herself
            username = user.username
        revoke_experiment_invite(username, experiment)
        return Response()


class IsNotAuthenticated(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return not super(IsNotAuthenticated, self).has_permission(request, view)


class DogboneViewSet(viewsets.ViewSet):
    permission_classes = [IsNotAuthenticated]

    SERIALIZER_SECRET_KEY = '/*[dogbone]->(spot)*/'

    @action(detail=False,methods=['GET'])
    def authorize(self, request, *args, **kwargs):
        connect_uri = request.build_absolute_uri(
            reverse('experiment-api:dogbone-connect')
        )
        login_uri = request.build_absolute_uri(
            reverse('experiment-api:dogbone-login')
        )
        dogbone_authorize_url = '{url}?{query}'.format(
            url=constance_settings.DOGBONE_AUTHORIZE_URL,
            query=urllib.parse.urlencode(
                {'connect_uri': connect_uri, 'login_uri': login_uri}
            )
        )
        return HttpResponseRedirect(dogbone_authorize_url)

    @action(detail=False,methods=['POST'])
    def connect(self, request, *args, **kwargs):
        data = request.data

        defaults = data['user']
        username = defaults.pop('username')
        # The username field must always be treated as immutable
        user, _ = User.objects.update_or_create(username=username,
                                                defaults=defaults)

        access_token = data['access_token']
        while True:
            try:
                defaults = {'value': access_token}
                AccessToken.objects.update_or_create(owner=user,
                                                     defaults=defaults)
                break
            except:  # validation failed or collision occurred
                access_token = generate_random_token()

        payload = {'access_token': access_token}
        return Response(payload)

    @action(detail=False,methods=['GET'])
    def login(self, request, *args, **kwargs):
        try:
            serializer = URLSafeSerializer(self.SERIALIZER_SECRET_KEY)
            access_token = serializer.loads(
                request.query_params['access_token']
            )

            user = AccessToken.objects.get(value=access_token).owner

            # Login the user without a password, i.e. avoid calling:
            # user = auth.authenticate(**credentials)
            backend = django_settings.AUTHENTICATION_BACKENDS[0]
            auth.login(request, user, backend=backend)

        except:  # authentication failed
            pass  # nothing to do

        return HttpResponseRedirect('/')


class AccessTokenAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        token = request.META.get('HTTP_X_ACCESS_TOKEN')
        if token:
            token = AccessToken.objects.filter(value=token).last()
            if token:
                return None, token


class IsAuthenticatedExtension(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return request.auth or \
            super(IsAuthenticatedExtension, self).has_permission(request, view)


class PublishViewSet(viewsets.GenericViewSet):
    authentication_classes = [AccessTokenAuthentication] + \
                             drf_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticatedExtension]
    lookup_field = 'uuid'

    # Hide private experiments
    manager = Experiment.public

    def get_queryset(self):
        return self.manager.select_related('owner').order_by('-created')

    @staticmethod
    def _filter_queryset_for_user(queryset, user):
        queryset_owning = queryset.filter(owner=user)
        queryset_collaborating = queryset.filter(
            id__in=user.experiment_collaboration_invites_received.values_list(
                'experiment_id', flat=True
            )
        )
        return queryset_owning | queryset_collaborating

    def filter_queryset(self, queryset):
        token = self.request.auth
        if token:
            user = token.owner
            if user:
                return self._filter_queryset_for_user(queryset, user)
            return queryset
        user = self.request.user
        if user and user.is_authenticated:
            return self._filter_queryset_for_user(queryset, user)
        return queryset.none()

    @action(detail=False,methods=['GET'])
    def ping(self, request, *args, **kwargs):
        """ Simply checks that the user has access to the Publish API. """
        payload = {'pong': True}
        return Response(payload)

    def _experiment_to_extended_dict(self, experiment, tags):
        experiment_dict = experiment.to_dict()
        online_learners_dict = {}
        online_learners = experiment.online_learners.filter(
            tag__in=list(map(experiment.build_online_learner_tag, tags))
        )
        for online_learner in online_learners:
            # Format: <username>#<experiment_uuid>
            username, _, _ = online_learner.tag.partition('#')
            online_learners_dict[username] = {
                'samples': online_learner.total_set_size
            }
        if online_learners_dict:
            experiment_dict['online_learners'] = online_learners_dict
        return experiment_dict

    def retrieve(self, request, *args, **kwargs):
        experiment = self.get_object()
        tags = request.query_params.getlist('tag')
        experiment_dict = self._experiment_to_extended_dict(experiment, tags)
        return Response(experiment_dict)

    @staticmethod
    def _check_field(data, field):
        if not field in data:
            raise drf_exceptions.ValidationError("No '%s' specified." % field)

    @action(detail=True, methods=['POST'])
    def add_sample(self, request, *args, **kwargs):
        experiment = self.get_object()
        data = request.data
        self._check_field(data, 'tag')
        self._check_field(data, 'text')
        self._check_field(data, 'label')
        add_sample_to_online_learner.delay(
            experiment_pk=experiment.pk,
            tag=data['tag'],
            text=data['text'],
            label=data['label'],
            infered_negatives=data.get('infered_negatives'),
        )
        return Response()

    @action(detail=True, methods=['POST'])
    def remove_sample(self, request, *args, **kwargs):
        experiment = self.get_object()
        data = request.data
        self._check_field(data, 'tag')
        self._check_field(data, 'text')
        self._check_field(data, 'label')
        remove_sample_from_online_learner.delay(
            experiment_pk=experiment.pk,
            tag=data['tag'],
            text=data['text'],
            label=data['label'],
        )
        return Response()

    @action(detail=True, methods=['POST'])
    def get_samples(self, request, *args, **kwargs):
        experiment = self.get_object()
        data = request.data
        self._check_field(data, 'tag')
        tag = experiment.build_online_learner_tag(data['tag'])
        online_learner = get_object_or_404(experiment.online_learners, tag=tag)
        payload = {'tagged': [], 'inferred': []}
        samples = online_learner.samples
        if samples:
            for index, (text, label, infered) in enumerate(zip(
                samples['text'], samples['label'], samples['infered']
            )):
                entry = {'index': index, 'text': text}
                if infered:
                    payload['inferred'].append(entry)
                else:
                    entry['label'] = label
                    payload['tagged'].append(entry)
        return Response(payload)

    @action(detail=True, methods=['POST'])
    def update_samples(self, request, *args, **kwargs):
        experiment = self.get_object()
        data = request.data
        self._check_field(data, 'tag')
        tag = experiment.build_online_learner_tag(data['tag'])
        online_learner = get_object_or_404(experiment.online_learners, tag=tag)
        update_online_learner_samples.delay(
            online_learner_pk=online_learner.pk,
            add=data.get('add'),
            edit=data.get('edit'),
            remove=data.get('remove'),
        )
        return Response()

    @action(detail=True, methods=['POST'])
    def reset(self, request, *args, **kwargs):
        experiment = self.get_object()
        data = request.data
        self._check_field(data, 'tag')
        tag = experiment.build_online_learner_tag(data['tag'])
        online_learner = experiment.online_learners.filter(tag=tag).last()
        if online_learner:
            reset_online_learner.delay(online_learner.pk)
        return Response()

    @action(detail=True, methods=['POST'])
    def predict(self, request, *args, **kwargs):
        experiment = self.get_object()
        data = request.data
        self._check_field(data, 'tag')
        self._check_field(data, 'samples')
        predictions = make_combined_predictions.delay(
            experiment_pk=experiment.pk,
            tag=data['tag'],
            samples=data['samples'],
        ).get()
        tags = [data['tag']]
        experiment_dict = self._experiment_to_extended_dict(experiment, tags)
        payload = {
            'predictions': predictions,
            'experiment': experiment_dict
        }
        return Response(payload)

    @action(detail=False,methods=['GET'])
    def suggestions(self, request, *args, **kwargs):
        experiments = self.filter_queryset(self.get_queryset())
        payload = list(map(Experiment.to_dict, experiments))
        return Response(payload)

    @action(detail=True, methods=['POST'])
    def collect_to_dataset(self, request, *args, **kwargs):
        experiment = self.get_object()
        data = request.data
        self._check_field(data, 'tag')
        self._check_field(data, 'name')
        self._check_field(data, 'include_inferred')
        tag = experiment.build_online_learner_tag(data['tag'])
        online_learner = get_object_or_404(experiment.online_learners, tag=tag)
        texts = []
        labels = []
        samples = online_learner.samples
        if samples:
            for index, (text, label, infered) in enumerate(zip(
                samples['text'], samples['label'], samples['infered']
            )):
                if data['include_inferred'] or not infered:
                    texts.append(text)
                    # Make sure to convert boolean labels to integer indices,
                    # i.e.: False -> 0, True -> 1
                    labels.append(int(label))
        description = 'Collected (%s inferred samples) from ' \
                      'online learner tag=%s of experiment uuid=%s' % \
                      ('including' if data['include_inferred'] else 'excluding',
                       data['tag'], experiment.uuid)
        dataset = Dataset.objects.create(
            name=data['name'],
            description=description,
            owner=request.user,
            supervised=True,
            klasses=['False', 'True'],  # must be a list of strings!
            samples={
                'texts': texts,
                'labels': labels
            }
        )
        payload = {'dataset': dataset.to_dict()}
        return Response(payload)


class OnlineLearnerViewSet(viewsets.ViewSet):
    authentication_classes = [AccessTokenAuthentication] + \
                             drf_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = [IsAuthenticatedExtension]

    @property
    def user(self):
        token = self.request.auth
        if token:
            user = token.owner
            if user:
                return user
        user = self.request.user
        if user and user.is_authenticated:
            return user
        raise drf_exceptions.PermissionDenied('Access forbidden.')

    @action(detail=False,methods=['GET'])
    def ping(self, request, *args, **kwargs):
        """ Simply checks that the user has access to the OnlineLearner API. """
        payload = {'pong': True}
        return Response(payload)

    @staticmethod
    def _check_field(data, field):
        if not field in data:
            raise drf_exceptions.ValidationError("No '%s' specified." % field)

    @action(detail=False,methods=['POST'])
    def get_or_create(self, request, *args, **kwargs):
        data = request.data
        self._check_field(data, 'tag')
        personal = data.get('personal', True)
        payload = learner_facade_get_or_create.delay(
            user_pk=self.user.pk if personal else None,
            tag=data['tag'],
            include_deleted=data.get('include_deleted'),
            defaults=data.get('defaults'),
        ).get()
        return Response(payload)

    @action(detail=False,methods=['POST'])
    def get_all(self, request, *args, **kwargs):
        data = request.data
        personal = data.get('personal', True)
        payload = learner_facade_get_all.delay(
            user_pk=self.user.pk if personal else None,
            active_only=data.get('active_only'),
            mature_only=data.get('mature_only'),
            include_deleted=data.get('include_deleted'),
        ).get()
        return Response(payload)

    @action(detail=False,methods=['POST'])
    def train(self, request, *args, **kwargs):
        data = request.data
        self._check_field(data, 'tag')
        self._check_field(data, 'texts')
        self._check_field(data, 'labels')
        learner_facade_train.delay(
            user_pk=self.user.pk,
            tag=data['tag'],
            texts=data['texts'],
            labels=data['labels'],
            flags=data.get('flags'),
            infered_negatives=data.get('infered_negatives'),
        )
        return Response()

    @action(detail=False,methods=['POST'])
    def predict(self, request, *args, **kwargs):
        data = request.data
        self._check_field(data, 'tag')
        self._check_field(data, 'texts')
        payload = learner_facade_predict.delay(
            user_pk=self.user.pk,
            tag=data['tag'],
            texts=data['texts'],
            flags=data.get('flags'),
            include_attributes=data.get('include_attributes'),
        ).get()
        return Response(payload)

    @action(detail=False,methods=['POST'])
    def remove_sample(self, request, *args, **kwargs):
        data = request.data
        self._check_field(data, 'tag')
        self._check_field(data, 'text')
        learner_facade_remove_sample.delay(
            user_pk=self.user.pk,
            tag=data['tag'],
            text=data['text'],
        )
        return Response()

    @action(detail=False,methods=['POST'])
    def update_flags(self, request, *args, **kwargs):
        data = request.data
        self._check_field(data, 'tag')
        online_learner_update_flags.delay(
            user_pk=self.user.pk,
            tag=data['tag'],
            flags=data.get('flags'),
        )
        return Response()

    @action(detail=False,methods=['POST'])
    def reset(self, request, *args, **kwargs):
        data = request.data
        self._check_field(data, 'tag')
        online_learner_reset.delay(
            user_pk=self.user.pk,
            tag=data['tag'],
        )
        return Response()

    @action(detail=False,methods=['POST'])
    def get_samples(self, request, *args, **kwargs):
        data = request.data
        self._check_field(data, 'tag')
        payload = online_learner_get_samples.delay(
            user_pk=self.user.pk,
            tag=data['tag'],
        ).get()
        return Response(payload)


class FormulaViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Formula.objects.order_by('-created')

    def filter_queryset(self, queryset):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        # TODO (optional): take into account collaboration
        return queryset.filter(experiment__owner=user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.FormulaSerializerExtended
        return serializers.FormulaSerializer
