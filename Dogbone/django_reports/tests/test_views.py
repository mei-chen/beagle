from django.core.urlresolvers import reverse
from django_reports import Report
from django_reports.tasks import build_report
from django_reports.models import GeneratedReport

from dogbone.testing.base import BeagleWebTest


class SomeReport1(Report):
    pass


class SomeReport2(Report):
    pass


class ViewsTestCase(BeagleWebTest):
    NEED_DEFAULT_USER = False

    def setUp(self):
        super(ViewsTestCase, self).setUp()
        self.user = self.create_user()
        self.login()

    def make_user_stuff(self):
        self.user.is_staff = True
        self.user.save()

    def test_list_accessible_to_staff_only(self):
        self.make_user_stuff()

        list_url = reverse('django_reports.list')

        response = self.client.get(list_url)
        self.assertTemplateUsed(response, 'report_list.html')
        self.assertTemplateNotUsed(response, 'admin/login.html')
        self.assertEqual(response.status_code, 200)

    def test_list_forbidden(self):
        list_url = reverse('django_reports.list')

        response = self.client.get(list_url)
        self.assertTemplateNotUsed(response, 'report_list.html')
        self.assertTemplateUsed(response, 'admin/login.html')
        self.assertEqual(response.status_code, 200)

    def test_details_accessible_to_staff_only(self):
        self.make_user_stuff()

        details_url = reverse('django_reports.details', kwargs={'module_name': 'django_reports.tests.test_views',
                                                                'class_name': 'SomeReport2'})

        response = self.client.get(details_url)
        self.assertTemplateUsed(response, 'report_details.html')
        self.assertTemplateNotUsed(response, 'admin/login.html')
        self.assertEqual(response.status_code, 200)

    def test_details_forbidden(self):
        details_url = reverse('django_reports.details', kwargs={'module_name': 'django_reports.tests.test_views',
                                                                'class_name': 'SomeReport1'})

        response = self.client.get(details_url)
        self.assertTemplateNotUsed(response, 'report_details.html')
        self.assertTemplateUsed(response, 'admin/login.html')
        self.assertEqual(response.status_code, 200)

    def test_download(self):
        self.make_user_stuff()

        build_report(self.user.pk + 1, 'django_reports.tests.test_views', 'SomeReport1', params={})
        available_generated_reports = GeneratedReport.objects.all()
        self.assertEqual(len(available_generated_reports), 1)

        generated = available_generated_reports[0]

        download_url = reverse('django_reports.download', kwargs={'report_id': generated.pk})
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)

    def test_download_not_found(self):
        self.make_user_stuff()

        build_report(self.user.pk + 1, 'django_reports.tests.test_views', 'SomeReport1', params={})
        available_generated_reports = GeneratedReport.objects.all()
        self.assertEqual(len(available_generated_reports), 1)

        generated = available_generated_reports[0]

        download_url = reverse('django_reports.download', kwargs={'report_id': generated.pk + 1})
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 404)
