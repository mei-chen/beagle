from __future__ import unicode_literals

from django.forms import ModelForm

from portal.models import Project, Batch, File


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'status']


class BatchForm(ModelForm):
    class Meta:
        model = Batch
        fields = ['name', 'description']


class FileForm(ModelForm):
    class Meta:
        model = File
        fields = ['content']
