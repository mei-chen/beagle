# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-08-25 15:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import jsonfield.fields
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('ml', '0010_remove_onlinelearner_positive_set_size'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnlineDataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('uuid', models.CharField(max_length=100, unique=True, verbose_name=b'UUID')),
                ('samples', jsonfield.fields.JSONField(blank=True, default=None, null=True, verbose_name=b'Samples')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='onlinelearner',
            name='samples',
        ),
        migrations.AddField(
            model_name='onlinelearner',
            name='dataset',
            field=models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='learner', to='ml.OnlineDataset'),
        ),
    ]