# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-25 18:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0008_trainedclassifier_dirty'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trainedclassifier',
            name='datasets',
            field=models.ManyToManyField(related_name='trained_classifiers', to='dataset.Dataset'),
        ),
    ]