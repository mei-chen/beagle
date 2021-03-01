from django_reports import Report
from django_reports.models import GeneratedReport
from django_reports.tasks import build_report

from dogbone.testing.base import BeagleWebTest


class SomeReport(Report):
    sort_by_column = None

    def generate(self, **kwargs):
        yield (1, 2, 3)
        yield (4, 5, 6)


class TasksTestCase(BeagleWebTest):

    def test_run_build_report_successfully(self):
        build_report(self.user.pk, 'django_reports.tests.test_task', 'SomeReport', params={})
        available_generated_reports = GeneratedReport.objects.all()
        self.assertEqual(len(available_generated_reports), 1)

        generated = available_generated_reports[0]

        self.assertEqual(generated.author, self.user)
        self.assertIsNotNone(generated.title)
        self.assertEqual(generated.params, {})
        self.assertEqual(generated.data, '"1","2","3"\r\n"4","5","6"\r\n')

    def test_non_existing_report(self):
        build_report(self.user.pk, 'django_reports.tests.test_task', 'NONEXISTINGREPORT', params={})
        available_generated_reports = GeneratedReport.objects.all()
        self.assertEqual(len(available_generated_reports), 1)

        generated = available_generated_reports[0]

        self.assertEqual(generated.author, self.user)
        self.assertIsNotNone(generated.title)
        self.assertEqual(generated.params, {})
        self.assertEqual(generated.data, 'No NONEXISTINGREPORT report found in django_reports.tests.test_task')

    def test_non_existing_user(self):
        build_report(self.user.pk + 1, 'django_reports.tests.test_task', 'NONEXISTINGREPORT', params={})
        available_generated_reports = GeneratedReport.objects.all()
        self.assertEqual(len(available_generated_reports), 1)

        generated = available_generated_reports[0]

        self.assertEqual(generated.author, None)
        self.assertIsNotNone(generated.title)
        self.assertEqual(generated.params, {})
        self.assertEqual(generated.data, 'The user does not exist')
