# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-26 16:39
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0022_auto_20170718_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='uuid',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='formula',
            name='uuid',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, verbose_name='UUID'),
        ),
    ]
