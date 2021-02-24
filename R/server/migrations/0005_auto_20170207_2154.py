# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 21:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0004_auto_20170207_2124'),
    ]

    operations = [
        migrations.RenameField(
            model_name='detail',
            old_name='domain',
            new_name='email_domain',
        ),
        migrations.RenameField(
            model_name='detail',
            old_name='protocol',
            new_name='endpoint_domain',
        ),
        migrations.AddField(
            model_name='detail',
            name='endpoint_protocol',
            field=models.CharField(default='', max_length=300),
            preserve_default=False,
        ),
    ]
