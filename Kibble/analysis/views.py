from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from utils.http import set_download_filename

from analysis.models import Report
from analysis.tasks import zip_reports
from portal.models import Batch


@login_required
def download_report(request):
    report_id = request.GET.get('report')
    batch_id = request.GET.get('batch')
    report_type = request.GET.get('report_type')
    if report_id:
        try:
            report = get_object_or_404(Report, pk=report_id)
        except ValueError:
            raise Http404('Bad report id')
        if request.GET.get('json'):
            ext = 'json'
            response = HttpResponse(
                report.json, content_type='application/json'
            )
        else:
            ext = 'csv'
            response = HttpResponse(
                report.generate_csv().getvalue(), content_type='text/csv'
            )

        set_download_filename(response, '%s.%s' % (report.name, ext))
        return response

    elif batch_id:
        batch = get_object_or_404(Batch, pk=batch_id)
        ziptype = 'json' if request.GET.get('json') else 'csv'
        zip_reports(batch, ziptype, report_type, request.session.session_key)
        return HttpResponse(status=201)
    return HttpResponseBadRequest()
