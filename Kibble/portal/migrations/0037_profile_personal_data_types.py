# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-03-12 12:53
from __future__ import unicode_literals

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0036_profile_obfuscated_export_ext'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='personal_data_types',
            field=jsonfield.fields.JSONField(default={b'Canadian Social Insurance Number': True, b'Date': True, b'Email': True, b'Link': True, b'Organization': True, b'Person': True, b'Phone': True, b'Price': True, b'Street Address': True, b'UK National Insurance Number': True, b'US Social Security Number': True}),
        ),
    ]