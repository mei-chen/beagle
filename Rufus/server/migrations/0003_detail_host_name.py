# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 21:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0002_auto_20170207_2039'),
    ]

    operations = [
        migrations.AddField(
            model_name='detail',
            name='host_name',
            field=models.CharField(default='', max_length=300),
            preserve_default=False,
        ),
    ]
