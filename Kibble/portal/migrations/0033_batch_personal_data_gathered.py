# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-02-28 12:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0032_profile_auto_gather_personal_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='personal_data_gathered',
            field=models.BooleanField(default=False),
        ),
    ]