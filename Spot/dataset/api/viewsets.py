from collections import defaultdict
import csv
import functools
import itertools
import logging
import re

# Django
from django.contrib.auth.models import User
from django.core import exceptions as django_exceptions
from django.core.validators import validate_email
from django.db.models import BooleanField, Case, When, Prefetch
from django.db.models.expressions import Value
from django.http import JsonResponse, HttpResponse

# REST framework
from rest_framework.decorators import action
from rest_framework import exceptions as drf_exceptions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets

# App
from core.utils import (
    user_to_dict,
    send_dataset_invite,
    revoke_dataset_invite,
)
from dataset.api import serializers
from dataset.models import Dataset, LabelingTask, Assignment
from dataset.signals import sample_added, sample_changed, sample_removed
from dataset.tasks import (
    select_samples, store_samples,
    export_supervised_dataset,
    generate_random_sample,
    expand_evaluation_score,
    compute_accord_matrix,
    build_experiment,
)
from experiment.tasks import (
    prepare_dataset, prepare_dataset_as_unsupervised,
    preview_dataset, preview_dataset_as_unsupervised,
)

logger = logging.getLogger(__name__)


def include_samples(method):
    """
    Cancels deferring of the samples field for querysets of datasets.
    Should only be used inside DatasetViewSet.
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.defer_samples = False
        result = method(self, *args, **kwargs)
        self.defer_samples = True
        return result

    return wrapper


class DatasetViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DatasetSerializer

    def get_queryset(self):
        # In most cases the heavyweight samples field is not needed here
        # (there is a separate API for them), so defer it by default
        # (unless explicitly selected by applying the include_samples decorator)
        return Dataset.objects.defer(
            'samples' if getattr(self, 'defer_samples', True) else None
        ).order_by('-created')

    def filter_queryset(self, queryset):
        """
        Each user has full access to its own datasets and
        limited access to datasets he/she is collaborating on.
        """
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        queryset_owning = queryset.filter(owner=user)
        queryset_collaborating = queryset.filter(
            id__in=user.dataset_collaboration_invites_received.values_list(
                'dataset_id', flat=True
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

    @include_samples
    def retrieve(self, request, *args, **kwargs):
        return super(DatasetViewSet, self).retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        data = request.data

        texts = data['data']['body']
        labels = data['data']['labels']

        mapping = data.get('mapping')
        if mapping and mapping['neg'] and mapping['pos']:
            mapped_labels = []
            mapped_texts = []
            for text, label in itertools.izip(texts, labels):
                if label in mapping['pos']:
                    mapped_labels.append('True')
                    mapped_texts.append(text)
                elif label in mapping['neg']:
                    mapped_labels.append('False')
                    mapped_texts.append(text)
            texts = mapped_texts
            labels = mapped_labels

        # Replace missing labels with the empty string
        klass_labels = map(lambda label: label or '', labels)

        klasses = sorted(set(klass_labels))
        # If all labels turned out to be null (i.e. None),
        # then the dataset should be treated as unsupervised
        if len(klasses) == 1 and klasses[0] == '':
            supervised = False
            samples = {'texts': texts}
            klasses = None
        else:
            supervised = True
            klass_to_index = {label: index for index, label in enumerate(klasses)}
            # Use integer indices for labeling samples
            index_labels = [klass_to_index[label] for label in klass_labels]
            samples = {'texts': texts, 'labels': index_labels}

        dataset = Dataset.objects.create(
            name=data['filename'],
            description=data.get('description', ''),
            supervised=supervised,
            samples=samples,
            klasses=klasses,
            train_percentage=data['data']['trainingPercentage'],
            owner=request.user
        )

        payload = {'dataset': dataset.to_dict()}
        return Response(payload)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super(DatasetViewSet, self).update(request, *args, **kwargs)

    @action(detail=True, methods=['GET'])
    @include_samples
    def export(self, request, *args, **kwargs):
        dataset = self.get_object()

        filename = dataset.name
        if not filename.endswith('.csv'):
            filename += '.csv'

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename

        writer = csv.writer(response)

        body = dataset.texts

        if dataset.supervised:
            writer.writerow(['Body', 'Label'])

            labels = dataset.klass_labels

            for b, l in itertools.izip(body, labels):
                writer.writerow([b.encode('utf-8'), l.encode('utf-8')])

        else:
            writer.writerow(['Body'])

            for b in body:
                writer.writerow([b.encode('utf-8')])

        return response

    @action(detail=True, methods=['POST'])
    @include_samples
    def preview(self, request, *args, **kwargs):
        try:
            dataset = self.get_object()
            mapping = request.data['mapping']
            split = request.data['split']
            if mapping is None:
                X = prepare_dataset_as_unsupervised(dataset=dataset,
                                                    split=split)
                payload = preview_dataset_as_unsupervised(X)
            else:
                X, y = prepare_dataset(dataset=dataset,
                                       mapping=mapping,
                                       split=split)
                payload = preview_dataset(X, y)
            return JsonResponse(payload)
        except ValueError as splitting_error:
            raise drf_exceptions.ValidationError(splitting_error)

    def _check_owner(self, request, dataset):
        if request.user != dataset.owner:
            raise drf_exceptions.PermissionDenied('Access forbidden.')

    def destroy(self, request, *args, **kwargs):
        dataset = self.get_object()
        self._check_owner(request, dataset)
        dataset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET'])
    def list_collaborators(self, request, *args, **kwargs):
        dataset = self.get_object()
        self._check_owner(request, dataset)
        payload = {
            'collaborators': map(user_to_dict, dataset.collaborators),
            'pending_invites': dataset.pending_invites
        }
        return JsonResponse(payload)

    @action(detail=True, methods=['POST'])
    def invite_collaborator(self, request, *args, **kwargs):
        dataset = self.get_object()
        self._check_owner(request, dataset)
        inviter = request.user
        email = request.data['email']
        try:
            validate_email(email)
        except django_exceptions.ValidationError:
            raise drf_exceptions.ValidationError('Invalid email address.')
        # The website domain is needed for building URLs later on,
        # and it is accessible only here (i.e. via request objects)
        domain = request.build_absolute_uri('/')
        status, message = send_dataset_invite(
            email, inviter, dataset, domain
        )
        if not status:
            raise drf_exceptions.ValidationError(message)
        return Response()

    @action(detail=True, methods=['POST'])
    def uninvite_collaborator(self, request, *args, **kwargs):
        dataset = self.get_object()
        user = request.user
        username = request.data.get('username')
        if username and username != user.username:
            # Only the owner is allowed to revoke access from anyone,
            # though collaborators can only revoke access from themselves
            self._check_owner(request, dataset)
        else:
            # The user revokes access from himself/herself
            username = user.username
        revoke_dataset_invite(username, dataset)
        return Response()

    @action(detail=True, methods=['GET'])
    def allowed_users(self, request, *args, **kwargs):
        dataset = self.get_object()
        payload = map(user_to_dict, [dataset.owner] + dataset.collaborators)
        return JsonResponse(payload, safe=False)

    @action(detail=True, methods=['POST'])
    @include_samples
    def random_sample(self, request, *args, **kwargs):
        dataset = self.get_object()
        data = request.data
        samples = generate_random_sample(dataset,
                                         size=data.get('size'),
                                         excluded=data.get('excluded'))
        payload = {'samples': samples}
        return Response(payload)


class SamplePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data, labels_counts=None):
        response = super(SamplePagination, self).get_paginated_response(data)
        if labels_counts is not None:
            response.data['label_count'] = labels_counts
        return response


class SampleViewSet(viewsets.ViewSet):
    pagination_class = SamplePagination
    serializer_class = serializers.get_serializer_class()

    @property
    def paginator(self):
        """ The paginator instance associated with the view. """
        if not hasattr(self, '_paginator'):
            self._paginator = self.pagination_class()
        return self._paginator

    def _get_dataset(self, dataset_pk):
        user = self.request.user
        if user.is_authenticated:
            # Check that the dataset exists and the current user can access it
            dataset = Dataset.objects.filter(pk=dataset_pk).last()
            if dataset and dataset.has_access(user):
                # Customize the serializer class for the current dataset
                self.serializer_class = \
                    serializers.get_serializer_class(dataset)
                return dataset
        raise drf_exceptions.NotFound

    def _get_sample_index(self, dataset, pk):
        try:
            sample_index = int(pk)
            assert 0 <= sample_index < dataset.samples_count
            return sample_index
        except:
            raise drf_exceptions.NotFound

    def _validate(self, data):
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _update_sample(self, dataset, sample_index, data):
        validated_data = self._validate(data)
        try:
            dataset.set_sample(sample_index,
                               text=validated_data.get('text'),
                               label=validated_data.get('label'))
        except:
            raise drf_exceptions.ValidationError(
                'Invalid label. Valid values are {%s}.' %
                ', '.join(str(klass) for klass in dataset.klasses)
            )

    def _create_sample(self, dataset, data):
        sample_index = dataset.samples_count
        # Add dummy placeholder values instead of an actual sample,
        # which will be overwritten and saved only if the validation succeeds
        dataset.add_sample(text=None, label=None)
        self._update_sample(dataset, sample_index, data)
        return sample_index

    def _destroy_sample(self, dataset, sample_index):
        return dataset.pop_sample(sample_index)

    def _get_sample_or_samples(self, dataset, sample_index=None):
        if sample_index is None:
            return [dataset.get_sample(index)
                    for index in range(dataset.samples_count)]
        else:
            return dataset.get_sample(sample_index)

    def _serialize(self, sample_or_samples):
        serializer = self.serializer_class(
            instance=sample_or_samples,
            many=isinstance(sample_or_samples, list)
        )
        return serializer.data

    def _get_response(self, sample):
        serialized_sample = self._serialize(sample)
        return Response(serialized_sample)

    def _get_sort_params(self, request):
        sort_params = {}
        sort_by = request.query_params.get('sortBy')
        if sort_by == 'body':  # alias
            sort_by = 'text'
        if sort_by in ('text', 'label'):
            # If the field to sort by is specified and valid,
            # then the default order (if not specified) should be 'asc'
            order = request.query_params.get('order', 'asc')
            # Invalid orders are also treated as 'asc'
            reverse_map = {'asc': False, 'desc': True}
            if order not in reverse_map:
                order = 'asc'
            reverse = reverse_map[order]
            sort_params['key'] = lambda sample: getattr(sample, sort_by)
            sort_params['reverse'] = reverse
        return sort_params

    def _get_paginated_response(self, samples, labels, search, sort_params):
        labels_counts = None
        if labels:
            filtered_samples = []
            labels_counts = defaultdict(int)
            for sample in samples:
                sample_label = sample.label
                if sample_label in labels:
                    filtered_samples.append(sample)
                    labels_counts[sample_label] += 1
            samples = filtered_samples
        if search:
            search_re = re.compile(search, re.IGNORECASE)
            filtered_samples = [sample for sample in samples
                                if search_re.search(sample.text)]
            samples = filtered_samples
        if sort_params:
            samples.sort(**sort_params)
        page = self.paginator.paginate_queryset(samples, self.request,
                                                view=self)
        serialized_page_samples = self._serialize(page)
        return self.paginator.get_paginated_response(serialized_page_samples,
                                                     labels_counts)

    # Main methods of REST API framework

    def retrieve(self, request, pk=None, dataset_pk=None):
        dataset = self._get_dataset(dataset_pk)
        sample_index = self._get_sample_index(dataset, pk)
        sample = self._get_sample_or_samples(dataset, sample_index)
        return self._get_response(sample)

    def update(self, request, pk=None, dataset_pk=None):
        dataset = self._get_dataset(dataset_pk)
        sample_index = self._get_sample_index(dataset, pk)
        self._update_sample(dataset, sample_index, request.data)
        sample = self._get_sample_or_samples(dataset, sample_index)
        sample_changed.send(sender=Dataset, instance=dataset)
        return self._get_response(sample)

    partial_update = update

    def list(self, request, dataset_pk=None):
        dataset = self._get_dataset(dataset_pk)
        samples = self._get_sample_or_samples(dataset)
        # Allow filtering by labels (specified as query params)
        labels = set(request.query_params.getlist('label'))
        # Allow filtering (i.e. case-independent searching) by text snippets
        search = request.query_params.get('search')
        # Allow sorting by either text or label
        # in some specified order ('asc' or 'desc')
        sort_params = self._get_sort_params(request)
        return self._get_paginated_response(
            samples, labels, search, sort_params
        )

    def create(self, request, dataset_pk=None):
        dataset = self._get_dataset(dataset_pk)
        sample_index = self._create_sample(dataset, request.data)
        sample = self._get_sample_or_samples(dataset, sample_index)
        sample_added.send(sender=Dataset, instance=dataset)
        return self._get_response(sample)

    def destroy(self, request, pk=None, dataset_pk=None):
        dataset = self._get_dataset(dataset_pk)
        sample_index = self._get_sample_index(dataset, pk)
        if dataset.labeling_tasks.exists():
            raise drf_exceptions.MethodNotAllowed(
                'Dataset has labeling tasks associated with it. '
                'Make sure to finish them all first.'
            )
        sample = self._destroy_sample(dataset, sample_index)
        sample_removed.send(sender=Dataset, instance=dataset)
        return self._get_response(sample)


class LabelingTaskViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return LabelingTask.objects.order_by('-created')

    def filter_queryset(self, queryset):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        return queryset.filter(owner=user).select_related(
            'dataset__owner', 'owner'
        ).prefetch_related(
            Prefetch('assignments', Assignment.objects.order_by('-created'))
        ).prefetch_related(
            'assignments__assignee'
        ).defer(
            'dataset__samples'
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.LabelingTaskSerializerOutput
        return serializers.LabelingTaskSerializerInput

    @staticmethod
    def _check_field(data, field):
        if not field in data:
            raise drf_exceptions.ValidationError("No '%s' specified." % field)

    @action(detail=True, methods=['POST'])
    def assign(self, request, *args, **kwargs):
        labeling_task = self.get_object()
        data = request.data
        self._check_field(data, 'assignees')
        assignees_ids = map(int, data['assignees'])
        invalid_assignees_ids = set(assignees_ids)
        # An assignee is considered to be valid,
        # if it exists and has access to the dataset
        assignees = User.objects.filter(id__in=assignees_ids)
        for assignee in assignees:
            if labeling_task.dataset.has_access(assignee):
                _, created = Assignment.objects.get_or_create(
                    labeling_task=labeling_task, assignee=assignee
                )
                if created:  # i.e. valid
                    invalid_assignees_ids.remove(assignee.id)
        payload = {'invalid_assignees': invalid_assignees_ids}
        return Response(payload)

    @action(detail=True, methods=['POST'])
    def unassign(self, request, *args, **kwargs):
        labeling_task = self.get_object()
        data = request.data
        self._check_field(data, 'assignment')
        assignment_id = data['assignment']
        assignment = labeling_task.assignments.filter(id=assignment_id).last()
        if not assignment:
            raise drf_exceptions.NotFound('Assignment does not exist.')
        assignment.delete()
        return Response()

    @action(detail=True, methods=['POST'])
    def export_supervised_dataset(self, request, *args, **kwargs):
        labeling_task = self.get_object()
        data = request.data
        self._check_field(data, 'name')
        self._check_field(data, 'description')
        self._check_field(data, 'task_uuid')
        export_supervised_dataset.delay(session_key=request.session.session_key,
                                        labeling_task_pk=labeling_task.pk,
                                        name=data['name'],
                                        description=data['description'],
                                        task_uuid=data['task_uuid'])
        return Response()

    @action(detail=True, methods=['POST'])
    def expand_evaluation_score(self, request, *args, **kwargs):
        labeling_task = self.get_object()
        data = request.data
        self._check_field(data, 'assignment')
        self._check_field(data, 'task_uuid')
        assignment_id = data['assignment']
        assignment = labeling_task.assignments.filter(id=assignment_id).last()
        if not assignment:
            raise drf_exceptions.NotFound('Assignment does not exist.')
        expand_evaluation_score.delay(session_key=request.session.session_key,
                                      assignment_pk=assignment.pk,
                                      task_uuid=data['task_uuid'])
        return Response()

    @action(detail=True, methods=['POST'])
    def compute_accord_matrix(self, request, *args, **kwargs):
        labeling_task = self.get_object()
        data = request.data
        self._check_field(data, 'task_uuid')
        compute_accord_matrix.delay(session_key=request.session.session_key,
                                    labeling_task_pk=labeling_task.pk,
                                    task_uuid=data['task_uuid'])
        return Response()


class AssignmentViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return Assignment.objects.order_by('-created')

    def filter_queryset(self, queryset):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        return queryset.filter(assignee=user).select_related(
            'labeling_task__dataset__owner', 'labeling_task__owner', 'assignee'
        ).defer(
            'labeling_task__dataset__samples', 'stages'
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.AssignmentSerializerOutput
        return serializers.AssignmentSerializerInput

    @staticmethod
    def _check_field(data, field):
        if not field in data:
            raise drf_exceptions.ValidationError("No '%s' specified." % field)

    @action(detail=True, methods=['POST'])
    def start_stage(self, request, *args, **kwargs):
        assignment = self.get_object()
        data = request.data
        self._check_field(data, 'task_uuid')
        select_samples.delay(session_key=request.session.session_key,
                             assignment_pk=assignment.pk,
                             task_uuid=data['task_uuid'])
        return Response()

    @action(detail=True, methods=['POST'])
    def finish_stage(self, request, *args, **kwargs):
        assignment = self.get_object()
        data = request.data
        self._check_field(data, 'samples')
        self._check_field(data, 'task_uuid')
        store_samples.delay(session_key=request.session.session_key,
                            assignment_pk=assignment.pk,
                            samples=data['samples'],
                            task_uuid=data['task_uuid'])
        return Response()

    @action(detail=True, methods=['POST'])
    def build_experiment(self, request, *args, **kwargs):
        assignment = self.get_object()
        data = request.data
        self._check_field(data, 'task_uuid')
        build_experiment.delay(session_key=request.session.session_key,
                               assignment_pk=assignment.pk,
                               task_uuid=data['task_uuid'])
        return Response()
