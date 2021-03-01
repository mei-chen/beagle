# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-23 11:06
from __future__ import unicode_literals

from django.db import migrations, models
import experiment.models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0014_auto_20170623_0953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='name',
            field=models.CharField(db_index=True, default=None, max_length=300, unique=True, verbose_name='Name'),
        ),
    ]
