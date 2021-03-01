# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-31 15:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0023_auto_20170726_1639'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=300, verbose_name='Name')),
                ('child', models.ForeignKey(help_text='Attribute classifier', on_delete=django.db.models.deletion.CASCADE, related_name='attribute_parent', to='experiment.Experiment')),
                ('parent', models.ForeignKey(help_text='Main classifier', on_delete=django.db.models.deletion.CASCADE, related_name='child_attribute', to='experiment.Experiment')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
