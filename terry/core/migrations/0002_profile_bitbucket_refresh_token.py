# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-26 14:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='bitbucket_refresh_token',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
