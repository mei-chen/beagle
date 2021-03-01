# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PaymentRecord'
        db.create_table(u'marketing_paymentrecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('buyer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('redeemed_coupon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['marketing.Coupon'], null=True)),
            ('purchased_subscription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['marketing.PurchasedSubscription'])),
            ('amount', self.gf('django.db.models.fields.FloatField')()),
            ('currency', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'marketing', ['PaymentRecord'])

        # Adding model 'PurchasedSubscription'
        db.create_table(u'marketing_purchasedsubscription', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('buyer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('subscription', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'marketing', ['PurchasedSubscription'])

        # Deleting field 'Coupon.expire'
        db.delete_column(u'marketing_coupon', 'expire')

        # Adding field 'Coupon.start'
        db.add_column(u'marketing_coupon', 'start',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Coupon.end'
        db.add_column(u'marketing_coupon', 'end',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)


        # Changing field 'Coupon.notes'
        db.alter_column(u'marketing_coupon', 'notes', self.gf('django.db.models.fields.TextField')(null=True))

    def backwards(self, orm):
        # Deleting model 'PaymentRecord'
        db.delete_table(u'marketing_paymentrecord')

        # Deleting model 'PurchasedSubscription'
        db.delete_table(u'marketing_purchasedsubscription')

        # Adding field 'Coupon.expire'
        db.add_column(u'marketing_coupon', 'expire',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2015, 7, 30, 0, 0)),
                      keep_default=False)

        # Deleting field 'Coupon.start'
        db.delete_column(u'marketing_coupon', 'start')

        # Deleting field 'Coupon.end'
        db.delete_column(u'marketing_coupon', 'end')


        # Changing field 'Coupon.notes'
        db.alter_column(u'marketing_coupon', 'notes', self.gf('django.db.models.fields.TextField')(default=''))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'marketing.coupon': {
            'Meta': {'object_name': 'Coupon'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'discount_percent': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'discount_units': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'free': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'special_price': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'subscription': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'marketing.paymentrecord': {
            'Meta': {'object_name': 'PaymentRecord'},
            'amount': ('django.db.models.fields.FloatField', [], {}),
            'buyer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'currency': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'purchased_subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['marketing.PurchasedSubscription']"}),
            'redeemed_coupon': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['marketing.Coupon']", 'null': 'True'})
        },
        u'marketing.purchasedsubscription': {
            'Meta': {'object_name': 'PurchasedSubscription'},
            'buyer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'subscription': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['marketing']