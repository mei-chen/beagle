# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-26 19:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ml', '0002_auto_20170718_1525'),
    ]

    operations = [
        migrations.RenameField(
            model_name='OnlineLearner',
            old_name='model_uuid',
            new_name='uuid',
        ),
        migrations.RenameField(
            model_name='PretrainedLearner',
            old_name='model_uuid',
            new_name='uuid',
        ),
        migrations.RenameField(
            model_name='LearnerAttribute',
            old_name='model_uuid',
            new_name='uuid',
        ),
    ]