# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Coupon'
        db.create_table(u'marketing_coupon', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('expire', self.gf('django.db.models.fields.DateTimeField')()),
            ('subscription', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('notes', self.gf('django.db.models.fields.TextField')()),
            ('free', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('special_price', self.gf('django.db.models.fields.FloatField')(default=None, null=True)),
            ('discount_percent', self.gf('django.db.models.fields.FloatField')(default=None, null=True)),
            ('discount_units', self.gf('django.db.models.fields.FloatField')(default=None, null=True)),
        ))
        db.send_create_signal(u'marketing', ['Coupon'])


    def backwards(self, orm):
        # Deleting model 'Coupon'
        db.delete_table(u'marketing_coupon')


    models = {
        u'marketing.coupon': {
            'Meta': {'object_name': 'Coupon'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'discount_percent': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'}),
            'discount_units': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'}),
            'expire': ('django.db.models.fields.DateTimeField', [], {}),
            'free': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'special_price': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True'}),
            'subscription': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['marketing']