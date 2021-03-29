from django import forms
from django.test import RequestFactory, TestCase
from django_reports import Report


class ReportTestCase(TestCase):

    def test_params(self):
        class CustomForm(forms.Form):
            name = forms.CharField()

        class CustomReport(Report):
            form_class = CustomForm

        request_factory = RequestFactory()
        request = request_factory.post('/path', data={'name': 'MyName'})

        report = CustomReport()
        report.bind(request)
        self.assertEqual(dict(report.params), {'name': ['MyName']})

    def test_is_valid(self):
        class CustomForm(forms.Form):
            name = forms.CharField(max_length=10)

        class CustomReport(Report):
            form_class = CustomForm

        request_factory = RequestFactory()
        request = request_factory.post('/path', data={'name': 'MyNameMyNameMyNameMyNameMyNameMyName'})

        report = CustomReport()
        report.bind(request)
        self.assertFalse(report.is_valid, False)

    def test_generate(self):
        class CustomForm(forms.Form):
            name = forms.CharField(max_length=10)

        class CustomReport(Report):
            form_class = CustomForm

            def generate(self, **kwargs):
                name = self.params['name']
                for char in name:
                    yield char

        request_factory = RequestFactory()
        request = request_factory.post('/path', data={'name': 'ThisIsName'})

        report = CustomReport()
        report.bind(request)

        generated = list(report.generate())
        self.assertEqual(generated, list('ThisIsName'))
