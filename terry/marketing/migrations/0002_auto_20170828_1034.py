# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-08-28 10:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasedsubscription',
            name='subscription',
            field=models.CharField(choices=[(b'MONTHLY_ENTERPRISE_SUBSCRIPTION', b"<class 'marketing.subscriptions.MonthlyEnterpriseSubscription'>"), (b'MONTHLY_PAID_SUBSCRIPTION', b"<class 'marketing.subscriptions.MonthlyPaidSubscription'>"), (b'YEARLY_ENTERPRISE_SUBSCRIPTION', b"<class 'marketing.subscriptions.YearlyEnterpriseSubscription'>"), (b'YEARLY_PAID_SUBSCRIPTION', b"<class 'marketing.subscriptions.YearlyPaidSubscription'>")], help_text='The subscription package', max_length=200, verbose_name='Subscription'),
        ),
    ]
