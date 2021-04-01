import csv
import itertools
import os
import re

from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from dataset.models import Dataset
from experiment.models import Experiment
from experiment.tasks import (
    prepare_dataset, prepare_dataset_as_unsupervised,
    train_classifier, plot_classifier_decision_function,
)


class ValidateRegex(APIView):

    @staticmethod
    def post(request):
        regex = request.data.get('regex')

        if regex is None:
            return JsonResponse({
                'error': 'Please pass a regex string'
            })

        try:
            re.compile(regex)
            response = {
                'regex_is_valid': True
            }
        except re.error as e:
            response = {
                'regex_is_valid': False,
                'error': e.msg
            }

        return JsonResponse(response)


class ExportPredicted(APIView):

    @staticmethod
    def get(request, experiment_pk):
        experiment = get_object_or_404(Experiment, pk=experiment_pk)

        data = experiment.get_cached_data('generate')
        if data is None:
            raise Http404

        dataset = get_object_or_404(Dataset, pk=data['dataset_pk'])

        if data['mapping'] is None:
            X = prepare_dataset_as_unsupervised(dataset, data['split'])
        else:
            # Discard ground-truth labels
            X, _ = prepare_dataset(dataset, data['mapping'], data['split'])

        y = data['predictions']

        response = HttpResponse(content_type='text/csv')

        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % (
            os.path.splitext('%s_%s' % (experiment.name, dataset.name))[0]
        )

        writer = csv.writer(response)

        writer.writerow(['BODY', 'LABEL'])

        for text, label in zip(X, y):
            # In Python 2 csv module does not support Unicode input, so make
            # sure to encode the text manually.
            # Also convert the binary label to 0 or 1 for the sake of
            # generalization, since boolean values may have different
            # representations in programming languages.
            writer.writerow([text.encode('utf-8'), int(label)])

        return response


class DiffPredicted(APIView):

    PAGE_SIZE = 10

    @staticmethod
    def _build_url(request, experiment_pk, page):
        return request.build_absolute_uri(
            '/api/v1/diff_predicted/%d?page=%d' % (experiment_pk, page)
        )

    @classmethod
    def get(cls, request, experiment_pk):
        experiment = get_object_or_404(Experiment, pk=experiment_pk)

        data = experiment.get_cached_data('generate')
        if data is None:
            raise Http404

        dataset = get_object_or_404(Dataset, pk=data['dataset_pk'])

        X, y_true = prepare_dataset(dataset, data['mapping'], data['split'])

        y_pred = data['predictions']

        results = [{'text': text, 'label': label_pred, 'gold': label_true}
                   for text, label_true, label_pred
                   in zip(X, y_true, y_pred)
                   if label_pred != label_true]

        count = len(results)

        first_page = 1
        last_page = (count // cls.PAGE_SIZE) + bool(count % cls.PAGE_SIZE)

        try:
            page = int(request.query_params.get('page', first_page))
            assert first_page <= page <= last_page
        except (ValueError, AssertionError):
            raise Http404

        next = (None if page == last_page else
                cls._build_url(request, experiment.pk, page + 1))
        previous = (None if page == first_page else
                    cls._build_url(request, experiment.pk, page - 1))

        page_slice = slice((page - 1) * cls.PAGE_SIZE, page * cls.PAGE_SIZE)

        return JsonResponse({
            'count': count,
            'next': next,
            'previous': previous,
            'results': results[page_slice]
        })


class TrainClassifier(APIView):

    @staticmethod
    def post(request):
        for clf_uuid in request.data['uuids']:
            train_classifier.delay(session_key=request.session.session_key,
                                   clf_uuid=clf_uuid)
        return Response()


class PlotClassifierDecisionFunction(APIView):

    @staticmethod
    def get(request, clf_uuid):
        session_key = request.session.session_key
        plot_classifier_decision_function.delay(session_key=session_key,
                                                clf_uuid=clf_uuid)
        return Response()
