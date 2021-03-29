from django.contrib.auth.models import User
from django.db import models
import jsonfield
from model_utils.models import TimeStampedModel

EVENT_TYPES = {
    'open_widget_view': 'Open Widget View',
    'open_context_view': 'Open Context View',
    'open_detail_view': 'Open Detail View',
    'open_clause_view': 'Open Clause View',
    'document_uploaded': 'Document Uploaded',
    'document_processed': 'Document Processed',
    'document_conversion_error': 'Document Conversion Error',
    'document_language_error': 'Document Language Error',
    'document_too_large_to_ocr': 'Document too large to OCR',
}


class Event(TimeStampedModel):

    name = models.CharField(max_length=100, choices=EVENT_TYPES.items())
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data = jsonfield.JSONField(blank=True, default=None, null=True)

    def __str__(self):
        return u'<Event: name="%s", user=%s>' % (self.name, self.user)
