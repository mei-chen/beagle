from django_filters.rest_framework import FilterSet, BooleanFilter, NumberFilter

from portal.models import Batch, File, Project


class BatchFilter(FilterSet):
    unassigned = NumberFilter(
        name="project", exclude=True, required=False
    )

    class Meta:
        model = Batch
        fields = ['project', 'unassigned']


class FileFilter(FilterSet):
    unassigned = BooleanFilter(name="batch", lookup_expr='isnull')
    nodocuments = BooleanFilter(name="documents", lookup_expr='isnull')

    class Meta:
        model = File
        fields = ['batch', 'unassigned']


class ProjectFilter(FilterSet):
    exclude_status = NumberFilter(name='status', exclude=True, required=False)

    class Meta:
        model = Project
        fields = ['status']
