# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-02-21 06:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0030_auto_20180219_0809'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='highlight_color',
            field=models.CharField(default=b'red', max_length=16),
        ),
        migrations.AlterField(
            model_name='profile',
            name='obfuscate_type',
            field=models.CharField(default=b'string', max_length=16),
        ),
    ]
