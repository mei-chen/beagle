import tempfile
import urllib

from django.template.defaultfilters import slugify
from django.shortcuts import render
from django.http import Http404, HttpResponse
from wsgiref.util import FileWrapper
from django.contrib.admin.views.decorators import staff_member_required

from . import Report
from .shortcuts import init_report
from .tasks import build_report
from .models import GeneratedReport


@staff_member_required
def report_list(request, *args, **kwargs):
    reports = Report.all()
    return render(request, 'report_list.html', {'reports': reports})


@staff_member_required
def report_details(request, module_name, class_name, *args, **kwargs):
    report = init_report(module_name, class_name)

    if not report:
        raise Http404()

    if request.method == 'POST':
        report.bind(request)
        if report.is_valid():
            # Start background job and redirect to confirmation page
            build_report.delay(request.user.pk, module_name, class_name, params=report.params)
            return render(request, 'report_success.html')
        else:
            return render(request, 'report_details.html', {'form': report.form})

    return render(request, 'report_details.html', {'form': report.form})


@staff_member_required
def report_download(request, report_id, *args, **kwargs):
    try:
        generated_report = GeneratedReport.objects.get(pk=int(report_id))
    except (GeneratedReport.DoesNotExist, ValueError):
        raise Http404()

    with tempfile.TemporaryFile() as response_file:
        response_file.write(generated_report.data.encode('utf-8'))
        content_length = response_file.tell()
        wrapper = FileWrapper(response_file)
        response = HttpResponse(wrapper, content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % urllib.parse.quote(slugify(generated_report.title))
        response['Content-Length'] = content_length

    return response
