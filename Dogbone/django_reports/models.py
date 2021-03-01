import jsonfield

from django.db import models
from django.contrib.auth.models import User

from model_utils.models import TimeStampedModel


class GeneratedReport(TimeStampedModel):
    """
    Generated report model
    it holds the result of the generated report inside the `data` field
    """
    author = models.ForeignKey(User, null=True)
    title = models.CharField('Title', max_length=300)
    params = jsonfield.JSONField(null=True)
    data = models.TextField('Data')

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Generated Reports'
        get_latest_by = 'created'
        ordering = ['-created']
