# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-26 16:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0009_auto_20170525_1837'),
    ]

    operations = [
        migrations.RenameField(
            model_name='builtinclassifier',
            old_name='data',
            new_name='model',
        ),
    ]
