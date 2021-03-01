from django_reports import Report
from django import forms
from django.conf import settings
from core.models import Document
from dateutil import parser
import pytz


class DocumentsUploadedViaRufusForm(forms.Form):
    from_datetime = forms.DateTimeField(widget=forms.TextInput(attrs={'class': 'datepicker-input'}))
    to_datetime = forms.DateTimeField(widget=forms.TextInput(attrs={'class': 'datepicker-input'}))


class DocumentsUploadedViaRufus(Report):

    # Starting from 0
    sort_by_column = None

    form_class = DocumentsUploadedViaRufusForm
    description = 'The documents uploaded via Rufus (Date format: MM/DD/YYYY)'

    def generate(self, **kwargs):
        from_datetime = parser.parse(kwargs['from_datetime'][0])
        to_datetime = parser.parse(kwargs['to_datetime'][0])

        from_datetime.replace(tzinfo=pytz.timezone(settings.TIME_ZONE))
        to_datetime.replace(tzinfo=pytz.timezone(settings.TIME_ZONE))

        documents = Document.lightweight.filter(created__gte=from_datetime, created__lte=to_datetime,
                                                upload_source='email')

        yield ('ID', 'TITLE', 'UPLOADER_EMAIL', 'UPLOADED_ON')

        for document in documents:
            yield (document.pk, document.title, document.owner.email, document.created)
