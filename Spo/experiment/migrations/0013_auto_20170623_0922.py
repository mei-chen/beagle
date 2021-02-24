# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-23 09:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0012_remove_experiment_klasses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='name',
            field=models.CharField(db_index=True, max_length=300, unique=True, verbose_name='Name'),
        ),
    ]
