from io import StringIO
import csv

from celery import shared_task
from django.utils.timezone import now
from django.contrib.auth.models import User

from .shortcuts import init_report
from .models import GeneratedReport
from .exceptions import ReportNotFound


@shared_task
def build_report(user_id, module_name, class_name, params):
    user = None
    try:
        user = User.objects.get(pk=user_id)
        report = init_report(module_name, class_name)

        if report is None:
            raise ReportNotFound("No %s report found in %s" % (class_name, module_name))

        output = StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        if report.sort_by_column is not None:
            result = [line for line in report.generate(**params)]
            result.sort(key=lambda x: x[report.sort_by_column], reverse=True)
        else:
            result = report.generate(**params)

        for line in result:
            writer.writerow(line)

        generated_report = GeneratedReport(author=user,
                                           title="%s.%s - %s" % (module_name, class_name, str(now())),
                                           params=params,
                                           data=output.getvalue())
        generated_report.save()
    except User.DoesNotExist:
        GeneratedReport(author=None,
                        title="[ERROR] %s.%s - %s" % (module_name, class_name, str(now())),
                        params=params,
                        data="The user does not exist").save()
    except (ReportNotFound, Exception) as e:
        GeneratedReport(author=user,
                        title="[ERROR] %s.%s - %s" % (module_name, class_name, str(now())),
                        params=params,
                        data=str(e)).save()
