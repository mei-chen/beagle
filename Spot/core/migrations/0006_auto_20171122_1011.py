# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-22 10:11
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0005_accesstoken'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accesstoken',
            name='name',
        ),
        migrations.AddField(
            model_name='accesstoken',
            name='owner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='access_token', to=settings.AUTH_USER_MODEL),
        ),
    ]
