# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-10 12:16
from __future__ import unicode_literals

from django.db import migrations, models


def set_names_of_legacy_labeling_tasks(apps, schema_editor):
    """
    Replaces empty value for the name field with the corresponding dataset's
    name (the default behavior) for each legacy labeling task.
    """

    try:
        LabelingTask = apps.get_model('dataset', 'LabelingTask')
        for labeling_task in LabelingTask.objects.all():
            labeling_task.name = labeling_task.dataset.name
            labeling_task.save()
    except LookupError:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('dataset', '0020_labelingtask_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='labelingtask',
            name='name',
            field=models.CharField(default='', max_length=300, verbose_name='Name'),
            preserve_default=False,
        ),

        migrations.RunPython(
            set_names_of_legacy_labeling_tasks,
            migrations.RunPython.noop,  # no reverse code needed
        )
    ]
