# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-02-28 21:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0033_batch_personal_data_gathered'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='sentence_word_threshold',
            field=models.SmallIntegerField(default=8),
        ),
    ]