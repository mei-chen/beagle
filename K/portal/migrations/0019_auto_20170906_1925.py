# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-09-06 19:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0018_merge_20170828_1109'),
    ]

    operations = [
        migrations.CreateModel(
            name='OCRStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.SmallIntegerField(null=True)),
                ('document_quality', models.SmallIntegerField(null=True)),
                ('word_quality', models.SmallIntegerField(null=True)),
                ('low_dictionary_characters', models.NullBooleanField()),
                ('document_id', models.CharField(blank=True, max_length=200)),
                ('page_count', models.IntegerField(null=True)),
                ('created_on', models.DateTimeField(null=True)),
                ('processed_on', models.DateTimeField(null=True)),
                ('message', models.CharField(blank=True, max_length=200)),
                ('content', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ocr_status', to='portal.File')),
            ],
        ),
        migrations.AlterModelOptions(
            name='project',
            options={},
        ),
    ]
