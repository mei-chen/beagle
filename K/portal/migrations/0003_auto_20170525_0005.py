# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-25 00:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0002_auto_20170522_1238'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='batch',
            name='upload_time',
        ),
        migrations.AlterField(
            model_name='batch',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='batches', to='portal.Project'),
        ),
    ]
