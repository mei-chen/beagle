# Generated by Django 2.2 on 2021-03-24 21:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import jsonfield.fields
import portal.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PDFUploadMonitor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('docs', models.IntegerField(default=0)),
                ('pages', models.IntegerField(default=0)),
                ('docs_ocred', models.IntegerField(default=0)),
                ('pages_ocred', models.IntegerField(default=0)),
                ('startdate', models.DateField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'PDF Upload monitoring',
                'verbose_name_plural': 'PDF Upload monitoring',
                'get_latest_by': 'startdate',
            },
        ),
        migrations.CreateModel(
            name='WrongAnalysisFlag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comments', models.TextField(blank=True, default='', null=True)),
                ('resolved', models.BooleanField(default=False, verbose_name='Resolved?')),
                ('resolution_comments', models.TextField(blank=True, default='', null=True)),
                ('doc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Document')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Wrong Analysis Flag',
                'verbose_name_plural': 'Wrong Analysis Flags',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_title', models.TextField(blank=True, default='', null=True)),
                ('company', models.TextField(blank=True, default='', null=True)),
                ('phone', models.TextField(blank=True, default='', max_length=25, null=True)),
                ('document_upload_count', models.IntegerField(null=True)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='profile_photo/%Y/%m/%d/')),
                ('avatar_s3', models.CharField(blank=True, help_text='Format: bucket:filename', max_length=255, null=True, verbose_name='S3 Avatar address')),
                ('tags_cache', jsonfield.fields.JSONField(blank=True, default=None, null=True, verbose_name='Tags Cache')),
                ('keywords_cache', jsonfield.fields.JSONField(blank=True, default=None, null=True, verbose_name='Keywords Cache')),
                ('initial_tour', models.DateTimeField(default=None, null=True, verbose_name='Initial Tour')),
                ('settings', jsonfield.fields.JSONField(blank=True, default=None, null=True, verbose_name='User Settings')),
                ('rlte_flags', jsonfield.fields.JSONField(default=portal.models.generate_default_rlte_flags, verbose_name='User RLTE Flags')),
                ('spot', jsonfield.fields.JSONField(blank=True, default=None, null=True, verbose_name='Spot')),
                ('kibble', jsonfield.fields.JSONField(blank=True, default=None, null=True, verbose_name='Kibble')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='details', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Details',
                'verbose_name_plural': 'Users Details',
            },
        ),
    ]
