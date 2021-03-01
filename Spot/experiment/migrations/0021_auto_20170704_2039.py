# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-04 20:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0020_trainedclassifier_scores'),
    ]

    operations = [
        migrations.AddField(
            model_name='builtinclassifier',
            name='name',
            field=models.CharField(blank=True, max_length=30, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='regexclassifier',
            name='name',
            field=models.CharField(blank=True, max_length=30, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='trainedclassifier',
            name='name',
            field=models.CharField(blank=True, max_length=30, verbose_name='Name'),
        ),
    ]
