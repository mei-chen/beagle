# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-08 13:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0006_auto_20170508_1353'),
        ('dataset', '0002_auto_20170505_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='classifiers',
            field=models.ManyToManyField(to='experiment.TrainedClassifier'),
        ),
    ]