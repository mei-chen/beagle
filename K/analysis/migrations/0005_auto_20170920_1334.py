# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-09-20 13:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0004_auto_20170920_1123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='keyword',
            name='keyword_list',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='keywords', to='analysis.KeywordList'),
        ),
    ]
