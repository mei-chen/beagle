# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-02-08 10:56
from __future__ import unicode_literals

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0011_personaldata'),
    ]

    operations = [
        migrations.AddField(
            model_name='sentence',
            name='vectorization',
            field=jsonfield.fields.JSONField(blank=True, null=True),
        ),
    ]