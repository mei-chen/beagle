from django_filters.rest_framework import (
    FilterSet, ModelChoiceFilter, NumberFilter
)

from analysis.models import Report, Keyword, KeywordList
from portal.models import Batch


class ReportFilter(FilterSet):
    batch = ModelChoiceFilter(queryset=Batch.objects.all(), to_field_name="id")
    report_type = NumberFilter(field_name="report_type", required=True)

    class Meta:
        model = Report
        fields = ['batch', 'report_type']


class KeywordFilter(FilterSet):
    keyword_list = ModelChoiceFilter(
        queryset=KeywordList.objects.all(), to_field_name="id")

    class Meta:
        model = Keyword
        fields = ['keyword_list']
