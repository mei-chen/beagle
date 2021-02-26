# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ClausesStatistic'
        db.create_table(u'clauses_statistics_clausesstatistic', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('tag', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('avg_word_count', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
        ))
        db.send_create_signal(u'clauses_statistics', ['ClausesStatistic'])


    def backwards(self, orm):
        # Deleting model 'ClausesStatistic'
        db.delete_table(u'clauses_statistics_clausesstatistic')


    models = {
        u'clauses_statistics.clausesstatistic': {
            'Meta': {'object_name': 'ClausesStatistic'},
            'avg_word_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        }
    }

    complete_apps = ['clauses_statistics']