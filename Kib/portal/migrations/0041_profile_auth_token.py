# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-03-30 11:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0040_profile_min_similarity_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='auth_token',
            field=models.CharField(max_length=40, null=True),
        ),
    ]