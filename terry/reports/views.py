import operator
import os
import six
import uuid

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from pygooglechart import PieChart2D
from rest_framework import viewsets, mixins
from rest_framework.decorators import list_route
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from reports.models import Report, ReportShared, LicenseStatistic
from reports.serializers import (
    ReportSerializer, ReportListSerializer, ReportSharedSerializer,
    LicenseStatisticSerializer
)
from reports.utils import render_to_pdf
from terry.utils import clean_repo_url

CHART_COLORS = ['3366CC', 'DC3912', 'FF9900', '109618', '990099', '3B3EAC',
                '0099C6', 'DD4477', '66AA00', 'B82E2E', '316395', '994499',
                '22AA99', 'AAAA11', '6633CC', 'E67300', '8B0707', '329262',
                '5574A6', '3B3EAC']


class ReportPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reports to be viewed or deleted.
    """
    queryset = Report.objects.order_by('-created_at')
    pagination_class = ReportPagination
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action in ['list', 'recent']:
            return ReportListSerializer
        else:
            return ReportSerializer

    def get_queryset(self):
        """
        Restricts the returned reports to a current user.
        """
        share_token = self.request.GET.get('share_token')
        if share_token:
            return self.queryset.filter(report_shared__token=share_token)

        elif self.request.user.is_authenticated():
            return self.queryset.filter(user=self.request.user)

        else:
            return self.queryset.none()

    def filter_queryset(self, queryset):
        # Allow filtering by url name (specified in query params)
        filter_by = self.request.query_params.get('filter')
        if filter_by:
            query = six.moves.reduce(
                operator.and_,
                [Q(url__icontains=item) for item in filter_by.split()]
            )
            queryset = queryset.filter(query)
        return queryset

    @list_route(methods=['get'])
    def recent(self, request):
        """
        Returns last 'amount' (query parameter) reports with 'green' status.
        """

        # Return 10 last green reports by default
        try:
            amount = int(request.query_params.get('amount', 10))
        except (TypeError, ValueError):
            amount = 10

        queryset = self.filter_queryset(self.get_queryset())[:amount]
        green_reports = [r for r in queryset
                         if r.content['status'] == 'green']
        serializer = self.get_serializer(green_reports, many=True)

        return Response(serializer.data)


class ReportSharedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reports to be viewed or deleted.
    """
    queryset = ReportShared.objects.order_by('-created_at')
    http_method_names = ['get', 'post', 'delete', 'put']
    serializer_class = ReportSharedSerializer

    def get_queryset(self):
        """
        Restricts the returned reports to a current user.
        """
        if self.request.user.is_authenticated():
            return self.queryset.filter(user=self.request.user)
        return self.queryset.none()

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super(ReportSharedViewSet, self).create(request)

    def update(self, request, *args, **kwargs):
        shared_report = self.get_object()

        # For now we only update name
        shared_report.name = request.data.get('name')
        shared_report.save()

        return Response()


def report_as_pdf(request, report_uuid):
    report = get_object_or_404(Report, uuid=report_uuid)
    cur_time = now().strftime("%Y-%m-%d %H:%M:%S")

    fname = 'Terry_%s - %s.pdf' % (
        report.content['git_url'].strip('/').split('/')[-1],
        cur_time
    )

    # Draw pie chart
    chart = PieChart2D(600, 500)
    chart.set_colours(CHART_COLORS)
    labels = []
    sizes = []

    for i, (lic, count, is_copyleft) in enumerate(report.content['stats']):
        labels.append('%s (%s)' % (lic, count))
        sizes.append(count)

    chart.add_data(sizes)
    chart.set_legend(labels)
    tmp_name = str(uuid.uuid4())

    image_path = os.path.join(settings.MEDIA_ROOT, tmp_name)
    chart.download(image_path)

    report.content['stats_img_path'] = request.build_absolute_uri(
        os.path.join('/', settings.MEDIA_URL, tmp_name))

    repo_icon_path = os.path.join('img', 'git-icons', '%s.png')
    if 'github.com' in report.content['git_url']:
        report.content['repo_icon'] = repo_icon_path % 'github'
    elif 'bitbucket.org' in report.content['git_url']:
        report.content['repo_icon'] = repo_icon_path % 'bitbucket'
    elif 'gitlab.com' in report.content['git_url']:
        report.content['repo_icon'] = repo_icon_path % 'gitlab'
    else:
        report.content['repo_icon'] = None
    print report.content['repo_icon']

    report.content['open_percent'] = 100 - report.content_for_frontend['overall_risk']

    _, repo_data = clean_repo_url(report.content['git_url'])
    report.content['repo_name'] = repo_data['repo_name']

    result = render_to_pdf(os.path.join('pdf', 'report.html'),
                           request.build_absolute_uri(),
                           report.content)
    os.remove(image_path)

    response = HttpResponse(result, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % fname
    return response


class LicenseStatisticViewSet(mixins.RetrieveModelMixin,
                              mixins.ListModelMixin,
                              GenericViewSet):
    """
    API endpoint that allows Licenses to be viewed.
    """
    queryset = LicenseStatistic.objects.all()
    serializer_class = LicenseStatisticSerializer
    lookup_field = 'name'
    lookup_value_regex = '.+'

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(name__in=request.data['licenses'])
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)
