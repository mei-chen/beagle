import csv
import json
import logging

from django.http import HttpResponse

from beagle_simpleapi.endpoint import ActionView, DetailView, StatusView
from beagle_simpleapi.mixin import DeleteDetailModelMixin
from core.models import Batch
from core.tasks import process_document_task
from dogbone.actions import has_permission
from nlplib.utils import preformat_markers
from portal.services import export_batch, prepare_batch


class BatchDetailView(DetailView, DeleteDetailModelMixin):
    model = Batch
    url_pattern = r'/batch/(?P<id>\d+)$'
    endpoint_name = 'batch_detail_view'

    model_key_name = 'id'
    url_key_name = 'id'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    @classmethod
    def to_dict(cls, model):
        return model.to_dict(include_docstats=True)

    def delete(self, request, *args, **kwargs):
        self.validate_delete(request, *args, **kwargs)
        instance = self.get_object(request, *args, **kwargs)
        instance = self.delete_model(instance, request, *args, **kwargs)

        serialized = {}
        if instance:
            serialized['upload_name'] = instance.name
            serialized['documents_count'] = instance.documents_count
        return serialized


class BatchReanalysisActionView(ActionView):
    model = Batch
    url_pattern = r'/batch/(?P<id>\d+)/reanalysis$'
    endpoint_name = 'batch_reanalysis_action_view'

    model_key_name = 'id'
    url_key_name = 'id'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def get_queryset(self):
        return self.instance.get_documents_queryset()

    def action(self, request, *args, **kwargs):
        for document in self.get_queryset():
            document.invalidate_analysis()
            document.pending = True
            document.save()

            # Trigger an analysis task
            process_document_task.delay(document.pk, doclevel=False, is_reanalisys=True)

        return {'status': 1, 'message': 'OK'}


class BatchCheckAnalysisStatusView(StatusView):
    url_pattern = r'/batch/(?P<id>\d+)/check_analysis$'
    endpoint_name = 'batch_check_analysis_status_view'

    def has_access(self, instance=None):
        if not instance:
            return True
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def status(self, request, *args, **kwargs):
        batch_id = kwargs.get('id')

        try:
            batch = Batch.objects.get(id=batch_id)
            if not self.has_access(batch):
                raise self.UnauthorizedException("You don't have access to this resource")
        except Batch.DoesNotExist:
            raise self.NotFoundException("Batch does not exist")

        result = {'upload': batch_id,
                  'all_analyzed': True,
                  'documents': []}

        for document in batch.get_documents():
            analyzed = document.is_ready
            result['documents'].append({
                'document_id': document.id,
                'title': document.title,
                'analyzed': analyzed,
                'original_name': document.original_name
            })
            if not analyzed:
                result['all_analyzed'] = False

        # No need for serialization here, it will be made in parent's dispatch
        return result


class BatchPrepareExportView(ActionView):
    model = Batch
    url_pattern = r'/batch/(?P<id>\d+)/prepare_export$'
    endpoint_name = 'batch_prepare_export_view'

    model_key_name = 'id'
    url_key_name = 'id'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def action(self, request, *args, **kwargs):
        allow, _ = has_permission(request, 'export', batch=self.instance)
        if not allow:
            logging.warning('%s tried to export without proper subscription' % self.user)
            raise self.UnauthorizedException("You are not allowed to export with your subscription")

        data = json.loads(request.body)

        prepare_batch(batch=self.instance,
                      include_comments=data.get('include_comments', False),
                      include_track_changes=data.get('include_track_changes', False),
                      include_annotations=data.get('include_annotations', None))

        return {'status': 1, 'message': 'OK'}


class BatchExportView(DetailView):
    model = Batch
    url_pattern = r'/batch/(?P<id>\d+)/export$'
    endpoint_name = 'batch_export_view'

    model_key_name = 'id'
    url_key_name = 'id'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def dispatch(self, request, *args, **kwargs):
        try:
            self.check_model()
            self.instance = self.get_object(request, *args, **kwargs)

            self.user = self.authenticate_user()

            if not self.has_access(self.instance):
                raise self.UnauthorizedException("You don't have access to this resource")

            allow, _ = has_permission(request, 'export', batch=self.instance)
            if not allow:
                logging.warning('%s tried to export without proper subscription' % self.user)
                raise self.UnauthorizedException("You are not allowed to export with your subscription")

            filename, content = export_batch(self.instance)

            response = HttpResponse(content, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=' + filename
            return response

        except Exception as e:
            result = self.build_error_response_from_exception(e)
            return HttpResponse(self.serialize(result, request.GET.get('format', 'json')),
                                status=result['http_status'], content_type='application/json')


class BatchExportSummaryView(DetailView):
    model = Batch
    url_pattern = r'/batch/(?P<id>\d+)/export_summary$'
    endpoint_name = 'batch_export_summary_view'

    model_key_name = 'id'
    url_key_name = 'id'

    def has_access(self, instance):
        return (not instance.trash) and (instance.has_access(self.user) or self.user.is_superuser)

    def dispatch(self, request, *args, **kwargs):
        try:
            self.check_model()
            self.instance = self.get_object(request, *args, **kwargs)

            self.user = self.authenticate_user()

            if not self.has_access(self.instance):
                raise self.UnauthorizedException("You don't have access to this resource")

            allow, _ = has_permission(request, 'export', batch=self.instance)
            if not allow:
                logging.warning('%s tried to export without proper subscription' % self.user)
                raise self.UnauthorizedException("You are not allowed to export with your subscription")

            filename = 'batch_%d_summary.csv' % self.instance.id

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + filename

            writer = csv.writer(response)
            summary = self.build_batch_summary(self.instance)
            writer.writerows(summary)

            return response

        except Exception as e:
            result = self.build_error_response_from_exception(e)
            return HttpResponse(self.serialize(result, request.GET.get('format', 'json')),
                                status=result['http_status'], content_type='application/json')

    @staticmethod
    def build_batch_summary(batch):

        def encode_row(row):
            # In Python 2 csv module does not support Unicode input,
            # so make sure to encode rows manually
            return [entry.encode('utf-8') for entry in row]

        summary = []

        header = ['Document', 'Label', 'Clause']
        summary.append(encode_row(header))

        documents = batch.get_sorted_documents()
        for document in documents:
            sentences = document.get_sorted_sentences()
            for sentence in sentences:
                clause = preformat_markers(sentence.text)
                annotations = (sentence.annotations or {}).get('annotations', [])
                labels = [annotation['label'] for annotation in annotations]
                for label in labels:
                    row = [document.title, label, clause]
                    summary.append(encode_row(row))

        return summary
