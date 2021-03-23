# Generated by Django 2.2 on 2021-03-17 21:03

import core.models
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import re


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('experiment', '0001_initial'),
        ('dataset', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExperimentExternalInvite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('email', models.EmailField(max_length=254)),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='external_invites', to='experiment.Experiment')),
                ('inviter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiment_external_invites_sent', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExperimentCollaborationInvite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collaboration_invites', to='experiment.Experiment')),
                ('invitee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiment_collaboration_invites_received', to=settings.AUTH_USER_MODEL)),
                ('inviter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='experiment_collaboration_invites_sent', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DatasetExternalInvite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('email', models.EmailField(max_length=254)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='external_invites', to='dataset.Dataset')),
                ('inviter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dataset_external_invites_sent', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DatasetCollaborationInvite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collaboration_invites', to='dataset.Dataset')),
                ('invitee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dataset_collaboration_invites_received', to=settings.AUTH_USER_MODEL)),
                ('inviter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dataset_collaboration_invites_sent', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(default=core.models.generate_random_token, max_length=100, unique=True, validators=[django.core.validators.RegexValidator(message='A token value must be an alphanumeric string of a size between 50 and 100 characters long.', regex=re.compile('^[a-zA-Z0-9]{50,100}$'))], verbose_name='Value')),
                ('owner', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='access_token', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
