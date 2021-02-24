from django_filters.rest_framework import (
    FilterSet, ModelChoiceFilter, BooleanFilter
)
from document.models import Document
from portal.models import Batch


class DocumentFilter(FilterSet):
    isorigin = BooleanFilter(name="origin", lookup_expr='isnull')
    source_file__batch = ModelChoiceFilter(
        queryset=Batch.objects.all(), to_field_name="id")

    class Meta:
        model = Document
        fields = ['source_file__batch', 'isorigin']
