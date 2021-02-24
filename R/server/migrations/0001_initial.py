# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 20:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Detail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
                ('env', models.CharField(choices=[('dev', 'dev'), ('beta', 'beta'), ('deploy', 'deploy'), ('STAGING', 'STAGING'), ('PRODUCTION', 'PRODUCTION')], max_length=300)),
                ('endpoint', models.CharField(max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
