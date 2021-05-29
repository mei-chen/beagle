# Generated by Django 2.2 on 2021-05-11 19:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('document', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='document',
            options={'ordering': ['id']},
        ),
        migrations.AlterField(
            model_name='document',
            name='source_file',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='portal.File'),
        ),
        migrations.AlterField(
            model_name='documenttag',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='document.Document'),
        ),
        migrations.AlterField(
            model_name='personaldata',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='document.Document'),
        ),
        migrations.AlterField(
            model_name='personaldata',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sentence',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sentences', to='document.Document'),
        ),
    ]