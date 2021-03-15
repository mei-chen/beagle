import csv
import json
import os
import shutil
import tempfile

from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from analysis.models import Report
from document.models import Document, PersonalData, CustomPersonalData
from document.tasks import (
    convert_file, cleanup_document, sentence_splitting
)
from document.api.filters import DocumentFilter
from portal.models import Batch, File, Sentence
from document.api.serializers import (
    DocumentSerializer, ConvertSerializer,
    CleanupDocumentSerializer, CleanupDocumentToolsSerializer,
    SentenceCreateSerializer, PersonalDataSerializer, CustomPersonalDataSerializer
)
from utils.conversion import docx_to_pdf
from utils.personal_data import obfuscate_document


class DocumentAPI(ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = (IsAuthenticated,)
    filter_class = DocumentFilter

    @action(detail=True,methods=['GET'])
    def obfuscate(self, request, pk):
        qp = self.request.query_params
        if qp:
            obf_reports = json.loads(qp['reports'])
        else:
            obf_reports = {}
        sents = set()
        for id in obf_reports.keys():
            report = Report.objects.get(pk=id)
            for i, entry in enumerate(json.loads(report.json)):
                i = str(i)
                if i in obf_reports[id]:
                    sents.add((entry['sentence'], obf_reports[id][i]))
        sents = list(sents)

        return self._obfuscate(sents)

    @action(detail=True,methods=['GET'])
    def obfuscate_sents(self, request, *args, **kwargs):
        qp = self.request.query_params
        sents = json.loads(qp.get('sents', '[]'))
        sents = [(Sentence.objects.get(id=id).text, obf_type)
                 for id, obf_type in sents]

        return self._obfuscate(sents)

    def _obfuscate(self, sents):
        document = self.get_object()
        obfuscated = obfuscate_document(document, sents)
        user = document.source_file.batch.owner
        if user.profile.obfuscated_export_ext == 'PDF':
            tmp_dir = tempfile.mkdtemp()
            path = os.path.join(tmp_dir, '%s.docx' % document.name)
            fl = open(path, 'w')
            fl.write(obfuscated.read())
            fl.close()
            docx_to_pdf(tmp_dir, path)
            with open(os.path.join(tmp_dir, '%s.pdf' % document.name), 'rb') as pdf:
                response = HttpResponse(
                    pdf,
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = 'attachment; filename="%s-obfuscated.pdf' % document.name
            shutil.rmtree(tmp_dir)
        else:
            response = HttpResponse(
                obfuscated,
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = 'attachment; filename=%s-obfuscated.docx' % document.name

        return response


class ConvertAPI(CreateModelMixin, ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ConvertSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        for conv_file in serializer.validated_data['files']:
            convert_file.delay(conv_file.id, self.request.session.session_key)


class CleanupDocumentAPI(CreateModelMixin, ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CleanupDocumentSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        tools = serializer.validated_data['sequence']
        for doc in serializer.validated_data['documents']:
            cleanup_document.delay(
                tools, doc.id, self.request.session.session_key)


class CleanupDocumentToolsAPI(ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CleanupDocumentToolsSerializer

    def list(self, request):
        queryset = [{'tool': tool} for tool in Document.get_tool()]
        serializer = CleanupDocumentToolsSerializer(queryset, many=True)
        return Response(serializer.data)


class SentenceAPI(CreateModelMixin, ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SentenceCreateSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        for doc in serializer.validated_data['documents']:
            sentence_splitting.delay(doc.id, self.request.session.session_key)


class PersonalDataAPI(ModelViewSet):
    queryset = PersonalData.objects.all()
    serializer_class = PersonalDataSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'uuid'

    def get_queryset(self):
        """
        Restricts the returned data to a current user.
        Optional filters by query params.
        """

        if not self.request.user.is_authenticated:
            return self.queryset.none()

        document = int(self.request.query_params.get('document', 0))
        batch = int(self.request.query_params.get('batch', 0))
        project = int(self.request.query_params.get('project', 0))

        self.queryset = self.queryset.filter(user=self.request.user)

        if document:
            self.queryset = self.queryset.filter(document=document)
        if batch:
            related_files = File.objects.filter(batch=batch)
            related_docs = Document.objects.filter(source_file__in=related_files)
            self.queryset = self.queryset.filter(document__in=related_docs)
        if project:
            related_batches = Batch.objects.filter(project=project)
            related_files = File.objects.filter(batch__in=related_batches)
            related_docs = Document.objects.filter(source_file__in=related_files)
            self.queryset = self.queryset.filter(document__in=related_docs)

        return self.queryset

    @action(detail=False,methods=['GET'])
    def statistics(self, request):
        data = self.filter_queryset(self.get_queryset())
        result = {}
        for entry in data:
            if not result.get(entry.type):
                result[entry.type] = 1
            else:
                result[entry.type] += 1
        result['ALL'] = len(data)

        return JsonResponse(result)

    @action(detail=False, methods=['GET'])
    def export_csv(self, request):

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="personal_data.csv"'

        writer = csv.writer(response)

        data = self.get_queryset()

        writer.writerow(['User', 'Batch', 'Document', 'Type', 'Text', 'Location'])
        for entry in data:
            writer.writerow([
                entry.user,
                entry.batch,
                entry.document,
                entry.type,
                entry.text.encode('utf-8'),
                entry.location
            ])

        return response


class CustomPersonalDataAPI(ModelViewSet):
    queryset = CustomPersonalData.objects.all()
    serializer_class = CustomPersonalDataSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'uuid'

    def get_queryset(self):
        """
        Restricts the returned data to a current user
        """

        if not self.request.user.is_authenticated:
            return self.queryset.none()

        self.queryset = self.queryset.filter(user=self.request.user)

        return self.queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
