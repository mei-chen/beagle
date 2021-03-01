from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.permissions import IsAuthenticated

from analysis.api.serializers import (
    RegExSerializer, RegExApplySerializer, ReportSerializer,
    SimModelListSerializer, RecommendationSerializer,
    KeywordSerializer, KeywordListSerializer, KeywordListSearchySerializer
)
from analysis.models import RegEx, Report, Keyword, KeywordList, SimModel

from analysis.api.filters import ReportFilter, KeywordFilter

from analysis.tasks import (
    regex_apply, most_similar_recommend, keywordlist_search
)


class RegExAPI(ModelViewSet):
    queryset = RegEx.objects.all()
    serializer_class = RegExSerializer
    permission_classes = (IsAuthenticated,)


class RegExApplyAPI(CreateModelMixin, ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = RegExApplySerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        regex = serializer.validated_data['regex']
        batch = serializer.validated_data['batch']
        regex_apply.delay(regex.id, batch.id, self.request.session.session_key)


class ReportAPI(ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = (IsAuthenticated,)
    filter_class = ReportFilter


class SimModelListAPI(ModelViewSet):
    queryset = SimModel.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = SimModelListSerializer


class RecommendationAPI(CreateModelMixin, ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = RecommendationSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        word = serializer.validated_data['word']
        model = serializer.validated_data['model']
        most_similar_recommend.delay(
            word, model, self.request.session.session_key)


class KeywordAPI(ModelViewSet):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    permission_classes = (IsAuthenticated,)
    filter_class = KeywordFilter


class KeywordListAPI(ModelViewSet):
    queryset = KeywordList.objects.all()
    serializer_class = KeywordListSerializer
    permission_classes = (IsAuthenticated,)


class KeywordListSearchAPI(CreateModelMixin, ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = KeywordListSearchySerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        keywordlist = serializer.validated_data['keywordlist']
        batch = serializer.validated_data['batch']
        obfuscate = serializer.validated_data['obfuscate']
        keywordlist_search.delay(
            keywordlist.id, batch.id, obfuscate,
            self.request.session.session_key
        )
