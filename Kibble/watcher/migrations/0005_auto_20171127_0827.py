# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-27 08:27
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('watcher', '0004_auto_20171126_1909'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cloudfile',
            name='file_object',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='portal.File'),
        ),
        migrations.AlterField(
            model_name='cloudfolder',
            name='batch',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='portal.Batch'),
        ),
    ]