# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-01-10 15:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0026_trainedclassifier_decision_threshold'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trainedclassifier',
            name='decision_threshold',
            field=models.FloatField(blank=True, null=True, verbose_name='Decision Threshold'),
        ),
    ]
